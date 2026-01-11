"""AWS CloudTrail ingestion adapter (Phase 1 - JSON/JSONL support)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.aws_plane_tagging import tag_plane
from src.security import prompt_firewall_event

logger = logging.getLogger(__name__)

REQUIRED_CLOUDTRAIL_FIELDS = ["eventTime", "eventSource", "eventName"]


def validate_required_fields(
    record: Dict[str, Any], source_file: str, record_index: int
) -> bool:
    """Validate required fields are present and not empty."""
    for field in REQUIRED_CLOUDTRAIL_FIELDS:
        if field not in record or not record[field] or str(record[field]).strip() == "":
            logger.warning(
                f"Skipping record {record_index} in {source_file}: "
                f"Missing or empty required field '{field}'"
            )
            return False
    return True


def safe_extract(
    record: Dict[str, Any], field_path: str, default: str = "Unknown"
) -> str:
    """Safely extract nested field with fallback to default."""
    try:
        keys = field_path.split(".")
        value: Any = record
        for key in keys:
            value = value.get(key, {})
        if not value or str(value).strip() == "":
            return default
        return str(value).strip()
    except (AttributeError, TypeError):
        return default


def extract_actor(record: Dict[str, Any]) -> str:
    """Extract actor with comprehensive fallback chain."""
    user_identity = record.get("userIdentity") or {}
    candidates = [
        user_identity.get("arn"),
        user_identity.get("userName"),
        user_identity.get("principalId"),
        user_identity.get("accountId"),
    ]
    for candidate in candidates:
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return "SYSTEM"


def ingest_cloudtrail(input_path: Path) -> List[Dict[str, Any]]:
    """
    Ingest AWS CloudTrail JSONL/JSON files into normalized event envelopes.
    Returns same structure as load_events() for seamless pipeline integration.
    """
    base_path = Path(input_path)
    if not base_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {base_path}")

    file_paths: List[Path] = []
    if base_path.is_file():
        file_paths = [base_path]
    elif base_path.is_dir():
        file_paths = sorted(base_path.glob("*.jsonl")) + sorted(
            base_path.glob("*.json")
        )
        if not file_paths:
            raise ValueError(f"No JSON or JSONL files found in {base_path}")
    else:
        raise ValueError(f"Input path is not a file or directory: {base_path}")

    events: List[Dict[str, Any]] = []
    for file_path in file_paths:
        events.extend(_load_cloudtrail_file(file_path))

    if not events:
        raise ValueError(
            "No valid CloudTrail events were loaded from the provided input"
        )

    logger.info(
        "Loaded %d CloudTrail events from %d file(s)", len(events), len(file_paths)
    )
    return events


def _load_cloudtrail_file(file_path: Path) -> List[Dict[str, Any]]:
    if file_path.suffix.lower() == ".jsonl":
        return _load_jsonl(file_path)
    if file_path.suffix.lower() == ".json":
        return _load_json(file_path)
    raise ValueError(f"Unsupported CloudTrail file extension: {file_path.suffix}")


def _load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            for record_index, line in enumerate(handle):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Skipping malformed JSON in %s at line %d: %s",
                        file_path,
                        record_index + 1,
                        exc,
                    )
                    continue

                event = _normalize_record(record, file_path, record_index)
                if event:
                    events.append(event)
    except OSError as exc:
        raise ValueError(f"Failed to read JSONL file {file_path}: {exc}") from exc

    return events


def _load_json(file_path: Path) -> List[Dict[str, Any]]:
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON file {file_path}: {exc}") from exc

    records = _extract_records(payload)
    events: List[Dict[str, Any]] = []
    for record_index, record in enumerate(records):
        event = _normalize_record(record, file_path, record_index)
        if event:
            events.append(event)
    return events


def _extract_records(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("Records"), list):
            return payload["Records"]
        return [payload]
    if isinstance(payload, list):
        return payload
    raise ValueError("Unexpected JSON payload shape for CloudTrail data.")


def _normalize_record(
    record: Dict[str, Any], source_file: Path, record_index: int
) -> Optional[Dict[str, Any]]:
    if not validate_required_fields(record, str(source_file), record_index):
        return None

    try:
        raw_hash = _hash_record(record)

        normalized_event = {
            "source": "aws_cloudtrail",
            "event_time": safe_extract(record, "eventTime"),
            "service": safe_extract(record, "eventSource"),
            "action": safe_extract(record, "eventName"),
            "actor": extract_actor(record),
            "actor_type": safe_extract(record, "userIdentity.type"),
            "src_ip": safe_extract(record, "sourceIPAddress"),
            "user_agent": safe_extract(record, "userAgent"),
            "aws_region": safe_extract(record, "awsRegion"),
            "account_id": safe_extract(record, "recipientAccountId"),
            "resources": _extract_resources(record),
            "error": _format_error(record),
            "raw_hash": raw_hash,
            "request_id": _extract_optional(record, "requestID", "requestId"),
            "event_type": _extract_optional(record, "eventType"),
            "read_only": _parse_bool(record.get("readOnly")),
            "management_event": _parse_bool(record.get("managementEvent")),
            "plane": tag_plane(
                safe_extract(record, "eventSource"),
                safe_extract(record, "eventName"),
            ),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to process record %d in %s: %s", record_index, source_file, exc
        )
        return None

    normalized_event = prompt_firewall_event(normalized_event)

    return {
        "source_file": str(source_file),
        "record_index": record_index,
        "event_id": _extract_event_id(record),
        "raw_event": normalized_event,
    }


def _extract_event_id(record: Dict[str, Any]) -> Optional[str]:
    event_id = record.get("eventID") or record.get("eventId")
    if event_id is None:
        return None
    return str(event_id)


def _hash_record(record: Dict[str, Any]) -> str:
    canonical = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_optional(record: Dict[str, Any], *field_paths: str) -> Optional[str]:
    for field_path in field_paths:
        value = safe_extract(record, field_path, default="")
        if value:
            return value
    return None


def _extract_resources(record: Dict[str, Any]) -> List[str]:
    resources = record.get("resources")
    if not resources:
        return ["NONE"]

    extracted: List[str] = []
    if isinstance(resources, list):
        for resource in resources:
            if isinstance(resource, dict):
                extracted.append(
                    resource.get("ARN") or resource.get("arn") or "UNKNOWN"
                )
            else:
                extracted.append(str(resource))
    else:
        extracted.append(str(resources))

    return extracted or ["NONE"]


def _format_error(record: Dict[str, Any]) -> Optional[str]:
    error_code = record.get("errorCode")
    error_message = record.get("errorMessage")
    if error_code and error_message:
        return f"{error_code}: {error_message}"
    if error_code:
        return str(error_code)
    if error_message:
        return str(error_message)
    return None


def _parse_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None
