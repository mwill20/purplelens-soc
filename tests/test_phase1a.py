"""
Usage:
  pytest tests/test_phase1a.py

Purpose:
  Validate core schemas and policy guardrails.

Limitations:
  - Uses synthetic data only.
"""

import pytest

from src.schemas import AnalysisOutput, Evidence, Finding, Hypothesis
from src.security import PROHIBITED_PATTERNS, validate_output


def test_imports_available() -> None:
    assert len(PROHIBITED_PATTERNS) > 0


def test_valid_analysis_output_instantiation() -> None:
    valid = AnalysisOutput(status="success", confidence=0.75)
    assert valid.status == "success"
    assert valid.confidence == 0.75


def test_security_validation_clean_text() -> None:
    valid, _ = validate_output("This is a clean response with no prohibited patterns")
    assert valid is True


@pytest.mark.parametrize(
    "text",
    [
        "I have removed the malicious file",
        "This is definitely malicious",
        "I have blocked the threat",
        "System modified to prevent attack",
        "Confirmed that this is a threat",
    ],
)
def test_security_validation_prohibited_text(text: str) -> None:
    valid, msg = validate_output(text)
    assert valid is False
    assert msg


def test_schema_rejects_invalid_status() -> None:
    with pytest.raises(Exception):
        AnalysisOutput(status="invalid_status", confidence=0.5)


def test_schema_rejects_confidence_out_of_range() -> None:
    with pytest.raises(Exception):
        AnalysisOutput(status="success", confidence=1.5)


def test_schema_rejects_invalid_severity() -> None:
    evidence = Evidence(source_file="test.jsonl", record_index=0, excerpt="test")
    with pytest.raises(Exception):
        Finding(
            title="test",
            summary="test",
            severity="ultra-critical",
            evidence=[evidence],
        )


def test_evidence_model_with_all_fields() -> None:
    evidence = Evidence(
        source_file="data/test.jsonl",
        record_index=42,
        event_id="4688",
        excerpt="powershell.exe -ExecutionPolicy Bypass",
    )
    assert evidence.event_id == "4688"


def test_finding_and_hypothesis_models() -> None:
    evidence = Evidence(
        source_file="data/test.jsonl",
        record_index=42,
        event_id="4688",
        excerpt="powershell.exe -ExecutionPolicy Bypass",
    )
    finding = Finding(
        title="Suspicious PowerShell",
        summary="PowerShell with bypass flag",
        severity="high",
        evidence=[evidence],
    )
    hypothesis = Hypothesis(description="Possible reconnaissance activity", confidence=0.68)
    assert finding.severity == "high"
    assert hypothesis.confidence == 0.68


def test_complete_analysis_output() -> None:
    evidence = Evidence(
        source_file="data/test.jsonl",
        record_index=42,
        event_id="4688",
        excerpt="powershell.exe -ExecutionPolicy Bypass",
    )
    finding = Finding(
        title="Suspicious PowerShell",
        summary="PowerShell with bypass flag",
        severity="high",
        evidence=[evidence],
    )
    hypothesis = Hypothesis(description="Possible reconnaissance activity", confidence=0.68)
    complete = AnalysisOutput(
        status="success",
        findings=[finding],
        hypotheses=[hypothesis],
        indicators_of_compromise=["powershell.exe -ExecutionPolicy Bypass"],
        recommended_next_steps=["Investigate PowerShell command history"],
        confidence=0.72,
    )
    assert complete.status == "success"
    assert len(complete.findings) == 1
    assert len(complete.hypotheses) == 1
