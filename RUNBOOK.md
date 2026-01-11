# RUNBOOK - PurpleLens AIOps V1

This runbook explains how to run PurpleLens, where to find artifacts, and how to debug failures.

---

## 1) How to run

PowerShell:
```powershell
python -m src.main --input data/evtx_parsed --dry-run
```

bash:
```bash
python -m src.main --input data/evtx_parsed --dry-run
```

After each run, artifacts are written to:
```
runs/<run_id>/
  run_log.jsonl
  metrics.json
  evidence.txt (if generated)
  what_broke.md (only on failure)
```

---

## 2) How to debug

### Find the latest run

PowerShell:
```powershell
$latest = Get-ChildItem runs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latest.FullName
```

bash:
```bash
ls -t runs | head -n 1
```

### Inspect logs

PowerShell:
```powershell
Get-Content runs/<run_id>/run_log.jsonl | Select-String "exception"
```

bash:
```bash
grep \"exception\" runs/<run_id>/run_log.jsonl
```

### Inspect metrics

```powershell
Get-Content runs/<run_id>/metrics.json
```

---

## 3) Known failures

- Missing API key: `OPENAI_API_KEY` or `GEMINI_API_KEY` not set.
- Malformed JSONL: invalid JSON line in input file.
- Schema mismatch (AWS/GCP): non-conforming log structure.
- Rate limit / LLM error: provider returns error on request.

---

## 4) What "good" looks like

Example log line (stage_end):
```json
{"ts":"2026-01-04T12:00:01Z","level":"INFO","run_id":"...","stage":"ingest","event":"stage_end","ok":true,"duration_ms":125,"source_type":"windows","records_out":15}
```

Example metrics snippet:
```json
{
  "run_id": "...",
  "total_duration_ms": 980,
  "ok": true,
  "error_count": 0,
  "files_processed": 3,
  "records_processed_total": 15
}
```

Note: token and cost fields are estimates. OpenAI models use a static pricing table; other providers report 0.0 unless configured.

---

## 5) Failure Drill #1

Good run:
```powershell
python -m src.main --input data/evtx_parsed --dry-run
```

Broken run:
```powershell
python -m src.main --input data/does_not_exist
```

Find evidence:
```powershell
Get-Content runs/<run_id>/run_log.jsonl | Select-String "exception"
Get-Content runs/<run_id>/what_broke.md
```
