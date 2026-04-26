# ThreatPrism SOC Demo Script and Runbook

Purpose: A concise, accurate demo guide for interviews and technical walkthroughs.  
Duration: 5-10 minutes  
Audience: Security engineers, cloud security leads, hiring managers

---

## Pre-Demo Checklist
- `.env` exists and contains `GEMINI_API_KEY` (default provider) or `OPENAI_API_KEY`.
- Dependencies installed: `pip install -r requirements.txt`.
- Datasets present:
  - Windows: `data/evtx_sample/` (JSONL demo set)
  - AWS sample: `data/sample_cloudtrail.csv`
  - GCP sample: `data/gcp_synthetic_minilab.jsonl`

Quick verification:
```powershell
# Windows (dry run, no LLM call)
python -m src.main --input data/evtx_sample --dry-run

# AWS (convert CSV to JSONL, then dry run)
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws --dry-run

# GCP (dry run)
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

---

## 5-Minute Demo Script

### 1) Opening (30 seconds)
What to say:
> "ThreatPrism is a guardrail-first SOC analysis pipeline. It ingests Windows, AWS, or GCP logs, normalizes them, uses an LLM only for structured extraction, and produces a deterministic report with evidence citations and SQLite persistence."

Key points:
- CLI-only, deterministic output.
- LLM is extraction-only (no actions, no remediation).
- Evidence provenance is mandatory.

### 2) Architecture (60 seconds)
Show: `docs/ARCHITECTURE.md` or the diagram in the README.

What to say:
> "The pipeline is linear: ingest, normalize, guardrails, LLM extraction, schema validation, deterministic report, persistence. AI is allowed only inside the extraction step. Everything else is Python and validated."

### 3) Choose a Run (2 minutes)
Pick one path depending on the audience.

Option A: Windows EVTX
```powershell
python -m src.main --input data/evtx_sample --model gemini-flash-latest
python -m src.main --input data/evtx_sample --provider openai --model gpt-4o
```

Option B: AWS CloudTrail
```powershell
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws --model gemini-flash-latest
python -m src.main --input data/sample_aws.jsonl --source aws --provider openai --model gpt-4o
```

Option C: GCP Audit Logs
```powershell
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --model gemini-flash-latest
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --provider openai --model gpt-4o
```

Callout:
> "OpenAI models must support `response_format={"type":"json_object"}`. Gemini models must support JSON output. The system fails closed if the model cannot return JSON."

### 4) Show the Report (60 seconds)
What to say:
> "Findings are severity-ordered, each includes evidence with source file and record index, and GCP includes event_id when present. The LLM does not write the report; Python renders it deterministically."

---

## Guardrails and Evidence (1-2 minutes)

Show policy guardrails:
```powershell
rg "PROHIBITED_PATTERNS" src/security.py
```

Show schema contract:
```powershell
rg "class Finding" src/schemas.py -n
```

Show persistence:
```powershell
python scripts/check_demo_db.py
```

What to say:
> "Schemas enforce structure, guardrails block unsafe claims, and persistence ensures auditability. Every claim must cite evidence from the original logs."

---

## Troubleshooting

API key missing:
- Symptom: `GEMINI_API_KEY environment variable not set` or `OPENAI_API_KEY environment variable not set`
- Fix: add the key to `.env`

Model incompatibility:
- Symptom: API error about unsupported model or response format
- Fix: use `gemini-flash-latest` or `--provider openai --model gpt-4o`

No events loaded:
- Symptom: "No JSONL files found" or "No supported files found"
- Fix: check input path and file extensions; for mixed directories, add `--source`

AWS CSV not ingested:
- Symptom: CloudTrail CSV rejected
- Fix: convert to JSONL with `scripts/aws_csv_to_jsonl.py`

---

## Quick Reference Commands
```powershell
# Windows EVTX
python -m src.main --input data/evtx_sample --model gemini-flash-latest
python -m src.main --input data/evtx_sample --provider openai --model gpt-4o

# AWS CloudTrail
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws --model gemini-flash-latest
python -m src.main --input data/sample_aws.jsonl --source aws --provider openai --model gpt-4o

# GCP Audit Logs
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --model gemini-flash-latest
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --provider openai --model gpt-4o

# Validation only (no LLM)
python -m src.main --input data/evtx_sample --dry-run
```

---

## Notes
- Emphasize constrained AI usage: extraction only, no actions.
- Highlight evidence provenance: every finding is traceable to the log artifact.
- Explain cloud-aware reasoning: plane tagging, identity focus, and log integrity.
- Stress deterministic reporting and schema enforcement as security controls.
