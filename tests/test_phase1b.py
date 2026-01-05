"""
Usage:
  pytest tests/test_phase1b.py

Purpose:
  Validate EVTX JSONL ingestion and SQLite persistence.

Limitations:
  - Uses temporary files and a temporary SQLite database.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ingest import load_events
from src.schemas import AnalysisOutput, Evidence, Finding, Hypothesis
from src.storage import initialize_database, save_analysis


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _create_evtx_dir(base_dir: Path) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)

    valid_file = base_dir / "valid.jsonl"
    _write_jsonl(
        valid_file,
        [
            json.dumps(
                {
                    "Event": {
                        "System": {"EventID": 4688},
                        "EventData": {"ProcessName": "powershell.exe"},
                    }
                }
            ),
            json.dumps(
                {"Event": {"System": {"EventID": 4624}, "EventData": {"LogonType": 3}}}
            ),
        ],
    )

    malformed_file = base_dir / "malformed.jsonl"
    _write_jsonl(
        malformed_file,
        [
            json.dumps({"Event": {"System": {"EventID": 1}}}),
            "{this is not valid json}",
            json.dumps({"Event": {"System": {"EventID": 2}}}),
        ],
    )

    return base_dir


def test_load_events_with_malformed_lines(tmp_path: Path) -> None:
    data_dir = _create_evtx_dir(tmp_path / "evtx")
    events = load_events(str(data_dir))
    assert len(events) == 4


def test_event_id_extraction(tmp_path: Path) -> None:
    data_dir = _create_evtx_dir(tmp_path / "evtx")
    events = load_events(str(data_dir))
    event_ids = [e["event_id"] for e in events]
    assert "4688" in event_ids
    assert "4624" in event_ids


def test_load_events_empty_dir_raises(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError):
        load_events(str(empty_dir))


def test_initialize_database_creates_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "test_phase1b.db"
    initialize_database(str(db_path))

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "analysis_runs" in tables
    assert "findings" in tables
    assert "hypotheses" in tables
    assert "indicators_of_compromise" in tables
    assert "reports" in tables


def test_save_analysis_persists_records(tmp_path: Path) -> None:
    db_path = tmp_path / "test_phase1b.db"
    initialize_database(str(db_path))

    run_id = "test-run-123"
    evidence = Evidence(
        source_file="test.jsonl",
        record_index=0,
        event_id="4688",
        excerpt="powershell.exe -ExecutionPolicy Bypass",
    )
    finding = Finding(
        title="Suspicious PowerShell",
        summary="PowerShell with bypass flag detected",
        severity="high",
        evidence=[evidence],
    )
    hypothesis = Hypothesis(description="Possible reconnaissance activity", confidence=0.72)
    analysis = AnalysisOutput(
        status="success",
        findings=[finding],
        hypotheses=[hypothesis],
        indicators_of_compromise=["powershell.exe -ExecutionPolicy Bypass"],
        recommended_next_steps=["Investigate command history"],
        confidence=0.75,
    )

    save_analysis(
        db_path=str(db_path),
        run_id=run_id,
        analysis=analysis,
        input_files=["test.jsonl"],
        model_used="gpt-4o",
        report_text="Test report content",
        report_generated_at=datetime.now(timezone.utc),
    )

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM analysis_runs WHERE run_id = ?", (run_id,))
    assert cursor.fetchone()[0] == "success"

    cursor.execute("SELECT COUNT(*) FROM findings WHERE run_id = ?", (run_id,))
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM hypotheses WHERE run_id = ?", (run_id,))
    assert cursor.fetchone()[0] == 1

    cursor.execute(
        "SELECT COUNT(*) FROM indicators_of_compromise WHERE run_id = ?", (run_id,)
    )
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM reports WHERE run_id = ?", (run_id,))
    assert cursor.fetchone()[0] == 1

    conn.close()


def test_status_mapping(tmp_path: Path) -> None:
    db_path = tmp_path / "status.db"
    initialize_database(str(db_path))

    save_analysis(
        str(db_path),
        "test-success",
        AnalysisOutput(status="success", confidence=0.8),
        ["test.jsonl"],
        "gpt-4o",
        "report",
        datetime.now(timezone.utc),
    )

    finding = Finding(
        title="Test",
        summary="Test",
        severity="high",
        evidence=[Evidence(source_file="test.jsonl", record_index=0, excerpt="test")],
    )
    save_analysis(
        str(db_path),
        "test-partial",
        AnalysisOutput(status="llm_error", findings=[finding], confidence=0.5),
        ["test.jsonl"],
        "gpt-4o",
        "report",
        datetime.now(timezone.utc),
    )

    save_analysis(
        str(db_path),
        "test-failed",
        AnalysisOutput(status="timeout", confidence=0.0),
        ["test.jsonl"],
        "gpt-4o",
        "report",
        datetime.now(timezone.utc),
    )

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM analysis_runs WHERE run_id = ?", ("test-success",))
    assert cursor.fetchone()[0] == "success"
    cursor.execute("SELECT status FROM analysis_runs WHERE run_id = ?", ("test-partial",))
    assert cursor.fetchone()[0] == "partial"
    cursor.execute("SELECT status FROM analysis_runs WHERE run_id = ?", ("test-failed",))
    assert cursor.fetchone()[0] == "failed"
    conn.close()
