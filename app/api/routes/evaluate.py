import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import EvaluationRequest, EvaluationResponse
from app.core.chains import STRATEGY_MAP
from app.evaluation.runner import (
    evaluate_single_scenario,
    load_scenarios,
    run_evaluation,
    _compute_summary,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/scenarios")
async def get_scenarios():
    """Return all test scenarios from data/scenarios.json."""
    try:
        return load_scenarios()
    except Exception as e:
        logger.exception("Failed to load scenarios")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    """Run the full evaluation suite across specified strategies."""
    logger.info("Starting evaluation for strategies: %s", request.strategies)

    try:
        results, summary = await run_evaluation(request.strategies)
    except Exception as e:
        logger.exception("Evaluation failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return EvaluationResponse(results=results, summary=summary)


@router.post("/evaluate/stream")
async def evaluate_stream(request: EvaluationRequest):
    """Stream evaluation results as Server-Sent Events."""

    async def generate():
        scenarios = load_scenarios()
        strategies = [s for s in request.strategies if s in STRATEGY_MAP]
        total = len(scenarios) * len(strategies)
        completed = 0
        all_results = []

        yield f"data: {json.dumps({'type': 'init', 'total': total, 'scenarios': len(scenarios), 'strategies': strategies})}\n\n"

        for strategy in strategies:
            for scenario in scenarios:
                sid = scenario.get("id", "?")
                try:
                    result = await evaluate_single_scenario(scenario, strategy)
                    all_results.append(result)
                    completed += 1
                    yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'completed': completed, 'total': total})}\n\n"
                except Exception as e:
                    completed += 1
                    logger.error("Scenario %s [%s] failed: %s", sid, strategy, e)
                    yield f"data: {json.dumps({'type': 'error', 'scenario_id': sid, 'strategy': strategy, 'error': str(e), 'completed': completed, 'total': total})}\n\n"

        summary = _compute_summary(all_results)
        yield f"data: {json.dumps({'type': 'complete', 'summary': summary, 'total_results': len(all_results)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
