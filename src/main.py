"""CLI entrypoint for the PurpleLens AI SOC Assistant."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import ValidationError

# Load environment variables from .env file if OPENAI_API_KEY not already set
# This allows tests to control the environment while still supporting .env for normal use
if not os.environ.get("OPENAI_API_KEY"):
    load_dotenv()

from src.ingest import load_events
from src.llm_analyze import analyze_events
from src.report import generate_report
from src.schemas import AnalysisOutput
from src.security import validate_output
from src.storage import initialize_database, save_analysis

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PurpleLens AI SOC Assistant")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to directory containing parsed EVTX JSONL files",
    )
    parser.add_argument(
        "--output",
        choices=["console", "file"],
        default="console",
        help="Console output (report is always saved to reports/)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--db",
        default="db/analysis.db",
        help="Path to SQLite database (default: db/analysis.db)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs only, do not call LLM",
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_environment(args: argparse.Namespace) -> bool:
    if not args.dry_run and not os.environ.get("OPENAI_API_KEY"):
        LOGGER.error("OPENAI_API_KEY environment variable not set.")
        return False
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    return True


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    run_id = str(uuid.uuid4())
    LOGGER.info(
        "Starting analysis run %s | model=%s | input=%s | dry_run=%s",
        run_id,
        args.model,
        args.input,
        args.dry_run,
    )

    if not ensure_environment(args):
        return 1

    try:
        events = load_events(args.input)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to load events: %s", exc)
        return 1

    if args.dry_run:
        print(
            f"Validation successful. Loaded {len(events)} events from {args.input}.",
            file=sys.stdout,
        )
        return 0

    initialize_database(args.db)
    analysis_data = analyze_events(events, model=args.model)
    analysis = _validate_analysis_output(analysis_data)

    policy_valid, policy_error = validate_output(
        json.dumps(analysis_data, ensure_ascii=False)
    )
    if not policy_valid:
        LOGGER.error("Security policy violation: %s", policy_error)
        analysis = _build_error_analysis("validation_error", policy_error)

    report_text = generate_report(analysis, event_count=len(events))
    _output_report(report_text, args.output, run_id)

    run_timestamp = datetime.now(timezone.utc)
    unique_files = sorted({event["source_file"] for event in events})

    try:
        save_analysis(
            db_path=args.db,
            run_id=run_id,
            analysis=analysis,
            input_files=unique_files,
            model_used=args.model,
            report_text=report_text,
            report_generated_at=datetime.now(timezone.utc),
            run_timestamp=run_timestamp,
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to persist analysis: %s", exc)
        return 1

    LOGGER.info("Analysis complete with status=%s", analysis.status)
    return 0 if analysis.status == "success" else 1


def _validate_analysis_output(data: dict) -> AnalysisOutput:
    try:
        return AnalysisOutput.model_validate(data)
    except ValidationError as exc:
        LOGGER.error("Schema validation failed: %s", exc)
        return _build_error_analysis("validation_error", "Schema validation failed.")


def _build_error_analysis(status: str, message: str | None) -> AnalysisOutput:
    return AnalysisOutput(
        status=status,
        error_message=message,
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )


def _output_report(report_text: str, destination: str, run_id: str) -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = reports_dir / f"analysis_{run_id}.txt"
    output_path.write_text(report_text, encoding="utf-8")
    if destination == "console":
        print(report_text)
    print(f"Report written to {output_path}", file=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
