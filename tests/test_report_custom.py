"""Test the new executive summary section."""

# Allow running from tests/ by adding parent dir to sys.path
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.report import generate_report
from src.schemas import AnalysisOutput

# Test Case 1: All critical (should be HIGH risk)
print("=" * 60)
print("TEST 1: All Critical Findings")
print("=" * 60)

critical_data = {
    "status": "success",
    "findings": [
        {
            "title": "Ransomware encryption detected",
            "summary": "Files encrypted by ransomware.",
            "severity": "critical",
            "evidence": [
                {
                    "source_file": "log1.jsonl",
                    "record_index": 0,
                    "event_id": "evt1",
                    "excerpt": "Suspicious encryption activity",
                }
            ],
            "id": "1",
        },
        {
            "title": "Data exfiltration to external IP",
            "summary": "Sensitive data sent to 8.8.8.8.",
            "severity": "critical",
            "evidence": [
                {
                    "source_file": "log2.jsonl",
                    "record_index": 5,
                    "event_id": "evt2",
                    "excerpt": "Data sent to 8.8.8.8",
                }
            ],
            "id": "2",
        },
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Isolate affected systems immediately"],
    "confidence": 0.95,
}

validated = AnalysisOutput.model_validate(critical_data)
report = generate_report(validated, event_count=20)
print(report[:500])  # Print first 500 chars to see summary
print("\n")

# Test Case 2: Mix of severities (should be HIGH risk - has criticals)
print("=" * 60)
print("TEST 2: Mixed Severities")
print("=" * 60)

mixed_data = {
    "status": "success",
    "findings": [
        {
            "title": "Privilege escalation",
            "summary": "User gained admin rights.",
            "severity": "critical",
            "evidence": [
                {
                    "source_file": "log3.jsonl",
                    "record_index": 2,
                    "event_id": "evt3",
                    "excerpt": "Admin rights granted",
                }
            ],
            "id": "1",
        },
        {
            "title": "Suspicious PowerShell",
            "summary": "Encoded command executed.",
            "severity": "high",
            "evidence": [
                {
                    "source_file": "log4.jsonl",
                    "record_index": 7,
                    "event_id": "evt4",
                    "excerpt": "Base64 PowerShell command",
                }
            ],
            "id": "2",
        },
        {
            "title": "Unusual login time",
            "summary": "Login at 3am.",
            "severity": "medium",
            "evidence": [
                {
                    "source_file": "log5.jsonl",
                    "record_index": 3,
                    "event_id": "evt5",
                    "excerpt": "Login at 3am",
                }
            ],
            "id": "3",
        },
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Review PowerShell logs"],
    "confidence": 0.85,
}

validated = AnalysisOutput.model_validate(mixed_data)
report = generate_report(validated, event_count=15)
print(report[:500])
print("\n")

# Test Case 3: Only low severity (should be MINIMAL risk)
print("=" * 60)
print("TEST 3: Only Low Severity")
print("=" * 60)

low_data = {
    "status": "success",
    "findings": [
        {
            "title": "Unusual process",
            "summary": "Process ran at odd time.",
            "severity": "low",
            "evidence": [
                {
                    "source_file": "log6.jsonl",
                    "record_index": 4,
                    "event_id": "evt6",
                    "excerpt": "Odd time process",
                }
            ],
            "id": "1",
        },
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Monitor process activity"],
    "confidence": 0.60,
}

validated = AnalysisOutput.model_validate(low_data)
report = generate_report(validated, event_count=5)
print(report[:500])
print("\n")

# Test Case 4: No findings (should be MINIMAL risk)
print("=" * 60)
print("TEST 4: No Findings (Clean)")
print("=" * 60)

clean_data = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["No action needed"],
    "confidence": 0.90,
}

validated = AnalysisOutput.model_validate(clean_data)
report = generate_report(validated, event_count=10)
print(report[:500])
print("\n")

print("✅ All tests completed! Check the risk levels above.")
