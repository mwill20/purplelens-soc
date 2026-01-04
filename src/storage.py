"""SQLite persistence layer for analysis runs and related artifacts."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.schemas import AnalysisOutput

_CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS analysis_runs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        input_files TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('success', 'partial', 'failed')),
        model_used TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS findings (
        finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('info', 'low', 'medium', 'high', 'critical')),
        evidence TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hypotheses (
        hypothesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        description TEXT NOT NULL,
        confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
        FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS indicators_of_compromise (
        ioc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        indicator TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        run_id TEXT PRIMARY KEY,
        report_text TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
    )
    """,
]


def initialize_database(db_path: str) -> None:
    """Ensure the SQLite database and schema exist."""

    conn = _get_connection(db_path)
    conn.close()


def save_analysis(
    db_path: str,
    run_id: str,
    analysis: AnalysisOutput,
    input_files: List[str],
    model_used: str,
    report_text: str,
    report_generated_at: datetime,
    run_timestamp: datetime | None = None,
) -> None:
    """Persist analysis outputs according to the architect-defined schema."""

    # Audit trail contract: every run is stored with metadata to reproduce outcomes.
    conn = _get_connection(db_path)
    try:
        with conn:
            _insert_analysis_run(
                conn, run_id, analysis, input_files, model_used, run_timestamp
            )
            _insert_findings(conn, run_id, analysis)
            _insert_hypotheses(conn, run_id, analysis)
            _insert_iocs(conn, run_id, analysis)
            _insert_report(conn, run_id, report_text, report_generated_at)
    finally:
        conn.close()


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection and ensure schema exists."""

    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    for statement in _CREATE_TABLE_STATEMENTS:
        conn.execute(statement)
    conn.commit()
    return conn


def _insert_analysis_run(
    conn: sqlite3.Connection,
    run_id: str,
    analysis: AnalysisOutput,
    input_files: List[str],
    model_used: str,
    run_timestamp: datetime | None,
) -> None:
    """Insert metadata for the analysis execution."""

    timestamp_source = run_timestamp or datetime.now(timezone.utc)
    timestamp = timestamp_source.isoformat()
    status_value = _derive_run_status(analysis)
    conn.execute(
        """
        INSERT INTO analysis_runs (run_id, timestamp, input_files, status, model_used)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, timestamp, json.dumps(input_files), status_value, model_used),
    )


def _insert_findings(
    conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput
) -> None:
    """Persist findings and their evidence arrays."""

    for finding in analysis.findings:
        evidence_json = json.dumps([ev.model_dump() for ev in finding.evidence])
        conn.execute(
            """
            INSERT INTO findings (run_id, title, summary, severity, evidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, finding.title, finding.summary, finding.severity, evidence_json),
        )


def _insert_hypotheses(
    conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput
) -> None:
    """Persist hypotheses collected from the analysis."""

    for hypothesis in analysis.hypotheses:
        conn.execute(
            """
            INSERT INTO hypotheses (run_id, description, confidence)
            VALUES (?, ?, ?)
            """,
            (run_id, hypothesis.description, hypothesis.confidence),
        )


def _insert_iocs(
    conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput
) -> None:
    """Persist indicators of compromise."""

    for indicator in analysis.indicators_of_compromise:
        conn.execute(
            """
            INSERT INTO indicators_of_compromise (run_id, indicator)
            VALUES (?, ?)
            """,
            (run_id, indicator),
        )


def _insert_report(
    conn: sqlite3.Connection,
    run_id: str,
    report_text: str,
    report_generated_at: datetime,
) -> None:
    """Persist the deterministic SOC report."""

    generated_at = report_generated_at
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)

    conn.execute(
        """
        INSERT INTO reports (run_id, report_text, generated_at)
        VALUES (?, ?, ?)
        """,
        (run_id, report_text, generated_at.isoformat()),
    )


def _derive_run_status(analysis: AnalysisOutput) -> str:
    """Map analyzer status into the storage status tri-state."""

    if analysis.status == "success":
        return "success"

    if analysis.findings or analysis.hypotheses or analysis.indicators_of_compromise:
        return "partial"

    return "failed"
