"""
Evaluation runner: orchestrates email generation and scoring across all scenarios and strategies.
"""

import asyncio
import json
import logging
from pathlib import Path

from app.api.schemas import MetricScore, ScenarioResult
from app.core.chains import STRATEGY_MAP
from app.evaluation.metrics.fact_recall import compute_fact_recall
from app.evaluation.metrics.professional_quality import compute_professional_quality
from app.evaluation.metrics.tone_alignment import compute_tone_alignment

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

REQUIRED_SCENARIO_KEYS = {"id", "intent", "key_facts", "tone"}


class ScenarioValidationError(ValueError):
    """Raised when a scenario dict is missing required keys or has bad data."""


def _validate_scenario(scenario: dict, index: int) -> None:
    missing = REQUIRED_SCENARIO_KEYS - set(scenario.keys())
    if missing:
        raise ScenarioValidationError(
            f"Scenario at index {index} missing required keys: {missing}"
        )
    if not isinstance(scenario["key_facts"], list) or not scenario["key_facts"]:
        raise ScenarioValidationError(
            f"Scenario {scenario.get('id', index)}: key_facts must be a non-empty list"
        )
    if not scenario["intent"].strip():
        raise ScenarioValidationError(
            f"Scenario {scenario.get('id', index)}: intent must not be empty"
        )


def load_scenarios() -> list[dict]:
    path = DATA_DIR / "scenarios.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenarios file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError(f"scenarios.json must be a non-empty JSON array, got {type(data).__name__}")

    for i, scenario in enumerate(data):
        _validate_scenario(scenario, i)

    return data


async def evaluate_single_scenario(
    scenario: dict,
    strategy: str,
) -> ScenarioResult:
    """Generate an email for one scenario with one strategy, then score it."""
    if strategy not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy '{strategy}'. Available: {list(STRATEGY_MAP.keys())}")

    generator = STRATEGY_MAP[strategy]
    sid = scenario.get("id", "?")

    logger.info("Evaluating scenario %s with strategy '%s'", sid, strategy)

    result = await generator(
        intent=scenario["intent"],
        key_facts=scenario["key_facts"],
        tone=scenario["tone"],
    )

    if not result.email or not result.email.strip():
        logger.warning("Scenario %s [%s]: generation produced empty email", sid, strategy)

    fact_result = await compute_fact_recall(
        key_facts=scenario["key_facts"],
        generated_email=result.email,
    )

    tone_result = await compute_tone_alignment(
        tone=scenario["tone"],
        generated_email=result.email,
    )

    quality_result = await compute_professional_quality(
        generated_email=result.email,
        reference_email=scenario.get("reference_email", ""),
    )

    scores = [
        MetricScore(
            metric_name="Fact Recall",
            score=fact_result["score"],
            details=fact_result["details"],
        ),
        MetricScore(
            metric_name="Tone Alignment",
            score=tone_result["score"],
            details=tone_result["details"],
        ),
        MetricScore(
            metric_name="Professional Quality",
            score=quality_result["score"],
            details=quality_result["details"],
        ),
    ]

    return ScenarioResult(
        scenario_id=scenario["id"],
        intent=scenario["intent"],
        tone=scenario["tone"],
        strategy=strategy,
        model_name=result.model_name,
        generated_email=result.email,
        scores=scores,
    )


def _compute_summary(results: list[ScenarioResult]) -> dict:
    """Compute average scores per strategy."""
    from collections import defaultdict

    if not results:
        return {}

    strategy_scores = defaultdict(lambda: defaultdict(list))

    for r in results:
        for s in r.scores:
            strategy_scores[r.strategy][s.metric_name].append(s.score)

    summary = {}
    for strategy, metrics in strategy_scores.items():
        summary[strategy] = {}
        total_scores = []
        for metric_name, scores in metrics.items():
            avg = round(sum(scores) / len(scores), 1) if scores else 0.0
            summary[strategy][metric_name] = avg
            total_scores.extend(scores)
        summary[strategy]["overall_average"] = (
            round(sum(total_scores) / len(total_scores), 1) if total_scores else 0.0
        )

    return summary


async def run_evaluation(
    strategies: list[str] | None = None,
) -> tuple[list[ScenarioResult], dict]:
    """Run the full evaluation pipeline."""
    if strategies is None:
        strategies = ["advanced", "baseline"]

    scenarios = load_scenarios()
    all_results: list[ScenarioResult] = []
    errors: list[dict] = []

    for strategy in strategies:
        if strategy not in STRATEGY_MAP:
            logger.warning("Unknown strategy '%s', skipping", strategy)
            continue
        for i, scenario in enumerate(scenarios):
            try:
                result = await evaluate_single_scenario(scenario, strategy)
                all_results.append(result)
                logger.info(
                    "Scenario %d [%s]: Fact=%.1f Tone=%.1f Quality=%.1f",
                    result.scenario_id,
                    strategy,
                    result.scores[0].score,
                    result.scores[1].score,
                    result.scores[2].score,
                )
            except Exception as e:
                sid = scenario.get("id", i)
                logger.error("Scenario %s [%s] FAILED: %s", sid, strategy, e)
                errors.append({"scenario_id": sid, "strategy": strategy, "error": str(e)})

            if i < len(scenarios) - 1:
                await asyncio.sleep(2)

    if errors:
        logger.warning("%d scenario(s) failed during evaluation", len(errors))

    if not all_results:
        raise RuntimeError(
            f"All scenarios failed. Errors: {errors}. "
            "Check your API key and network connection."
        )

    summary = _compute_summary(all_results)
    return all_results, summary
