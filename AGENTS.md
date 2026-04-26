# AGENTS.md

## Project Overview

ThreatPrism is an AI-assisted SOC analysis pipeline with deterministic guardrails, evidence-first reporting, and multi-source security log ingestion.

The project is CLI-first. It ingests Windows EVTX-derived JSONL, AWS CloudTrail, and GCP Audit Logs; normalizes events into a common envelope; sanitizes untrusted inputs; optionally calls an LLM for structured extraction; validates output through schemas and policy checks; renders deterministic reports; and persists run data to SQLite.

ThreatPrism assists SOC analysts. It does not execute response actions or autonomous remediation.

## Build And Run

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on bash:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run safe local ingestion validation without LLM calls:

```bash
python -m src.main --input data/evtx_sample --dry-run
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

Convert and validate the bundled AWS sample:

```bash
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws --dry-run
```

Model-backed analysis requires `GEMINI_API_KEY` or `OPENAI_API_KEY` in the environment or `.env`. Do not run model-backed analysis for routine validation.

## Safe Validation Commands

Use these commands for local validation:

```bash
python -m pytest
python -m compileall .
python -m src.main --input data/evtx_sample --dry-run
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

Avoid commands that require live OpenAI, Gemini, GCP, AWS, or secret credentials unless the user explicitly asks for them.

## Repository Rules

- Do not leave public-facing references to the previous project name or repository slug.
- Do not run external LLM or cloud calls during validation.
- Do not invent metrics, performance claims, production claims, or adoption claims.
- Preserve technical substance when editing docs: architecture, guardrails, evidence provenance, persistence, and observability details matter.
- Keep reports deterministic and evidence-first.
- Treat LLM output as untrusted until schema validation and policy checks pass.
- Do not edit resume files.
