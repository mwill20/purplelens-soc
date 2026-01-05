"""
Usage:
  pytest tests/test_phase1d.py

Purpose:
  Validate deterministic report generation and formatting.

Limitations:
  - Uses synthetic findings; does not require external data.
"""

import time

from src.report import generate_error_report, generate_report
from src.schemas import AnalysisOutput, Evidence, Finding, Hypothesis


def test_success_report_structure():
    """Test that successful analysis produces properly structured report."""
    analysis = AnalysisOutput(
        status="success",
        findings=[
            Finding(
                title="Test Finding",
                summary="A test finding",
                severity="medium",
                evidence=[
                    Evidence(
                        source_file="test.jsonl",
                        record_index=0,
                        event_id="4688",
                        excerpt="powershell.exe",
                    )
                ],
            )
        ],
        hypotheses=[Hypothesis(description="Test hypothesis", confidence=0.75)],
        indicators_of_compromise=["powershell.exe"],
        recommended_next_steps=["Investigate PowerShell usage"],
        confidence=0.8,
    )

    report = generate_report(analysis)

    assert "PURPLELENS AI SOC ASSISTANT" in report
    assert "Analysis Report" in report
    assert "## FINDINGS" in report
    assert "## HYPOTHESES" in report
    assert "## INDICATORS OF COMPROMISE" in report
    assert "## RECOMMENDED NEXT STEPS" in report
    assert "Overall Confidence: 0.80" in report

    assert "[MEDIUM] Test Finding" in report
    assert "Summary: A test finding" in report
    assert "test.jsonl:0 | event_id=4688 | powershell.exe" in report

    assert "Test hypothesis (confidence: 0.75)" in report
    assert "- powershell.exe" in report
    assert "- Investigate PowerShell usage" in report


def test_error_report_llm_error():
    """Test error report for LLM failure."""
    analysis = AnalysisOutput(
        status="llm_error",
        error_message="API connection failed",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    assert "Analysis Report — INCOMPLETE" in report
    assert "STATUS: llm_error" in report
    assert "API connection failed" in report
    assert "PARTIAL FINDINGS: 0 extracted before failure" in report
    assert "Check OpenAI API connectivity and credentials" in report
    assert "Review logs for additional details" in report


def test_error_report_timeout():
    """Test error report for timeout."""
    analysis = AnalysisOutput(
        status="timeout",
        error_message="LLM request timed out after 60s",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    assert "STATUS: timeout" in report
    assert "LLM request timed out after 60s" in report
    assert "Re-run analysis with fewer events or during lower load" in report


def test_error_report_validation_error():
    """Test error report for validation failure."""
    analysis = AnalysisOutput(
        status="validation_error",
        error_message="Schema violation detected",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    assert "STATUS: validation_error" in report
    assert "Schema violation detected" in report
    assert "Inspect LLM output logs for policy or schema violations" in report


def test_error_report_with_partial_findings():
    """Test error report that preserves partial findings."""
    analysis = AnalysisOutput(
        status="timeout",
        error_message="Timeout occurred",
        findings=[
            Finding(
                title="Partial Finding",
                summary="Found before timeout",
                severity="high",
                evidence=[
                    Evidence(
                        source_file="test.jsonl",
                        record_index=5,
                        event_id="4624",
                        excerpt="suspicious login",
                    )
                ],
            )
        ],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    assert "PARTIAL FINDINGS: 1 extracted before failure" in report
    assert "[HIGH] Partial Finding" in report
    assert "Found before timeout" in report
    assert "test.jsonl:5 | event_id=4624 | suspicious login" in report


def test_findings_sorted_by_severity():
    """Test that findings are sorted by severity (critical to info)."""
    analysis = AnalysisOutput(
        status="success",
        findings=[
            Finding(
                title="Low Finding",
                summary="Low severity",
                severity="low",
                evidence=[
                    Evidence(source_file="test.jsonl", record_index=0, excerpt="test")
                ],
            ),
            Finding(
                title="Critical Finding",
                summary="Critical severity",
                severity="critical",
                evidence=[
                    Evidence(source_file="test.jsonl", record_index=1, excerpt="test")
                ],
            ),
            Finding(
                title="Medium Finding",
                summary="Medium severity",
                severity="medium",
                evidence=[
                    Evidence(source_file="test.jsonl", record_index=2, excerpt="test")
                ],
            ),
        ],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.5,
    )

    report = generate_report(analysis)

    critical_pos = report.find("[CRITICAL] Critical Finding")
    medium_pos = report.find("[MEDIUM] Medium Finding")
    low_pos = report.find("[LOW] Low Finding")

    assert critical_pos < medium_pos < low_pos, "Findings not sorted by severity"


def test_empty_sections_handled():
    """Test that empty sections display '(none)'."""
    analysis = AnalysisOutput(
        status="success",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_report(analysis)

    assert report.count("(none)") == 5, "Empty sections not handled correctly"


def test_determinism():
    """Test that same input produces identical output (deterministic)."""
    analysis = AnalysisOutput(
        status="success",
        findings=[
            Finding(
                title="Test",
                summary="Test",
                severity="medium",
                evidence=[
                    Evidence(source_file="test.jsonl", record_index=0, excerpt="test")
                ],
            )
        ],
        hypotheses=[Hypothesis(description="Test", confidence=0.5)],
        indicators_of_compromise=["test.exe"],
        recommended_next_steps=["Test action"],
        confidence=0.75,
    )

    report1 = generate_report(analysis)
    report2 = generate_report(analysis)

    assert report1 == report2, "Report generation is not deterministic"


def test_confidence_formatting():
    """Test that confidence values are formatted to 2 decimal places."""
    analysis = AnalysisOutput(
        status="success",
        findings=[],
        hypotheses=[
            Hypothesis(description="Test 1", confidence=0.123456),
            Hypothesis(description="Test 2", confidence=0.987654),
        ],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.555555,
    )

    report = generate_report(analysis)

    assert "Overall Confidence: 0.56" in report
    assert "(confidence: 0.12)" in report
    assert "(confidence: 0.99)" in report


def test_banner_formatting():
    """Test that banner lines are 80 characters wide."""
    analysis = AnalysisOutput(
        status="success",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.5,
    )

    report = generate_report(analysis)

    lines = report.split("\n")
    banner_lines = [line for line in lines if line == "=" * 80]

    assert len(banner_lines) >= 2, "Not enough banner lines"


def test_evidence_multiple_items():
    """Test that multiple evidence items are listed correctly."""
    analysis = AnalysisOutput(
        status="success",
        findings=[
            Finding(
                title="Multi-Evidence Finding",
                summary="Finding with multiple evidence",
                severity="high",
                evidence=[
                    Evidence(
                        source_file="file1.jsonl",
                        record_index=0,
                        event_id="4688",
                        excerpt="cmd.exe",
                    ),
                    Evidence(
                        source_file="file1.jsonl",
                        record_index=5,
                        event_id="4688",
                        excerpt="powershell.exe",
                    ),
                    Evidence(
                        source_file="file2.jsonl",
                        record_index=10,
                        event_id="4624",
                        excerpt="login attempt",
                    ),
                ],
            )
        ],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.7,
    )

    report = generate_report(analysis)

    assert "file1.jsonl:0 | event_id=4688 | cmd.exe" in report
    assert "file1.jsonl:5 | event_id=4688 | powershell.exe" in report
    assert "file2.jsonl:10 | event_id=4624 | login attempt" in report


def test_no_llm_involvement():
    """Test that report generation does not involve LLM (deterministic Python)."""
    analysis = AnalysisOutput(
        status="success",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.5,
    )

    start = time.time()
    report = generate_report(analysis)
    duration = time.time() - start

    assert duration < 0.1, "Report generation took too long (possible network call)"
    assert isinstance(report, str)


def test_status_branch_logic():
    """Test that non-success status routes to error report."""
    for status in ["llm_error", "timeout", "validation_error"]:
        analysis = AnalysisOutput(
            status=status,
            error_message=f"Test {status}",
            findings=[],
            hypotheses=[],
            indicators_of_compromise=[],
            recommended_next_steps=[],
            confidence=0.0,
        )

        report = generate_report(analysis)

        assert "INCOMPLETE" in report, f"Status {status} should route to error report"
        assert f"STATUS: {status}" in report


def test_error_message_fallback():
    """Test that error report handles missing error_message."""
    analysis = AnalysisOutput(
        status="llm_error",
        error_message=None,
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    assert "LLM API call failed or returned invalid response" in report
