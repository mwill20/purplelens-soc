#!/usr/bin/env python3
"""Simple DB check for demo validation."""

import sqlite3
from pathlib import Path


def check_db():
    """Verify demo database content after running AWS CloudTrail analysis."""
    db_path = Path("db/analysis.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print(
            "Run an analysis first: python -m src.main --source aws --input data/aws_demo.jsonl"
        )
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("✅ Database found: db/analysis.db\n")

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Available tables: {', '.join(tables)}\n")

        # Count analysis runs
        cursor.execute("SELECT COUNT(*) FROM analysis_runs;")
        run_count = cursor.fetchone()[0]
        print(f"🔬 Analysis runs: {run_count}")

        # Get latest run info
        if run_count > 0:
            cursor.execute(
                """
                SELECT run_id, model_used, status,
                       datetime(timestamp, 'localtime') as run_time
                FROM analysis_runs 
                ORDER BY timestamp DESC 
                LIMIT 1;
            """
            )
            run_id, model, status, run_time = cursor.fetchone()
            print(f"  Latest run: {run_id[:8]}... | model={model} | status={status}")
            print(f"  Timestamp: {run_time}\n")

            # Count findings
            cursor.execute("SELECT COUNT(*) FROM findings;")
            finding_count = cursor.fetchone()[0]
            print(f"🔍 Total findings: {finding_count}")

            # Show recent findings
            if finding_count > 0:
                cursor.execute(
                    """
                    SELECT title, severity
                    FROM findings 
                    ORDER BY finding_id DESC 
                    LIMIT 5;
                """
                )
                findings = cursor.fetchall()
                print("  Recent findings:")
                for title, severity in findings:
                    print(f"    • {title} (severity: {severity})")
                print()

            # Count hypotheses
            cursor.execute("SELECT COUNT(*) FROM hypotheses;")
            hypo_count = cursor.fetchone()[0]
            print(f"💡 Hypotheses: {hypo_count}")

            # Count IOCs
            cursor.execute("SELECT COUNT(*) FROM indicators_of_compromise;")
            ioc_count = cursor.fetchone()[0]
            print(f"⚠️  Indicators of Compromise: {ioc_count}\n")

            print("✅ Demo verification complete!")

        conn.close()

    except Exception as e:
        print(f"❌ DB error: {e}")


if __name__ == "__main__":
    check_db()
