"""
Master pipeline runner.

Usage:
    uv run python pipeline/run_pipeline.py                     # run all steps
    uv run python pipeline/run_pipeline.py --steps collect     # just collect
    uv run python pipeline/run_pipeline.py --steps topics sentiment  # parallel-safe steps
"""

import argparse
import sys

from pipeline.config import logger

ALL_STEPS = ["collect", "preprocess", "topics", "sentiment", "synthesize"]


def run_step(step: str) -> None:
    logger.info(f"▶ Starting step: {step}")

    match step:
        case "collect":
            from pipeline.collect_appstore import run as collect_appstore
            from pipeline.collect_reddit import run as collect_reddit

            collect_reddit()
            collect_appstore()
        case "preprocess":
            from pipeline.preprocess import run as preprocess

            preprocess()
        case "topics":
            from pipeline.topic_model import run as topic_model

            topic_model()
        case "sentiment":
            from pipeline.sentiment import run as sentiment

            sentiment()
        case "synthesize":
            from pipeline.synthesize import run as synthesize

            synthesize()
        case _:
            raise ValueError(f"Unknown step: {step}")

    logger.success(f"✓ Completed step: {step}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Community Intelligence Pipeline")
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=ALL_STEPS,
        default=ALL_STEPS,
        metavar="STEP",
        help=f"Steps to run. Choices: {', '.join(ALL_STEPS)} (default: all)",
    )
    args = parser.parse_args()

    logger.info(f"Running pipeline steps: {' → '.join(args.steps)}")

    for step in args.steps:
        try:
            run_step(step)
        except Exception as e:
            logger.error(f"Step '{step}' failed: {e}")
            logger.info("Fix the error above and re-run with --steps {step} to resume")
            sys.exit(1)

    logger.success("Pipeline complete!")
    logger.info("Launch dashboard: uv run streamlit run ui/app.py")


if __name__ == "__main__":
    main()
