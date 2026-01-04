"""Phase 1D validation tests for report generation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

    # Check for all required sections
    assert "PURPLELENS AI SOC ASSISTANT" in report
    assert "Analysis Report" in report
    assert "## FINDINGS" in report
    assert "## HYPOTHESES" in report
    assert "## INDICATORS OF COMPROMISE" in report
    assert "## RECOMMENDED NEXT STEPS" in report
    assert "Overall Confidence: 0.80" in report

    # Check for finding details
    assert "[MEDIUM] Test Finding" in report
    assert "Summary: A test finding" in report
    assert "test.jsonl:0 | event_id=4688 | powershell.exe" in report

    # Check for hypothesis details
    assert "Test hypothesis (confidence: 0.75)" in report

    # Check for IOCs and recommendations
    assert "- powershell.exe" in report
    assert "- Investigate PowerShell usage" in report

    print("✓ Success report structure works")


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

    print("✓ Error report for llm_error works")


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

    print("✓ Error report for timeout works")


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

    print("✓ Error report for validation_error works")


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

    print("✓ Error report with partial findings works")


def test_findings_sorted_by_severity():
    """Test that findings are sorted by severity (critical → info)."""
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

    # Check order: critical should appear before medium, medium before low
    critical_pos = report.find("[CRITICAL] Critical Finding")
    medium_pos = report.find("[MEDIUM] Medium Finding")
    low_pos = report.find("[LOW] Low Finding")

    assert critical_pos < medium_pos < low_pos, "Findings not sorted by severity"

    print("✓ Findings sorted by severity correctly")


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

    # Should have multiple (none) entries for empty sections
    assert report.count("(none)") == 5, "Empty sections not handled correctly"

    print("✓ Empty sections display '(none)' correctly")


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

    print("✓ Report generation is deterministic")


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

    # Check overall confidence formatting
    assert (
        "Overall Confidence: 0.56" in report
    ), "Overall confidence not formatted correctly"

    # Check hypothesis confidence formatting
    assert (
        "(confidence: 0.12)" in report
    ), "Hypothesis confidence not formatted correctly"
    assert (
        "(confidence: 0.99)" in report
    ), "Hypothesis confidence not formatted correctly"

    print("✓ Confidence formatting (2 decimal places) works")


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

    # Count banner lines (should be multiple lines of 80 '=' characters)
    lines = report.split("\n")
    banner_lines = [line for line in lines if line == "=" * 80]

    assert len(banner_lines) >= 2, "Not enough banner lines"

    print("✓ Banner formatting (80 chars) works")


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
    # This is a conceptual test - we verify the code only uses string formatting
    # No network calls, no API interactions, just Python string operations

    analysis = AnalysisOutput(
        status="success",
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.5,
    )

    # Generate report - should complete instantly without network calls
    import time

    start = time.time()
    report = generate_report(analysis)
    duration = time.time() - start

    # Should complete in milliseconds, not seconds (no network calls)
    assert duration < 0.1, "Report generation took too long (possible network call)"
    assert isinstance(report, str), "Report should be a string"

    print("✓ Report generation is deterministic (no LLM involvement)")


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

        # Should route to error report
        assert "INCOMPLETE" in report, f"Status {status} should route to error report"
        assert f"STATUS: {status}" in report

    print("✓ Non-success statuses route to error report")


def test_error_message_fallback():
    """Test that error report handles missing error_message."""
    analysis = AnalysisOutput(
        status="llm_error",
        error_message=None,  # No explicit error message
        findings=[],
        hypotheses=[],
        indicators_of_compromise=[],
        recommended_next_steps=[],
        confidence=0.0,
    )

    report = generate_error_report(analysis)

    # Should use status explanation as fallback
    assert "LLM API call failed or returned invalid response" in report

    print("✓ Error message fallback works")


def run_all_tests():
    """Run all Phase 1D validation tests."""
    tests = [
        test_success_report_structure,
        test_error_report_llm_error,
        test_error_report_timeout,
        test_error_report_validation_error,
        test_error_report_with_partial_findings,
        test_findings_sorted_by_severity,
        test_empty_sections_handled,
        test_determinism,
        test_confidence_formatting,
        test_banner_formatting,
        test_evidence_multiple_items,
        test_no_llm_involvement,
        test_status_branch_logic,
        test_error_message_fallback,
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("PHASE 1D VALIDATION TESTS")
    print("=" * 70)
    print()

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as exc:
            print(f"✗ {test_func.__name__} FAILED: {exc}")
            failed += 1
        except Exception as exc:
            print(f"✗ {test_func.__name__} ERROR: {exc}")
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
