# Complete Demo Runbook (Interview Panel)

Purpose: a single, repeatable walkthrough that starts from GitHub clone and ends with a clean demo of Windows, AWS, and GCP analysis plus a brief code tour.

Gemini quick-switch (PowerShell):
```powershell
$provider = "gemini"
$model = "gemini-flash-latest"
# or:
# $provider = "openai"
# $model = "gpt-4o"
```
Use in commands:
```powershell
python -m src.main --input data/evtx_sample --provider $provider --model $model
```

Target time: 12-15 minutes demo + 5-10 minutes Q&A.

---

## 0) Starting Point (Clone + Setup)

### Clone the repo
```powershell
git clone https://github.com/mwill20/purplelens-soc.git
cd purplelens-soc
```

### Verify Python
```powershell
python --version
```
If Python is not found:
```powershell
py -3 --version
```

### Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```
If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Install dependencies
```powershell
pip install -r requirements.txt
```

### Set up your API key
```powershell
Copy-Item .env.example .env
notepad .env
```
Add your key(s):
```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```
You can keep both and choose with `--provider`.

Quick sanity check:
```powershell
python -m src.main --help
```

---

## 1) Preflight Data Check (No surprises)

### Windows sample (15 events total)
```powershell
Get-ChildItem data\evtx_sample\*.jsonl | ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    Write-Host "$($_.Name): $lines events"
}
```
Expected counts:
- Credential_hashdump.jsonl: 2
- Execution_wmic.jsonl: 8
- Lateral_wmic.jsonl: 5

### Raw EVTX sample (binary)
`data/evtx_raw/Execution_wmic.evtx` is included for the raw vs JSONL contrast.

### AWS sample
`data/sample_cloudtrail.csv` should exist.

### GCP sample
`data/gcp_synthetic_minilab.jsonl` should exist.

---

## 2) Demo Flow (Run in this order)

### A0) Quick EVTX contrast (raw vs JSONL)

Use this to show the pain point before the live run.

Raw EVTX (binary, unreadable). Uses the bundled sample in `data\evtx_raw\`:
```powershell
Get-Content data\evtx_raw\Execution_wmic.evtx -TotalCount 1
```

Readable JSONL for the same event source (choose one):
```powershell
# If you converted EVTX locally:
Get-Content data\evtx_parsed\Execution_wmic.jsonl -TotalCount 1 |
  ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }

# If you only have the repo sample:
Get-Content data\evtx_sample\Execution_wmic.jsonl -TotalCount 1 |
  ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }
```

### A) Windows run (primary demo)
```powershell
# Gemini (default)
python -m src.main --input data/evtx_sample --verbose --model gemini-flash-latest

# OpenAI (optional)
python -m src.main --input data/evtx_sample --provider openai --model gpt-4o
```

What to look for in output:
- `Detected source type: windows`
- A report printed to console
- `Report written to reports/analysis_<UUID>.txt`

Open the latest report:
```powershell
$latest = Get-ChildItem reports\analysis_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName
```

What to point out:
- Executive Summary
- Findings (each includes `source_file`, `record_index`, `event_id`)
- Hypotheses and recommended next steps

### B) AWS run (CloudTrail)
Convert the sample CSV to JSONL (one-time):
```powershell
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
```
Run the analysis:
```powershell
# Gemini (default)
python -m src.main --input data/sample_aws.jsonl --source aws --verbose --model gemini-flash-latest

# OpenAI (optional)
python -m src.main --input data/sample_aws.jsonl --source aws --provider openai --model gpt-4o
```

What to point out:
- Source-specific adapter
- Plane tagging (control/data/telemetry) used as context
- Correlation by time proximity (deterministic IDs)

### C) GCP run (Audit Logs)
```powershell
# Gemini (default)
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --verbose --model gemini-flash-latest

# OpenAI (optional)
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --provider openai --model gpt-4o
```

What to point out:
- GCP normalization into the same evidence envelope
- Deterministic enrichment: actor type, automation hints, workload identity
- Evidence uses `insertId` for provenance

---

## 3) If You Don't Want to Call the API

Use `--dry-run` for validation only:
```powershell
python -m src.main --input data/evtx_sample --dry-run
python -m src.main --input data/sample_aws.jsonl --source aws --dry-run
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

Expected output:
`Validation successful. Loaded 15 events from ...`

---

## 4) Database Proof (Audit Trail)

After any real run:
```powershell
python scripts/check_demo_db.py
```

What to point out:
- Run ID, model, status
- Findings count and recent entries

---

## 5) 90-Second Code Tour (Order Matters)

Open each file and say one line:

1) `src/main.py`
- Orchestrator: detect source, ingest, analyze, validate, report, persist.

2) `src/ingest.py`
- Provenance envelope: `source_file`, `record_index`, `event_id`.

3) `src/ingest_aws.py` + `src/aws_plane_tagging.py`
- CloudTrail normalization + plane tags (control/data/telemetry).

4) `src/ingest_gcp.py` + `src/gcp_plane_tagging.py` + `src/gcp_enrichment.py`
- GCP normalization + plane tags + deterministic actor/automation signals.

5) `src/schemas.py`
- Schema contract that the LLM must follow.

6) `src/llm_analyze.py`
- Strict prompt + batching + retries.

7) `src/security.py`
- Policy guardrails against action claims and unsafe patterns.

8) `src/report.py`
- Deterministic reporting (no LLM narrative).

9) `src/storage.py`
- SQLite audit trail for runs, findings, hypotheses, IOCs.

---

## 6) Cloud Planes (Use This Explanation)

Keep it intuitive and conservative:

- **Control plane** = identity and configuration changes that can alter security posture  
  (IAM, KMS, logging sinks, org policy).
- **Telemetry plane** = visibility and monitoring data  
  (CloudWatch, Logging read/write, Monitoring).
- **Data plane** = access to user data  
  (S3 object access, GCS object access).

Why it matters:
Control plane changes have high blast radius.  
Telemetry changes can blind detection.  
Data plane changes indicate possible exfil or access.

In PurpleLens:
- Plane tagging is deterministic and conservative.
- Used as context, not proof of malicious intent.

---

## 7) Guardrails (One-Sentence Summary)

The LLM is extraction-only: it must output JSON that matches the schema, evidence is required for every claim, policy rules block action or certainty language, and Python renders the report deterministically.

---

## 8) Common Errors (Fix Fast)

- **OPENAI_API_KEY not set**: add it to `.env` or use `--dry-run`.
- **GEMINI_API_KEY not set**: add it to `.env` or switch to OpenAI.
- **Gemini model not found**: use `gemini-flash-latest` (the `models/` prefix is optional).
- **No report file**: look for `Report written to ...` in output.
- **Activation blocked**: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Wrong input type**: add `--source aws` or `--source gcp`.

---

## 9) Final Close (30 seconds)

"PurpleLens is a constrained, evidence-first SOC analysis pipeline.  
It normalizes logs, applies guardrails, uses AI only for structured extraction,  
then produces a deterministic report with provenance and an audit trail."

---

## Quick Command Cheat Sheet

```powershell
# Windows run (demo)
python -m src.main --input data/evtx_sample --verbose --model gemini-flash-latest
python -m src.main --input data/evtx_sample --provider openai --model gpt-4o

# AWS run
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws --verbose --model gemini-flash-latest
python -m src.main --input data/sample_aws.jsonl --source aws --provider openai --model gpt-4o

# GCP run
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --verbose --model gemini-flash-latest
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --provider openai --model gpt-4o

# Dry run (no API)
python -m src.main --input data/evtx_sample --dry-run

# DB check
python scripts/check_demo_db.py
```
