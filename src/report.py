from __future__ import annotations

import re


def _generate_executive_summary(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """
    Generate an executive summary section for the SOC report.
    Includes risk level, key statistics, critical issues, and top recommendation.
    """
    # Count severities
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in analysis.findings:
        sev = finding.severity.lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Determine risk level
    if severity_counts["critical"] > 0 or severity_counts["high"] > 0:
        risk_level = "**HIGH**"
        risk_detail = _build_severity_breakdown(severity_counts)
    elif severity_counts["medium"] > 0:
        risk_level = "**MEDIUM**"
        risk_detail = _build_severity_breakdown(severity_counts)
    elif severity_counts["low"] > 0 or severity_counts["info"] > 0:
        risk_level = "**LOW**"
        risk_detail = _build_severity_breakdown(severity_counts)
    else:
        risk_level = "**MINIMAL**"
        risk_detail = _build_severity_breakdown(severity_counts)

    # Key statistics
    finding_count = len(analysis.findings)
    hypothesis_count = len(analysis.hypotheses)
    ioc_count = len(analysis.indicators_of_compromise)
    top_recommendation = _select_top_recommendation(analysis)

    # Critical issues (show up to 3)
    critical_issues = [f for f in analysis.findings if f.severity.lower() == "critical"]
    critical_lines = []
    for f in critical_issues[:3]:
        critical_lines.append(f"- **CRITICAL**: {f.title}")
    if not critical_lines and severity_counts["high"] > 0:
        # Show high if no critical
        high_issues = [f for f in analysis.findings if f.severity.lower() == "high"]
        for f in high_issues[:3]:
            critical_lines.append(f"- **HIGH**: {f.title}")

    lines = [
        "## Executive Summary",
        f"- **Risk Level**: {risk_level} {risk_detail}",
        f"- **Analysis Scope**: {event_count} events analyzed",
        f"- **Key Findings**: {finding_count} security findings identified",
        f"- **Hypotheses**: {hypothesis_count} investigative theories",
        f"- **Indicators of Compromise**: {ioc_count} IOCs detected",
        f"- **Immediate Action Required**: {top_recommendation}",
        "",
        "**Critical Issues:**",
    ]
    if critical_lines:
        lines.extend(critical_lines)
    else:
        lines.append("- (none)")
    lines.append("\n---\n")
    return "\n".join(lines)


from typing import Dict, List

from src.schemas import AnalysisOutput, Evidence, Finding, Hypothesis

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

STATUS_EXPLANATIONS: Dict[str, str] = {
    "llm_error": "LLM API call failed or returned invalid response.",
    "timeout": "LLM call exceeded the 60-second timeout limit.",
    "validation_error": "LLM output violated schema or security policies.",
}


def generate_report(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """Generate deterministic SOC report from the structured analysis object."""

    # Determinism contract: same structured input yields the same report text.
    if analysis.status != "success":
        return generate_error_report(analysis)

    deduped_findings = _merge_findings(analysis.findings)
    deduped_hypotheses = _dedupe_hypotheses(analysis.hypotheses)
    deduped_iocs = _dedupe_iocs(analysis.indicators_of_compromise)
    deduped_next_steps = _dedupe_actions(analysis.recommended_next_steps)

    analysis_for_report = analysis.model_copy(
        update={
            "findings": deduped_findings,
            "hypotheses": deduped_hypotheses,
            "indicators_of_compromise": deduped_iocs,
            "recommended_next_steps": deduped_next_steps,
        }
    )

    sections: List[str] = []
    sections.extend(_header_lines("Security Analysis Report"))
    # Add executive summary at the top
    sections.append(
        _generate_executive_summary(analysis_for_report, event_count=event_count)
    )
    sections.append("## FINDINGS")
    sections.extend(_format_findings(analysis_for_report.findings))
    sections.append("## HYPOTHESES")
    sections.extend(_format_hypotheses(analysis_for_report.hypotheses))
    sections.append("## INDICATORS OF COMPROMISE")
    sections.extend(_format_list(analysis_for_report.indicators_of_compromise))
    sections.append("## RECOMMENDED NEXT STEPS")
    sections.extend(_format_list(analysis_for_report.recommended_next_steps))
    sections.append("=" * 80)
    sections.append(f"Overall Confidence: {analysis.confidence:.2f}")
    sections.append("=" * 80)
    return "\n".join(sections)


def generate_error_report(analysis: AnalysisOutput) -> str:
    """Generate degraded report describing partial results and next actions."""

    sections: List[str] = []
    sections.extend(_header_lines("Analysis Report - INCOMPLETE"))
    sections.append(f"STATUS: {analysis.status}")
    explanation = STATUS_EXPLANATIONS.get(
        analysis.status, "Analysis did not complete successfully."
    )
    sections.append(f"ERROR: {analysis.error_message or explanation}")
    sections.append("")
    # Provide a minimal Executive Summary for consistency with successful reports
    sections.append("## Executive Summary")
    partial_event_count = len(analysis.findings) + len(
        analysis.indicators_of_compromise
    )
    sections.append("- **Risk Level**: UNKNOWN")
    sections.append(f"- **Analysis Scope**: {partial_event_count} events (partial)")
    sections.append(
        f"- **Key Findings**: {len(analysis.findings)} security findings identified (partial)"
    )
    sections.append(
        f"- **Hypotheses**: {len(analysis.hypotheses)} investigative theories (partial)"
    )
    sections.append(
        f"- **Indicators of Compromise**: {len(analysis.indicators_of_compromise)} IOCs detected (partial)"
    )
    sections.append("\n---\n")
    sections.append(
        f"PARTIAL FINDINGS: {len(analysis.findings)} extracted before failure"
    )
    if analysis.findings:
        sections.extend(_format_findings(analysis.findings))

    sections.append("RECOMMENDED ACTION:")
    sections.append("- Review logs for additional details.")
    if analysis.status == "llm_error":
        sections.append("- Check LLM API connectivity and credentials.")
    if analysis.status == "timeout":
        sections.append("- Re-run analysis with fewer events or during lower load.")
    if analysis.status == "validation_error":
        sections.append("- Inspect LLM output logs for policy or schema violations.")
    sections.append("- Retry the CLI with --verbose for additional diagnostics.")
    sections.append("- Verify input files are valid JSONL if the issue persists.")
    sections.append("=" * 80)
    return "\n".join(sections)


def _header_lines(subtitle: str) -> List[str]:
    return [
        "=" * 80,
        "PURPLELENS AI SOC ASSISTANT",
        subtitle,
        "=" * 80,
        "",
    ]


def _format_findings(findings: List[Finding]) -> List[str]:
    if not findings:
        return ["(none)", ""]

    sections: List[str] = []
    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.index(f.severity))

    for finding in ordered:
        sections.append(f"### [{finding.severity.upper()}] {finding.title}")
        sections.append(f"Summary: {finding.summary}")
        sections.append("Evidence:")
        for ev in finding.evidence:
            event_id_part = f" | event_id={ev.event_id}" if ev.event_id else ""
            sections.append(
                f"  - {ev.source_file}:{ev.record_index}{event_id_part} | {ev.excerpt}"
            )
        sections.append("")

    return sections


def _format_hypotheses(hypotheses: List[Hypothesis]) -> List[str]:
    if not hypotheses:
        return ["(none)", ""]
    return [
        f"- {h.description} (confidence: {h.confidence:.2f})" for h in hypotheses
    ] + [""]


def _format_list(items: List[str]) -> List[str]:
    if not items:
        return ["(none)", ""]
    return [f"- {item}" for item in items] + [""]


_ACTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "any",
    "around",
    "audit",
    "at",
    "by",
    "check",
    "conduct",
    "consider",
    "examine",
    "for",
    "from",
    "in",
    "investigate",
    "monitor",
    "of",
    "on",
    "other",
    "perform",
    "review",
    "the",
    "to",
    "with",
    "account",
    "accounts",
    "activity",
    "activities",
    "compromise",
    "possible",
    "potential",
    "sign",
    "signs",
    "suspicious",
    "unauthorized",
    "user",
}


def _dedupe_actions(items: List[str]) -> List[str]:
    seen_tokens: List[set[str]] = []
    deduped: List[str] = []
    for item in items:
        tokens = _action_tokens(item)
        if not tokens:
            continue
        if any(
            _jaccard_similarity(tokens, existing) >= 0.6 for existing in seen_tokens
        ):
            continue
        seen_tokens.append(tokens)
        deduped.append(item)
    return deduped


def _normalize_action(text: str) -> str:
    normalized = _normalize_text(text)
    tokens = [token for token in normalized.split() if token not in _ACTION_STOPWORDS]
    return " ".join(tokens)


def _action_tokens(text: str) -> set[str]:
    normalized = _normalize_action(text)
    tokens = normalized.split()
    if not tokens:
        tokens = _normalize_text(text).split()
    return set(tokens)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left & right
    union = left | right
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _dedupe_iocs(items: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for item in items:
        normalized = _normalize_ioc(item)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(item)
    return deduped


def _normalize_ioc(text: str) -> str:
    return " ".join(text.split()).lower()


def _dedupe_hypotheses(hypotheses: List[Hypothesis]) -> List[Hypothesis]:
    seen = set()
    deduped: List[Hypothesis] = []
    for hypothesis in hypotheses:
        normalized = _normalize_text(hypothesis.description)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(hypothesis)
    return deduped


def _merge_findings(findings: List[Finding]) -> List[Finding]:
    merged: Dict[str, Finding] = {}

    for finding in findings:
        key = _merge_key(finding.title)
        if key not in merged:
            merged[key] = finding
            continue

        existing = merged[key]
        merged[key] = existing.model_copy(
            update={
                "severity": _worst_severity(existing.severity, finding.severity),
                "summary": _merge_summaries(existing.summary, finding.summary),
                "evidence": _dedupe_evidence(existing.evidence + finding.evidence),
            }
        )

    return list(merged.values())


def _merge_key(title: str) -> str:
    normalized = _normalize_text(title)
    # Normalize common variants to consistent keys for merging and display
    if "crypto" in normalized and ("key" in normalized or "keyversion" in normalized):
        return "destruction of cryptokeyversion"
    if "credential dump" in normalized or "credential dumping" in normalized:
        return "credential dumping"
    if "user account" in normalized and (
        "modification" in normalized or "change" in normalized
    ):
        return "user account change"
    if "jjs" in normalized or (
        "dll" in normalized and "side" in normalized and "loading" in normalized
    ):
        return "jjs execution"
    if (
        "group policy" in normalized
        or "gpo" in normalized
        or "grouppolicycontainer" in normalized
        or "policy container" in normalized
    ):
        return "group policy change"
    if "security policy" in normalized:
        return "security policy change"
    if "object access" in normalized or (
        "object" in normalized and "access" in normalized
    ):
        return "object access"
    return normalized


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    cleaned = " ".join(cleaned.split())
    return _singularize_last_word(cleaned)


def _singularize_last_word(text: str) -> str:
    parts = text.split()
    if not parts:
        return text
    last = parts[-1]
    if last.endswith("s") and len(last) > 3 and not last.endswith("ss"):
        parts[-1] = last[:-1]
    return " ".join(parts)


def _dedupe_evidence(evidence_list: List[Evidence]) -> List[Evidence]:
    seen = set()
    deduped: List[Evidence] = []
    for evidence in evidence_list:
        key = (
            evidence.source_file,
            evidence.record_index,
            evidence.event_id,
            evidence.excerpt,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(evidence)
    return deduped


def _merge_summaries(existing: str, incoming: str) -> str:
    if not incoming:
        return existing
    if incoming.strip().lower() == existing.strip().lower():
        return existing
    if incoming.strip() in existing:
        return existing
    if _summary_similarity(existing, incoming) >= 0.5:
        return existing
    return f"{existing} Additional context: {incoming}"


def _summary_similarity(existing: str, incoming: str) -> float:
    existing_tokens = set(_normalize_text(existing).split())
    incoming_tokens = set(_normalize_text(incoming).split())
    return _jaccard_similarity(existing_tokens, incoming_tokens)


def _worst_severity(current: str, incoming: str) -> str:
    current_rank = _severity_rank(current)
    incoming_rank = _severity_rank(incoming)
    return current if current_rank <= incoming_rank else incoming


def _severity_rank(severity: str) -> int:
    try:
        return SEVERITY_ORDER.index(severity.lower())
    except ValueError:
        return len(SEVERITY_ORDER)


def _build_severity_breakdown(severity_counts: Dict[str, int]) -> str:
    parts: List[str] = []
    total = 0
    for label in ["critical", "high", "medium", "low", "info"]:
        count = severity_counts.get(label, 0)
        if count:
            parts.append(f"{count} {label}")
            total += count

    if not parts:
        return "(no findings)"

    noun = "finding" if total == 1 else "findings"
    return f"({', '.join(parts)} severity {noun})"


def _select_top_recommendation(analysis: AnalysisOutput) -> str:
    if analysis.findings:
        top_finding = min(
            analysis.findings, key=lambda finding: _severity_rank(finding.severity)
        )
        if top_finding.severity.lower() in {"critical", "high"}:
            return f"Prioritize investigation of: {top_finding.title}."

    if analysis.recommended_next_steps:
        return analysis.recommended_next_steps[0]

    if analysis.findings:
        top_finding = min(
            analysis.findings, key=lambda finding: _severity_rank(finding.severity)
        )
        return f"Prioritize investigation of: {top_finding.title}."

    return "None"
