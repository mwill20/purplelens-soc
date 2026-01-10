# Lesson 01 - Architecture Guide

This lesson explains how the current pipeline fits together and where each
phase lives in the codebase. The CLI is the entrypoint today, but the phases are
cleanly separated for future API or job execution.

## Objectives
- Understand the end-to-end data flow
- Learn the normalized event envelope
- Know where to look when modifying behavior

## Pipeline overview

```
Inputs -> Ingest + Normalize -> LLM Analysis -> Validate -> Report -> Store
```

- Inputs are log files (Windows, AWS, or GCP)
- Ingest normalizes each event into a consistent envelope
- LLM analysis produces structured findings
- Validation enforces the schema and safety checks
- Reports and SQLite records are written deterministically

## Code map
- CLI entry: `src/main.py`
- Ingest:
  - Windows: `src/ingest.py`
  - AWS: `src/ingest_aws.py` and `src/aws_plane_tagging.py`
  - GCP: `src/ingest_gcp.py` and `src/gcp_plane_tagging.py`
- LLM analysis: `src/llm_analyze.py`
- Validation schemas: `src/schemas.py`
- Safety checks: `src/security.py`
- Reporting: `src/report.py`
- Storage: `src/storage.py`

## Normalized event envelope
All sources produce the same envelope for downstream stages:

```json
{
  "source_file": "Logs/windows_sample.jsonl",
  "record_index": 12,
  "event_id": "optional",
  "raw_event": {
    "EventID": 4688,
    "CommandLine": "powershell -enc ...",
    "User": "LAB\\alice"
  }
}
```

Fields:
- `source_file`: input file path
- `record_index`: line or record number in the input file
- `event_id`: optional identifier (for example CloudTrail eventID or GCP insertId)
- `raw_event`: full source-specific payload

## CLI flow (current)
The CLI orchestrates all phases in one run:

```
python src/main.py --input Logs/sample.jsonl --source auto --provider gemini
```

Outputs:
- Report: `reports/analysis_<UTC timestamp>.txt`
- SQLite DB: `db/analysis.db`
- Run log: `logs/run_<run_id>.log`

## Design notes
- Batch-first: logs are analyzed in batches, not as a streaming system.
- Source-specific prompts: Windows, AWS, and GCP have dedicated prompts.
- Deterministic output: reports and storage do not depend on UI or API layers.

## When to change what
- Add new log format: modify the ingest phase.
- Improve LLM reasoning: adjust prompt templates and batching.
- Change output schema: update `src/schemas.py` and validation rules.
- Change report formatting: edit `src/report.py`.
