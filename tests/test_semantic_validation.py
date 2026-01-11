"""
Usage:
  pytest tests/test_semantic_validation.py

Purpose:
  Validate deterministic semantic checks for evidence mapping.
"""

from src.schemas import AnalysisOutput, Evidence, Finding
from src.security import validate_semantic_output


def test_semantic_validation_detects_event_id_mismatch() -> None:
    events = [
        {
            "source_file": "data/test.jsonl",
            "record_index": 0,
            "event_id": "evt-123",
            "raw_event": {"source": "gcp", "message": "test"},
        }
    ]

    evidence = Evidence(
        source_file="data/test.jsonl",
        record_index=0,
        event_id="evt-999",
        excerpt="mismatch",
    )
    finding = Finding(
        title="Mismatch",
        summary="Evidence event_id mismatch",
        severity="medium",
        evidence=[evidence],
    )
    analysis = AnalysisOutput(
        status="success",
        findings=[finding],
        confidence=0.5,
    )

    ok, issues = validate_semantic_output(analysis, events)

    assert ok is False
    assert any("mismatch" in issue for issue in issues)


def test_semantic_validation_detects_missing_reference() -> None:
    events = [
        {
            "source_file": "data/test.jsonl",
            "record_index": 1,
            "event_id": "evt-123",
            "raw_event": {"message": "test"},
        }
    ]

    evidence = Evidence(
        source_file="data/missing.jsonl",
        record_index=0,
        event_id="evt-000",
        excerpt="missing",
    )
    finding = Finding(
        title="Missing",
        summary="Evidence points to missing event",
        severity="low",
        evidence=[evidence],
    )
    analysis = AnalysisOutput(
        status="success",
        findings=[finding],
        confidence=0.5,
    )

    ok, issues = validate_semantic_output(analysis, events)

    assert ok is False
    assert any("missing source reference" in issue for issue in issues)
