
from __future__ import annotations

def _generate_executive_summary(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """
    Generate an executive summary section for the SOC report.
    Includes risk level, key statistics, critical issues, and top recommendation.
    """
    # Count severities
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in analysis.findings:
        sev = finding.severity.lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Determine risk level
    if severity_counts["critical"] > 0:
        risk_level = "🔴 **HIGH**"
        risk_detail = f"({severity_counts['critical']} critical, {severity_counts['high']} high-severity findings)"
    elif severity_counts["high"] > 0:
        risk_level = "🟠 **MEDIUM**"
        risk_detail = f"({severity_counts['high']} high, {severity_counts['medium']} medium-severity findings)"
    elif severity_counts["medium"] > 0:
        risk_level = "🟡 **LOW**"
        risk_detail = f"({severity_counts['medium']} medium-severity findings)"
    else:
        risk_level = "🟢 **MINIMAL**"
        risk_detail = "(all findings are low severity)"

    # Key statistics
    finding_count = len(analysis.findings)
    hypothesis_count = len(analysis.hypotheses)
    ioc_count = len(analysis.indicators_of_compromise)
    top_recommendation = analysis.recommended_next_steps[0] if analysis.recommended_next_steps else "None"

    # Critical issues (show up to 3)
    critical_issues = [f for f in analysis.findings if f.severity.lower() == "critical"]
    critical_lines = []
    for f in critical_issues[:3]:
        critical_lines.append(f"- 🔴 **CRITICAL**: {f.title}")
    if not critical_lines and severity_counts["high"] > 0:
        # Show high if no critical
        high_issues = [f for f in analysis.findings if f.severity.lower() == "high"]
        for f in high_issues[:3]:
            critical_lines.append(f"- 🟠 **HIGH**: {f.title}")


    lines = [
        "## 📊 Executive Summary",
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

from src.schemas import AnalysisOutput, Finding, Hypothesis

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

STATUS_EXPLANATIONS: Dict[str, str] = {
    "llm_error": "LLM API call failed or returned invalid response.",
    "timeout": "LLM call exceeded the 60-second timeout limit.",
    "validation_error": "LLM output violated schema or security policies.",
}

def generate_report(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """Generate deterministic SOC report from the structured analysis object."""

    if analysis.status != "success":
        return generate_error_report(analysis)

    sections: List[str] = []
    sections.extend(_header_lines("Security Analysis Report"))
    # Add executive summary at the top
    sections.append(_generate_executive_summary(analysis, event_count=event_count))
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
