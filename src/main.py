"""
CLI entrypoint for the ThreatPrism AI SOC Assistant.
- "This is the entrypoint and control plane: parse args, configure logging, then run the pipeline."
- "The pipeline is a straight line: ingest -> normalize -> sanitize -> enrich -> llm_analyze -> validate_output -> report -> persist."
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

from src.llm_analyze import analyze_events, run_semantic_judge
from src.ops.ops_context import create_ops_context
from src.report import generate_report
from src.schemas import AnalysisOutput
from src.security import validate_output, validate_semantic_output
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


def _event_ref(event: dict) -> dict:
    return {
        "source_file": event.get("source_file"),
        "record_index": event.get("record_index"),
        "event_id": event.get("event_id"),
    }


def parse_args() -> argparse.Namespace:  # CLI options (input path, output mode, model, db)
    """Parse command-line arguments and return an argparse.Namespace.

    Returns:
        argparse.Namespace: Parsed CLI arguments including:
            - input: path to input file or directory
            - source: data source type (auto/windows/aws/gcp)
            - output: output mode (console/file)
            - model: LLM model to use
            - provider: LLM provider (openai/gemini)
            - db: path to SQLite database
            - verbose/debug/dry_run: logging and run controls
    """
    parser = argparse.ArgumentParser(description="ThreatPrism AI SOC Assistant")
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
    parser.add_argument(
        "--semantic-judge",
        action="store_true",
        help="Enable optional LLM semantic judge validation",
    )
    return parser.parse_args()


def configure_logging(verbose: bool, debug: bool, run_id: str) -> Path:
    # Console level based on flags, file level matches debug/verbose behavior
    console_level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING
    # File logging: DEBUG only when --debug is set, otherwise INFO for audit trail
    file_level = logging.DEBUG if debug else logging.INFO
    
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"run_{run_id}.log"

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    # Set root to lowest handler level to allow handlers to filter
    root_logger.setLevel(min(console_level, file_level))

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return log_path


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
    run_id = str(uuid.uuid4())
    args = parse_args()
    log_path = configure_logging(args.verbose, args.debug, run_id)
    ops = create_ops_context(run_id)
    ops.log_run_start(
        {
            "input": str(args.input),
            "model": args.model,
            "provider": args.provider,
            "dry_run": args.dry_run,
            "semantic_judge": args.semantic_judge,
        }
    )
    ops.stage_start("parse")
    ops.stage_end("parse", ok=True)

    events: list[dict] = []
    ok = False
    current_stage = "init"
    policy_valid = True
    semantic_valid = True
    judge_valid = True

    try:
        LOGGER.info(
            "Starting analysis run %s | model=%s | provider=%s | input=%s | dry_run=%s",
            run_id,
            args.model,
            args.provider,
            args.input,
            args.dry_run,
        )

        current_stage = "environment"
        ops.stage_start(current_stage)
        if not ensure_environment(args):
            ops.exception(
                current_stage,
                "MissingApiKey",
                f"Missing API key for provider={args.provider}",
            )
            return 1
        ops.stage_end(current_stage, ok=True)

        current_stage = "source_detect"
        ops.stage_start(current_stage, source_file=str(args.input))
        if args.source == "auto":
            decision, reason = detect_source(args.input)
        else:
            decision = args.source
            reason = f"User specified --source {args.source}"
        ops.set_source_type(decision)
        ops.stage_end(current_stage, ok=True, source_file=str(args.input))

        LOGGER.info(
            "source_detect",
            extra={
                "source": decision,
                "reason": reason,
                "input": str(args.input),
            },
        )
        LOGGER.info("Detected source type: %s | Reason: %s", decision, reason)

        current_stage = "ingest"
        ops.stage_start(current_stage, source_file=str(args.input))
        if decision == "aws":
            from src.ingest_aws import ingest_cloudtrail

            events = ingest_cloudtrail(args.input)
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

        ops.stage_end(
            current_stage,
            ok=True,
            source_file=str(args.input),
            records_out=len(events),
        )

        records_before = len(events)
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

            current_stage = "normalize"
            ops.stage_start(current_stage, records_in=records_before)
            events = correlate_events(events, CORRELATION_CONFIG)
            ops.stage_end(
                current_stage,
                ok=True,
                records_in=records_before,
                records_out=len(events),
            )
        else:
            current_stage = "normalize"
            ops.stage_start(current_stage, records_in=records_before)
            ops.stage_end(
                current_stage,
                ok=True,
                records_in=records_before,
                records_out=len(events),
            )

        current_stage = "sanitize"
        ops.stage_start(current_stage, records_in=len(events))
        prompt_injection_hits = 0
        sanitized_refs: list[dict] = []
        quarantined_refs: list[dict] = []
        affected_event_ids: list[str] = []
        retained_events: list[dict] = []

        for event in events:
            raw_event = event.get("raw_event", {})
            flags = raw_event.get("injection_flags") or []
            if flags:
                prompt_injection_hits += len(flags)
                sanitized_refs.append(_event_ref(event))
            if raw_event.get("quarantined"):
                quarantined_refs.append(_event_ref(event))
            if raw_event.get("sanitized") or raw_event.get("quarantined"):
                event_id = event.get("event_id")
                if event_id:
                    affected_event_ids.append(str(event_id))
                else:
                    source_file = event.get("source_file") or "unknown"
                    record_index = event.get("record_index")
                    affected_event_ids.append(f"{Path(source_file).name}:{record_index}")
            if not raw_event.get("quarantined"):
                retained_events.append(event)

        ops.metrics.record_prompt_injection(
            prompt_injection_hits,
            len(sanitized_refs),
            len(quarantined_refs),
        )
        ops.stage_end(
            current_stage,
            ok=True,
            records_in=len(events),
            records_out=len(retained_events),
            extra_fields={
                "prompt_injection_hits": prompt_injection_hits,
                "events_sanitized": len(sanitized_refs),
                "events_quarantined": len(quarantined_refs),
                "affected_event_ids": affected_event_ids,
                "sanitized_event_refs": sanitized_refs,
                "quarantined_event_refs": quarantined_refs,
            },
        )
        events = retained_events

        if decision == "gcp":
            current_stage = "enrich"
            ops.stage_start(current_stage, records_in=len(events))
            ops.stage_end(
                current_stage,
                ok=True,
                records_in=len(events),
                records_out=len(events),
            )

        unique_files = sorted({event["source_file"] for event in events})
        ops.metrics.set_counts(len(unique_files), len(events))

        if args.dry_run:
            print(
                f"Validation successful. Loaded {len(events)} events from {args.input}.",
                file=sys.stdout,
            )
            ok = True
            return 0

        initialize_database(args.db)
        current_stage = "llm_analyze"
        ops.stage_start(current_stage, records_in=len(events))
        analysis_data = analyze_events(                         # call analyze_events from llm_analyze.py
            events, model=args.model, provider=args.provider, ops=ops
        )
        ops.stage_end(
            current_stage,
            ok=True,
            records_in=len(events),
            records_out=len(events),
        )

        current_stage = "validate_output"
        ops.stage_start(current_stage, records_in=len(events))
        analysis = _validate_analysis_output(analysis_data)
        validation_errors: list[str] = []

        policy_valid, policy_error = validate_output(
            json.dumps(analysis_data, ensure_ascii=False)
        )
        if not policy_valid:
            LOGGER.error("Security policy violation: %s", policy_error)
            ops.metrics.record_error("SecurityPolicyViolation")
            if policy_error:
                validation_errors.append(f"Security policy violation: {policy_error}")

        semantic_valid, semantic_issues = validate_semantic_output(analysis, events)
        if not semantic_valid:
            ops.metrics.record_error("SemanticValidationFailed")
            sample_issues = "; ".join(semantic_issues[:3])
            LOGGER.error("Semantic validation failed: %s", sample_issues)
            if semantic_issues:
                validation_errors.append(f"Semantic validation failed: {sample_issues}")

        judge_issues: list[str] = []
        if args.semantic_judge and analysis.status == "success":
            judge_result = run_semantic_judge(
                analysis.model_dump(),
                events,
                model=args.model,
                provider=args.provider,
                ops=ops,
            )
            judge_valid = bool(judge_result.get("ok"))
            judge_issues = [
                str(issue) for issue in (judge_result.get("issues") or []) if issue
            ]
            if not judge_valid:
                ops.metrics.record_error("SemanticJudgeFailed")
                sample_issues = "; ".join(judge_issues[:3])
                LOGGER.error("Semantic judge failed: %s", sample_issues)
                if judge_issues:
                    validation_errors.append(f"Semantic judge failed: {sample_issues}")
        else:
            judge_valid = True

        if validation_errors:
            analysis = _build_error_analysis(
                "validation_error", "; ".join(validation_errors)
            )

        output_valid = policy_valid and semantic_valid and judge_valid
        ops.stage_end(
            current_stage,
            ok=output_valid,
            records_in=len(events),
            records_out=len(events),
        )

        current_stage = "report"
        ops.stage_start(current_stage, records_in=len(events))
        report_text = generate_report(analysis, event_count=len(events))
        _output_report(report_text, args.output, run_id)
        ops.stage_end(
            current_stage,
            ok=True,
            records_in=len(events),
            records_out=len(events),
        )

        current_stage = "persist"
        ops.stage_start(current_stage, records_in=len(events))
        run_timestamp = datetime.now(timezone.utc)
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
        ops.stage_end(
            current_stage,
            ok=True,
            records_in=len(events),
            records_out=len(events),
        )

        ok = analysis.status == "success" and output_valid
        LOGGER.info("Analysis complete with status=%s", analysis.status)
        return 0 if ok else 1
    except SystemExit as exc:
        ops.exception(current_stage, "SystemExit", str(exc))
        LOGGER.error("Failed to complete run: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        ops.exception(current_stage, exc.__class__.__name__, str(exc))
        LOGGER.error("Failed to complete run: %s", exc)
        return 1
    finally:
        ops.finalize(ok)
        print(f"Ops artifacts written to {ops.run_dir}", file=sys.stdout)
        print(f"Debug log written to {log_path}", file=sys.stdout)


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
    if output_path.exists():
        for counter in range(1, 1000):
            candidate = reports_dir / f"analysis_{run_id}-{counter}.txt"
            if not candidate.exists():
                output_path = candidate
                break
    output_path.write_text(report_text, encoding="utf-8")
    if destination == "console":
        print(report_text)
    print(f"Report written to {output_path}", file=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
