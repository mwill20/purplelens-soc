"""Security policy enforcement for LLM responses.

LLM output is untrusted input:
- We enforce behavior, not hope for compliance
- PROHIBITED_PATTERNS blocks false authority claims
- validate_output() inspects all responses before acceptance
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.schemas import AnalysisOutput

logger = logging.getLogger(__name__)

# LLM output is untrusted input - enforce behavior with regex guardrails
# Guardrail contract: no false authority or claimed actions; we only recommend.
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    # Prevent first-person claims of taking actions while avoiding false positives
    # like "no action taken" or attacker-action descriptions.
    r"\b(I|we)\b.*\b(took|have taken|has taken|executed|completed|performed)\b.*\baction\b",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
    # Block base64 PowerShell commands (common attack vector)
    r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}",
]

PROMPT_INJECTION_RULES = [
    {
        "name": "ignore_previous",
        "pattern": r"ignore (all|any|previous|above) instructions",
        "action": "quarantine",
    },
    {
        "name": "system_prompt_request",
        "pattern": r"(system prompt|developer message|internal rules)",
        "action": "quarantine",
    },
    {
        "name": "role_override",
        "pattern": r"you are (an? )?(ai|assistant|chatgpt)|act as",
        "action": "redact",
    },
    {
        "name": "instruction_block",
        "pattern": r"(BEGIN|END) (SYSTEM|INSTRUCTION|PROMPT)",
        "action": "redact",
    },
    {
        "name": "tool_request",
        "pattern": r"(run|execute) (this )?(command|script)",
        "action": "redact",
    },
    {
        "name": "prompt_exfil",
        "pattern": r"(exfiltrate|leak).*(prompt|system)",
        "action": "quarantine",
    },
]


# We enforce behavior, not hope: validate_output() inspects every LLM response
def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """Check the raw LLM response for prohibited language."""

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Security validation: Checking response (%d chars) against %d patterns",
            len(response_text),
            len(PROHIBITED_PATTERNS),
        )

    for pattern in PROHIBITED_PATTERNS:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Security VIOLATION: Pattern '%s' matched (length=%d)",
                    pattern,
                    len(match.group(0)),
                )
            return False, f"Prohibited pattern detected: {pattern}"

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Security validation: PASS - No prohibited patterns found")
    return True, None


def prompt_firewall_event(
    raw_event: Dict[str, Any], skip_keys: Optional[set[str]] = None
) -> Dict[str, Any]:
    """Detect prompt injection strings and redact or quarantine."""

    if not isinstance(raw_event, dict):
        return raw_event

    skip_keys = skip_keys or set()
    injection_flags: List[str] = []
    sanitized_fields: List[str] = []
    quarantined = False

    def sanitize_text(text: str) -> Tuple[str, List[str], bool]:
        matched: List[str] = []
        quarantined_local = False
        sanitized = text
        for rule in PROMPT_INJECTION_RULES:
            if re.search(rule["pattern"], sanitized, re.IGNORECASE):
                matched.append(rule["name"])
                if rule["action"] == "quarantine":
                    quarantined_local = True
                sanitized = re.sub(
                    rule["pattern"],
                    "[REDACTED_PROMPT_INJECTION]",
                    sanitized,
                    flags=re.IGNORECASE,
                )
        return sanitized, matched, quarantined_local

    def walk(value: Any, path: str) -> Any:
        nonlocal quarantined
        if isinstance(value, dict):
            sanitized_dict: Dict[str, Any] = {}
            for key, entry in value.items():
                if key in skip_keys:
                    sanitized_dict[key] = entry
                else:
                    next_path = f"{path}.{key}" if path else key
                    sanitized_dict[key] = walk(entry, next_path)
            return sanitized_dict
        if isinstance(value, list):
            sanitized_list = []
            for idx, entry in enumerate(value):
                next_path = f"{path}[{idx}]"
                sanitized_list.append(walk(entry, next_path))
            return sanitized_list
        if isinstance(value, str):
            sanitized_text, matched, quarantined_local = sanitize_text(value)
            if matched:
                injection_flags.extend(matched)
                sanitized_fields.append(path)
            if quarantined_local:
                quarantined = True
            return sanitized_text
        return value

    sanitized_event = walk(raw_event, "")
    unique_flags = sorted(set(injection_flags))
    sanitized_event["injection_flags"] = unique_flags
    sanitized_event["sanitized"] = bool(unique_flags)
    sanitized_event["quarantined"] = quarantined
    if sanitized_fields:
        sanitized_event["sanitized_fields"] = sanitized_fields
    return sanitized_event


def validate_semantic_output(
    analysis: AnalysisOutput, events: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """Deterministic semantic validation for evidence mapping."""

    issues: List[str] = []
    event_lookup: Dict[Tuple[str, int], Dict[str, Any]] = {}

    def normalize_source(value: str | None) -> str | None:
        if not value:
            return None
        return Path(value).as_posix()

    for event in events:
        source_file = normalize_source(event.get("source_file"))
        if source_file is None:
            continue
        key = (source_file, event.get("record_index"))
        event_lookup[key] = event

    for finding in analysis.findings:
        for evidence in finding.evidence:
            source_file = normalize_source(evidence.source_file)
            if source_file is None:
                issues.append(
                    f"Evidence missing source reference: {evidence.source_file}:{evidence.record_index}"
                )
                continue
            key = (source_file, evidence.record_index)
            if key not in event_lookup:
                issues.append(
                    f"Evidence missing source reference: {evidence.source_file}:{evidence.record_index}"
                )
                continue
            expected_id = event_lookup[key].get("event_id")
            source_marker = (event_lookup[key].get("raw_event") or {}).get("source")
            if source_marker == "gcp" and not evidence.event_id:
                issues.append(
                    "Evidence missing event_id for GCP event: "
                    f"{evidence.source_file}:{evidence.record_index}"
                )
            if source_marker in {"gcp", "aws_cloudtrail"}:
                if evidence.event_id and expected_id and str(evidence.event_id) != str(expected_id):
                    issues.append(
                        "Evidence event_id mismatch: "
                        f"{evidence.source_file}:{evidence.record_index} "
                        f"expected={expected_id} got={evidence.event_id}"
                    )
                if evidence.event_id and expected_id is None:
                    issues.append(
                        "Evidence event_id provided but source event_id missing: "
                        f"{evidence.source_file}:{evidence.record_index}"
                    )

    return len(issues) == 0, issues
