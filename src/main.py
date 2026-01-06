"""
CLI entrypoint for the PurpleLens AI SOC Assistant.
- "This is the entrypoint and control plane: parse args, configure logging, then run the pipeline."
- "The pipeline is a straight line: ingest -> analyze -> validate -> report -> persist."
- "Report output is saved to `reports/` and the path is printed, so the demo can always show the file."
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

# Load environment variables from .env if either provider key is missing.
# This allows tests to control the environment while still supporting .env for normal use.
if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("GEMINI_API_KEY"):
    load_dotenv()

from src.llm_analyze import analyze_events
from src.report import generate_report
from src.schemas import AnalysisOutput
from src.security import validate_output
from src.storage import initialize_database, save_analysis

LOGGER = logging.getLogger(__name__)


def _sample_json_record(file_path: Path) -> dict | None:
    try:
        if file_path.suffix.lower() == ".jsonl":
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    return json.loads(stripped)
            return None
        if file_path.suffix.lower() == ".json":
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                return data[0] if data else None
            if isinstance(data, dict):
                return data
            return None
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _unwrap_pubsub_record(record: dict) -> dict | None:
    message = record.get("message")
    if isinstance(message, dict) and "data" in message:
        try:
            decoded = base64.b64decode(message["data"])
            nested = json.loads(decoded)
            return nested if isinstance(nested, dict) else None
        except (ValueError, json.JSONDecodeError, base64.binascii.Error):
            return None
    return None


def _detect_json_source(file_path: Path) -> str | None:
    record = _sample_json_record(file_path)
    if not isinstance(record, dict):
        return None

    unwrapped = _unwrap_pubsub_record(record)
    if isinstance(unwrapped, dict):
        record = unwrapped

    if (
        "Records" in record
        or "eventVersion" in record
        or ("eventSource" in record and "eventName" in record)
    ):
        return "aws"

    if "protoPayload" in record or "insertId" in record or "logName" in record:
        return "gcp"

    if "Event" in record:
        return "windows"

    return None


def detect_source(input_path: Path) -> tuple[str, str]:
    """
    Detect source type with explicit logging order

    Returns:
        (source_type, reason) tuple

    Raises:
        SystemExit: If ambiguous input detected
    """
    input_path = Path(input_path)
    if input_path.is_file():
        # Step 1: Extension check
        if input_path.suffix.lower() == ".evtx":
            return "windows", f"EVTX extension detected: {input_path.suffix}"
        elif input_path.suffix.lower() in [".json", ".jsonl"]:
            detected = _detect_json_source(input_path)
            if detected == "aws":
                return "aws", "CloudTrail schema markers detected"
            if detected == "gcp":
                return "gcp", "GCP schema markers detected"
            if input_path.name.lower().startswith("gcp_"):
                return "gcp", "GCP filename prefix detected"
            return "windows", "JSON without CloudTrail/GCP markers"
        else:
            raise SystemExit(f"Unsupported file extension: {input_path.suffix}")
    elif input_path.is_dir():
        # Check for mixed directory
        evtx_files = list(input_path.glob("*.evtx"))
        json_files = list(input_path.glob("*.json")) + list(input_path.glob("*.jsonl"))

        if evtx_files and json_files:
            raise SystemExit(
                "Ambiguous input directory contains both EVTX and JSON files. "
                "Use --source aws|windows to specify data type."
            )
        elif evtx_files:
            return "windows", f"Directory contains {len(evtx_files)} EVTX files"
        elif json_files:
            detected_sources = set()
            for json_file in json_files:
                detected = _detect_json_source(json_file)
                if detected is None and json_file.name.lower().startswith("gcp_"):
                    detected = "gcp"
                detected_sources.add(detected or "windows")

            if len(detected_sources) > 1:
                raise SystemExit(
                    "Ambiguous input directory contains multiple JSON source types. "
                    "Use --source gcp|aws|windows to specify data type."
                )

            detected = detected_sources.pop()
            if detected == "aws":
                return "aws", "CloudTrail schema markers detected"
            if detected == "gcp":
                return "gcp", "GCP schema markers detected"
            return "windows", f"Directory contains {len(json_files)} JSON files"
        else:
            raise SystemExit(f"No supported files found in directory: {input_path}")
    else:
        raise SystemExit(f"Input path does not exist: {input_path}")


def parse_args() -> (
    argparse.Namespace
):  # for CLI options (input path, output mode, model, db)
    parser = argparse.ArgumentParser(description="PurpleLens AI SOC Assistant")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to directory containing EVTX, CloudTrail, or GCP audit logs",
    )
    parser.add_argument(
        "--source",
        choices=["auto", "windows", "aws", "gcp"],
        default="auto",
        help="Data source type (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        choices=["console", "file"],
        default="console",
        help="Console output (report is always saved to reports/)",
    )
    parser.add_argument(
        "--model",
        default="gemini-flash-latest",
        help="LLM model to use (default: gemini-flash-latest)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini"],
        default="gemini",
        help="LLM provider to use (default: gemini)",
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
        "--debug",
        action="store_true",
        help="Enable debug logging (includes enrichment details)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs only, do not call LLM",
    )
    return parser.parse_args()


def configure_logging(verbose: bool, debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_environment(
    args: argparse.Namespace,
) -> bool:  # for API key checks and DB path setup
    if not args.dry_run:
        if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            LOGGER.error("OPENAI_API_KEY environment variable not set.")
            return False
        if args.provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
            LOGGER.error("GEMINI_API_KEY environment variable not set.")
            return False
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    return True


def main() -> int:  # for the one-pass orchestration sequence.
    args = parse_args()
    configure_logging(args.verbose, args.debug)

    run_id = str(uuid.uuid4())
    LOGGER.info(
        "Starting analysis run %s | model=%s | provider=%s | input=%s | dry_run=%s",
        run_id,
        args.model,
        args.provider,
        args.input,
        args.dry_run,
    )

    if not ensure_environment(args):
        return 1

    try:
        # Source detection and routing
        if args.source == "auto":
            decision, reason = detect_source(args.input)
        else:
            decision = args.source
            reason = f"User specified --source {args.source}"

        LOGGER.info(
            "source_detect",
            extra={
                "source": decision,
                "reason": reason,
                "input": str(args.input),
            },
        )
        LOGGER.info("Detected source type: %s | Reason: %s", decision, reason)

        # Route to appropriate ingestion
        if decision == "aws":
            from src.ingest_aws import ingest_cloudtrail

            events = ingest_cloudtrail(args.input)  # Will raise NotImplementedError
        elif decision == "gcp":
            from src.ingest_gcp import load_gcp_log_file, normalize_gcp_audit

            input_path = Path(args.input)
            if input_path.is_file():
                file_paths = [input_path]
            elif input_path.is_dir():
                file_paths = sorted(input_path.glob("*.jsonl")) + sorted(
                    input_path.glob("*.json")
                )
            else:
                raise ValueError(f"Input path is not a file or directory: {input_path}")

            if not file_paths:
                raise ValueError(f"No JSON or JSONL files found in {input_path}")

            events = []
            for file_path in file_paths:
                records = load_gcp_log_file(file_path)
                for idx, record in enumerate(records):
                    events.append(normalize_gcp_audit(record, str(file_path), idx))

            if not events:
                raise ValueError(
                    "No valid GCP events were loaded from the provided input"
                )
        elif decision == "windows":
            from src.ingest import load_events

            events = load_events(args.input)
        else:
            raise SystemExit(f"Unknown source type: {decision}")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to load events: %s", exc)
        return 1

    if (
        len(
            [
                e
                for e in events
                if e.get("raw_event", {}).get("source") == "aws_cloudtrail"
            ]
        )
        > 1
    ):
        from src.aws_correlate import correlate_events
        from src.config_aws import CORRELATION_CONFIG

        events = correlate_events(events, CORRELATION_CONFIG)

    if args.dry_run:
        print(
            f"Validation successful. Loaded {len(events)} events from {args.input}.",
            file=sys.stdout,
        )
        return 0

    initialize_database(args.db)
    analysis_data = analyze_events(events, model=args.model, provider=args.provider)
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
