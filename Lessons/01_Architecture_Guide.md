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
Inputs -> Ingest -> Normalize -> Sanitize -> Enrich (GCP) -> LLM Analyze -> Validate Output -> Report -> Persist
```

- Inputs are log files (Windows, AWS, or GCP)
- Ingest normalizes each event into a consistent envelope
- Sanitize applies the prompt firewall (redact/quarantine flags) before any LLM calls
- Enrich adds deterministic signals for GCP
- LLM analysis produces structured findings
- Validation enforces schema + policy + semantic checks (optional judge)
- Reports/SQLite are written deterministically
- Ops harness records run logs/metrics per `run_id`

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
- Ops harness: `src/ops/*` (run logs, metrics, artifacts)
- Jailbreak harness: `scripts/jailbreak_harness.py` (optional replay)

## Normalized event envelope
All sources produce the same envelope for downstream stages:

```json
{
  "source_file": "Logs/windows_sample.jsonl",
  "record_index": 12,
  "event_id": "insertId-or-eventID",
  "raw_event": {
    "source": "gcp|aws_cloudtrail|windows",
    "event_time": "...",
    "action": "...",
    "actor": "...",
    "resource": "...",
    "plane": "control|data|telemetry|unknown",
    "...": "source-specific fields"
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
- Report: `reports/analysis_<run_id>.txt`
- SQLite DB: `db/analysis.db`
- Run log: `logs/run_<run_id>.log`
- Ops artifacts: `runs/<run_id>/run_log.jsonl`, `runs/<run_id>/metrics.json`

## Design notes
- Batch-first: logs are analyzed in batches, not as a streaming system.
- Source-specific prompts: Windows, AWS, and GCP have dedicated prompts.
- Prompt firewall: sanitize stage flags/quarantines injection-like input.
- Optional semantic judge: can be enabled with `--semantic-judge`.
- Deterministic output: reports and storage do not depend on UI or API layers.
- Ops-first: every run has run_id, logs, and metrics for auditability.

## When to change what
- Add new log format: modify the ingest phase.
- Improve LLM reasoning: adjust prompt templates and batching.
- Change output schema: update `src/schemas.py` and validation rules.
- Change report formatting: edit `src/report.py`.
