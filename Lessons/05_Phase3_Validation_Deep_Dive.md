# Lesson 05 - Phase 3: Validation Deep Dive

Validation ensures that LLM outputs are safe and conform to the expected
schema. It is the boundary between probabilistic analysis and deterministic
reporting.

## Objectives
- Understand the `AnalysisOutput` schema
- Learn how evidence is linked to raw events
- See how validation protects downstream steps

## Core schema (`src/schemas.py`)

```json
{
  "status": "success",
  "findings": [
    {
      "title": "Suspicious PowerShell Execution",
      "summary": "Encoded command lines indicate possible staging.",
      "severity": "high",
      "evidence": [
        {
          "source_file": "Logs/windows_sample.jsonl",
          "record_index": 12,
          "event_id": "optional",
          "excerpt": "powershell -enc ..."
        }
      ]
    }
  ],
  "hypotheses": [
    {
      "description": "Initial staging via PowerShell.",
      "confidence": 0.62
    }
  ],
  "indicators_of_compromise": [
    "powershell -enc"
  ],
  "recommended_next_steps": [
    "Isolate the host and review parent process tree."
  ],
  "confidence": 0.58
}
```

Notes:
- `status` is one of `success`, `partial`, or `failed`.
- `Finding.summary` is required (not `description`).
- `Finding.evidence` is required and may reference an optional `event_id`.
- `Hypothesis.confidence` is per-hypothesis, while `confidence` is overall.

## Safety checks
`src/security.py` blocks unsafe patterns from being included in final output.
This keeps the report safe and demo-friendly.

## Exercises
1. Add a new validation rule that limits the maximum length of any excerpt.
2. Add a required field to the schema and propagate it to report generation.
