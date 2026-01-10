# Architecture

PurpleLens is a CLI-first security analysis pipeline that ingests log files
from Windows, AWS CloudTrail, and GCP Cloud Logging, runs LLM-driven analysis,
validates the result, and writes a deterministic report plus a SQLite record of
the run. The goal is demo-grade realism with clear, explainable phases.

## Goals
- Batch processing: file in, report out
- Multi-source: Windows, AWS, GCP
- Deterministic reporting and storage
- Simple CLI entrypoint for local or job execution

## Pipeline phases
1. Ingest and normalize
2. LLM analysis
3. Validate output
4. Generate report
5. Persist to SQLite

## Input and normalization
- Source auto-detection via `--source` (auto/windows/aws/gcp)
- Formats: JSONL per line, JSON arrays, AWS CloudTrail JSON, GCP Pub/Sub wrapper

Normalized event envelope:

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

## LLM analysis
- Providers: Gemini and OpenAI
- CLI flags: `--provider` and `--model` (default model is Gemini)
- Source-specific prompts for Windows, AWS, and GCP
- Batching to control prompt size and token cost
  - Windows: up to 50 events or ~24k characters per batch
  - AWS: 25 events per batch (config driven)
  - GCP: chunked processing for large log sets
- Up to three attempts per batch for reliability
- GCP adds deterministic IOC extraction on top of LLM output

## Validation and safety
- `src/schemas.py` defines the `AnalysisOutput` schema
- Evidence schema links findings back to original events
- `src/security.py` blocks unsafe patterns from appearing in outputs

Core output shape:

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

## Report generation
- `src/report.py` builds a deterministic text report
- Output path: `reports/analysis_<UTC timestamp>.txt`
- Sections: Executive Summary, Findings, Hypotheses, IOCs, Recommended Next Steps
- Errors are recorded when analysis or validation fails

## Storage
- SQLite at `db/analysis.db`
- Tables:
  - `analysis_runs`: run_id, timestamp, input_files, status, model_used
  - `findings`: run_id, title, summary, severity, evidence JSON
  - `hypotheses`: run_id, description, confidence
  - `indicators_of_compromise`: run_id, indicator
  - `reports`: run_id, report_text, generated_at
- Run status is derived from output presence (success, partial, failed)

## Observability
- Run logs: `logs/run_<run_id>.log`
- The run_id ties together logs, report, and database records
