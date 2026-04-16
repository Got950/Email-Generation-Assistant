"""
CLI entry point: runs the full evaluation pipeline and generates reports.

Usage:
    python run_evaluation.py
    python run_evaluation.py --strategies advanced baseline
"""

import asyncio
import argparse
import logging
import sys

from app.evaluation.report import save_csv_report, save_json_report, save_markdown_report
from app.evaluation.runner import run_evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main(strategies: list[str]):
    logger.info("=" * 60)
    logger.info("Email Generation Assistant — Evaluation Pipeline")
    logger.info("Strategies: %s", strategies)
    logger.info("=" * 60)

    results, summary = await run_evaluation(strategies)

    json_path = save_json_report(results, summary)
    csv_path = save_csv_report(results)
    md_path = save_markdown_report(results, summary)

    logger.info("=" * 60)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 60)

    for strategy, metrics in summary.items():
        logger.info("\n--- %s ---", strategy.upper())
        for metric, avg in metrics.items():
            logger.info("  %-25s: %.1f", metric, avg)

    logger.info("\nReports saved:")
    logger.info("  JSON:     %s", json_path)
    logger.info("  CSV:      %s", csv_path)
    logger.info("  Markdown: %s", md_path)

    return results, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run email generation evaluation")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["advanced", "baseline"],
        help="Strategies to evaluate (default: advanced baseline)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.strategies))
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Evaluation failed: %s", e)
        sys.exit(1)
