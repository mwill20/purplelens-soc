"""
GCP Audit Log Ingestion Adapter.
Handles multiple GCP export formats and normalizes to PurpleLens standard envelope.

Supports:
- JSON Arrays (Cloud Logging export to Storage)
- JSONL (Newline Delimited JSON)
- Pub/Sub wrappers (base64-encoded message payloads)

Implements data minimization: SHA-256 hash storage only.

GCP Adapter Stack (3-phase pipeline):
1. Normalize first: normalize_gcp_audit() -> standard envelope
2. Tag plane: tag_plane() -> control/data/telemetry classification
3. Enrich deterministically: classify_actor_type() + compute_automation_confidence()
"""

import base64
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.gcp_enrichment import (
    classify_actor_type,
    compute_automation_confidence,
    detect_automation_tool,
    detect_workload_identity,
    is_cross_project,
    is_private_ip,
)
from src.gcp_plane_tagging import tag_plane

logger = logging.getLogger(__name__)


def compute_raw_hash(raw_event: Dict[str, Any]) -> str:
    """
    Generate SHA-256 hash of the raw log entry.
    Used for data minimization (we store this hash, not the full raw blob).
    """
    # Sort keys to ensure deterministic hashing regardless of field order
    canonical = json.dumps(raw_event, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_gcp_log_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Smart loader that handles both JSON Arrays and JSONL (Newline Delimited).
    Also unwraps common Pub/Sub formats if present.

    Args:
        file_path: Path to the GCP audit log file

    Returns:
        List of raw GCP audit log dictionaries
    """
    records = []

    with file_path.open("r", encoding="utf-8") as f:
        first_char = f.read(1)
        f.seek(0)  # Reset to start

        # Strategy 1: JSON Array (starts with '[')
        if first_char == "[":
            try:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
            except json.JSONDecodeError:
                # Fallback: might be malformed or mixed, try line-by-line
                pass

        # Strategy 2: JSONL (Line-by-line)
        if not records:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # Skip malformed lines (logging policy)

    # Strategy 3: Pub/Sub Wrapper Unwrapping
    # Detect and unwrap: {"message": {"data": "<base64>", "attributes": {...}}}
    unwrapped = []
    for rec in records:
        if "message" in rec and isinstance(rec.get("message"), dict):
            msg = rec["message"]
            if "data" in msg:
                # Pub/Sub wrapper detected - extract nested audit log
                try:
                    decoded = base64.b64decode(msg["data"])
                    nested = json.loads(decoded)
                    unwrapped.append(nested)
                except (ValueError, json.JSONDecodeError, base64.binascii.Error):
                    # If unwrap fails, keep original
                    unwrapped.append(rec)
            else:
                unwrapped.append(rec)
        else:
            unwrapped.append(rec)

    return unwrapped


# Phase 1: Normalize first - convert raw GCP audit log to standard envelope
def normalize_gcp_audit(
    rec: Dict[str, Any], source_file: str, idx: int
) -> Dict[str, Any]:
    """
    Translate a raw GCP Audit Log into the PurpleLens standard envelope.

    Args:
        rec: Raw GCP audit log dictionary
        source_file: Path to the source file (for evidence tracking)
        idx: Record index within the file (for evidence tracking)

    Returns:
        Normalized event dictionary matching PurpleLens schema
    """
    # 1. Extract Core GCP Structures
    pp = rec.get("protoPayload") or {}
    auth = pp.get("authenticationInfo") or {}
    req_meta = pp.get("requestMetadata") or {}
    resource = rec.get("resource") or {}
    resource_labels = resource.get("labels") or {}

    # 2. Extract Critical Evidence Fields
    # insertId is the GCP Unique ID - Critical for audit trails
    insert_id = rec.get("insertId", "UNKNOWN")

    # 3. Phase 2: Tag plane - classify into control/data/telemetry
    service_name = pp.get("serviceName", "unknown")
    method_name = pp.get("methodName", "unknown")
    plane = tag_plane(service_name, method_name)  # Deterministic plane classification

    # 4. Extract fields for enrichment analysis
    principal_email = auth.get("principalEmail", "unknown")
    principal_subject = auth.get("principalSubject", "")
    # Some exports/synthetic packs may place a normalized userAgent at protoPayload.userAgent.
    # Prefer that when present so automation signals (e.g., Terraform) survive normalization.
    user_agent = pp.get("userAgent") or req_meta.get("callerSuppliedUserAgent", "")
    caller_ip = req_meta.get("callerIp", "")
    resource_name = pp.get("resourceName") or resource.get("type", "unknown")

    # Prefer resource.labels.project_id for project-scoped resources.
    # This supports cross-project simulation via label edits in exported log packs.
    resource_project_id = resource_labels.get("project_id")
    if resource_project_id and resource.get("type") == "project":
        resource_name = f"projects/{resource_project_id}"

    # 5. Phase 3: Enrich deterministically - no external API calls, pure logic
    actor_kind = classify_actor_type(principal_email)  # Human vs service account vs agent
    automation_tool = detect_automation_tool(user_agent)
    workload_identity_detected = detect_workload_identity(principal_subject)
    private_ip_detected = is_private_ip(caller_ip)
    cross_project_detected = is_cross_project(principal_email, resource_name)
    automation_confidence = compute_automation_confidence(  # Multi-signal confidence scoring
        actor_kind, automation_tool, workload_identity_detected, private_ip_detected
    )

    # 6. Construct Normalized Event (enrichment nested in raw_event)
    raw_event = {
        "source": "gcp",
        "event_time": rec.get("timestamp"),
        "plane": plane,
        "actor": principal_email,
        "action": f"{service_name}/{method_name}",
        "resource": resource_name,
        "src_ip": caller_ip,
        "user_agent": user_agent,
        "severity": rec.get("severity", "DEFAULT"),
        "raw_hash": compute_raw_hash(rec),
        "insertId": insert_id,
        # Phase 3 enrichment fields
        "actor_kind": actor_kind,
        "automation_tool": automation_tool,
        "automation_confidence": automation_confidence,
        "workload_identity": workload_identity_detected,
        "cross_project": cross_project_detected,
        "raw": rec,
    }

    # [DEBUG VISIBILITY] Log enrichment details if in debug mode
    # This allows verification without cluttering the final report evidence
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "GCP Enrichment [%s:%d]: ActorKind=%s, Tool=%s, Confidence=%s, CrossProject=%s",
            source_file,
            idx,
            actor_kind,
            automation_tool,
            automation_confidence,
            cross_project_detected,
        )

    return {
        "source_file": source_file,
        "record_index": idx,
        "event_id": insert_id,  # Maps to Evidence.event_id
        "raw_event": raw_event,
    }
