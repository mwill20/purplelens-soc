"""Deterministic SOC-style report generation."""

from __future__ import annotations

from typing import Dict, List

from src.schemas import AnalysisOutput, Finding, Hypothesis

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

STATUS_EXPLANATIONS: Dict[str, str] = {
    "llm_error": "LLM API call failed or returned invalid response.",
    "timeout": "LLM call exceeded the 60-second timeout limit.",
    "validation_error": "LLM output violated schema or security policies.",
}


def generate_report(analysis: AnalysisOutput) -> str:
    """Generate deterministic SOC report from the structured analysis object."""

    if analysis.status != "success":
        return generate_error_report(analysis)

    sections: List[str] = []
    sections.extend(_header_lines("Analysis Report"))
    sections.append("## FINDINGS")
    sections.extend(_format_findings(analysis.findings))
    sections.append("## HYPOTHESES")
    sections.extend(_format_hypotheses(analysis.hypotheses))
    sections.append("## INDICATORS OF COMPROMISE")
    sections.extend(_format_list(analysis.indicators_of_compromise))
    sections.append("## RECOMMENDED NEXT STEPS")
    sections.extend(_format_list(analysis.recommended_next_steps))
    sections.append("=" * 80)
    sections.append(f"Overall Confidence: {analysis.confidence:.2f}")
    sections.append("=" * 80)
    return "\n".join(sections)


def generate_error_report(analysis: AnalysisOutput) -> str:
    """Generate degraded report describing partial results and next actions."""

    sections: List[str] = []
    sections.extend(_header_lines("Analysis Report — INCOMPLETE"))
    sections.append(f"STATUS: {analysis.status}")
    explanation = STATUS_EXPLANATIONS.get(
        analysis.status, "Analysis did not complete successfully."
    )
    sections.append(f"ERROR: {analysis.error_message or explanation}")
    sections.append("")
    sections.append(f"PARTIAL FINDINGS: {len(analysis.findings)} extracted before failure")
    if analysis.findings:
        sections.extend(_format_findings(analysis.findings))

    sections.append("RECOMMENDED ACTION:")
    sections.append("- Review logs for additional details.")
    if analysis.status == "llm_error":
        sections.append("- Check OpenAI API connectivity and credentials.")
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
        "BESPIN AI SECURITY ANALYST ASSISTANT",
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
            sections.append(
                f"  - {ev.source_file}:{ev.record_index} | {ev.excerpt}"
            )
        sections.append("")

    return sections


def _format_hypotheses(hypotheses: List[Hypothesis]) -> List[str]:
    if not hypotheses:
        return ["(none)", ""]
    return [f"- {h.description} (confidence: {h.confidence:.2f})" for h in hypotheses] + [
        ""
    ]


def _format_list(items: List[str]) -> List[str]:
    if not items:
        return ["(none)", ""]
    return [f"- {item}" for item in items] + [""]
