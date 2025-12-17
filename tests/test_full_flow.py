"""Phase 1G integration test for full CLI execution."""

import os
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import main as cli_main


def run_full_flow() -> None:
    """Execute CLI pipeline end-to-end with a mocked LLM response."""

    dataset_dir = Path("data/evtx_parsed")
    assert dataset_dir.exists(), "Dataset directory missing; run Phase 1F first."

    mock_analysis = {
        "status": "success",
        "error_message": None,
        "findings": [
            {
                "title": "Mock Finding",
                "summary": "Simulated detection for integration test.",
                "severity": "medium",
                "evidence": [
                    {
                        "source_file": "data/evtx_parsed/Execution_wmic.jsonl",
                        "record_index": 0,
                        "event_id": "4688",
                        "excerpt": "powershell.exe -ExecutionPolicy Bypass",
                    }
                ],
            }
        ],
        "hypotheses": [
            {"description": "Potential credential abuse", "confidence": 0.55}
        ],
        "indicators_of_compromise": ["powershell.exe -ExecutionPolicy Bypass"],
        "recommended_next_steps": ["Review host PowerShell history"],
        "confidence": 0.67,
    }

    previous_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = previous_key or "test-key"

    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "integration.db"
        args = [
            "src.main",
            "--input",
            str(dataset_dir),
            "--db",
            str(db_path),
            "--model",
            "mock-model",
            "--output",
            "console",
        ]

        with patch("src.main.analyze_events", return_value=mock_analysis):
            with patch.object(sys, "argv", args):
                exit_code = cli_main.main()
                assert exit_code == 0, f"CLI exited with {exit_code}"

        _validate_database(db_path)

    if previous_key is None:
        del os.environ["OPENAI_API_KEY"]
    else:
        os.environ["OPENAI_API_KEY"] = previous_key

    print("✓ Phase 1G full-flow integration test passed")


def _validate_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analysis_runs")
    run_count = cursor.fetchone()[0]
    assert run_count == 1, "analysis_runs table should contain one entry"

    cursor.execute("SELECT status FROM analysis_runs")
    status = cursor.fetchone()[0]
    assert status == "success", f"analysis_runs status expected 'success', got {status}"

    cursor.execute("SELECT COUNT(*) FROM findings")
    finding_count = cursor.fetchone()[0]
    assert finding_count == 1, "findings table should contain one record"

    cursor.execute("SELECT COUNT(*) FROM reports")
    report_count = cursor.fetchone()[0]
    assert report_count == 1, "reports table should contain one record"

    conn.close()


if __name__ == "__main__":
    run_full_flow()
