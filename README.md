<div align="center">
  <img src="docs/PurpleLens-SOC-Logo.png" alt="PurpleLens SOC Logo" width="400"/>
</div>

# PurpleLens - AI-Assisted SOC Analysis with Deterministic Guardrails

## Overview
PurpleLens is a CLI SOC analysis system that ingests Windows EVTX, AWS CloudTrail logs, and GCP Audit Logs, normalizes them into a consistent event envelope, attaches provenance, uses a constrained LLM to extract structured intelligence. Every claim is evidence-backed, validated against schemas and policy guardrails, and rendered into a deterministic report that is stored in SQLite for auditability.

This is not a chatbot or an automated responder. It is a guardrail-first analysis pipeline designed to make cloud and host security and telemetry review faster while preserving defensibility.

## Installation
1. Clone the repo and enter it.
   ```bash
   git clone https://github.com/mwill20/purplelens-soc.git
   cd purplelens-soc
   ```
2. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your API key (OpenAI or Gemini).
   ```powershell
   Copy-Item .env.example .env
   # Edit .env and add:
   # OPENAI_API_KEY=sk-...
   # GEMINI_API_KEY=AIza...
   ```
   ```bash
   cp .env.example .env
   ```

## Dataset Preparation (Windows EVTX)
PurpleLens expects EVTX to be pre-parsed into JSONL.
The repo includes a small Windows sample set at `data/evtx_sample/` for demos.

1. Clone EVTX-ATTACK-SAMPLES.
   ```powershell
   git clone https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git
   ```
2. Copy a small set of `.evtx` files into `data\evtx_raw\`.
3. Convert to JSONL.
   ```powershell
   .\scripts\prep_evtx.ps1 -InputPath ".\data\evtx_raw" -OutputPath ".\data\evtx_parsed"
   ```

## Usage
Minimal run:
```bash
python -m src.main --input data/evtx_sample
```

Verbose logging:
```bash
python -m src.main --input data/evtx_sample --verbose
```

Validation only (no LLM calls):
```bash
python -m src.main --input data/evtx_sample --dry-run
```

Write report to file (always saved in `reports/` regardless):
```bash
python -m src.main --input data/evtx_sample --output file
```

Model compatibility:
- OpenAI: requires `response_format={"type":"json_object"}` support (for example `gpt-4o`).
- Gemini: use a JSON-capable model (for example `gemini-flash-latest`).

## LLM Providers
Gemini is the default. To use OpenAI, set `OPENAI_API_KEY` and pass `--provider openai`.

Gemini (default):
```bash
python -m src.main --input data/evtx_sample --model gemini-flash-latest
```

OpenAI:
```bash
python -m src.main --input data/evtx_sample --provider openai --model gpt-4o
```

## Data Sources and Detection
PurpleLens supports three source types and processes one type per run:
- Windows EVTX (JSONL)
- AWS CloudTrail (JSON/JSONL; CSV via prep script)
- GCP Audit Logs (JSON/JSONL)

Auto-detection uses file extension, schema markers, and `gcp_` filename prefixes. Mixed directories require `--source`.
```bash
python -m src.main --input data/sample_aws.jsonl --source aws
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp
```

## AWS CloudTrail
### Dataset and Prep
Sample data is included in the repo at `data/sample_cloudtrail.csv`.
```powershell
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws
```

### Analysis Behavior
- Plane tagging: conservative control/data/telemetry classification.
- Correlation: proximity-based clustering with deterministic IDs.
- Prompt batching: cluster-aware batches for token efficiency.

### Data Minimization
Raw CloudTrail records are never stored in the database. Only normalized fields and a SHA256 hash are persisted for security purposes and storage efficiency.

## GCP Audit Logs
### Inputs
The repo includes:
- `data/gcp_synthetic_minilab.jsonl` (small synthetic set, used for initial setup and testing only)
- `data/gcp_log_pack/minilab_ground_truth_complete.json` (created from purpose built live GCP project)

### Quick Start
```powershell
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --source gcp --dry-run
```

### GCP Enrichment
GCP ingestion adds deterministic signals:
- Actor type (human vs service account)
- Automation tool hints from user agent
- Workload identity detection
- Cross-project heuristics

Debug output for enrichment:
```powershell
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --debug
```

## Guardrails and Validation
- All LLM inputs and outputs are treated as untrusted. 
- Schema enforcement: Pydantic models define the LLM contract.
- Policy guardrails: regex checks block action claims and unsafe patterns.
- Deterministic reporting: Python renders the report; the LLM does not.
- Untrusted input handling: prompts instruct the model to ignore log-embedded instructions.

## Evidence and Provenance
Every finding must cite:
- `source_file`
- `record_index`
- `event_id` (GCP uses `insertId`)

This enables audit-ready, replayable analysis without relying on model memory or inference.

## Output and Persistence
- Reports are saved to `reports/analysis_<UUID>.txt`.
- SQLite database at `db/analysis.db` stores run metadata, findings, hypotheses, IOCs, and report text.

## Architecture
The pipeline is intentionally linear and deterministic:
```
Source -> Ingest -> Normalize -> Guardrails -> AI Extraction -> Validation -> Report -> Persist
```
<div align="center">
   <img src="docs/PurpleLens_SOC_Architecture.png" alt="PurpleLens Architecture Overview" width="900"/>
</div>

See the full architecture guide for details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Testing
Tests are organized by phase and feature area.
```bash
pytest tests/
pytest tests/test_phase1a.py
pytest tests/test_full_flow.py
```

AWS and GCP-specific tests are under `tests/`.

## Project Structure
```
src/
    main.py             # CLI orchestration
    ingest.py           # EVTX ingestion
    ingest_aws.py        # AWS CloudTrail ingestion
    ingest_gcp.py        # GCP Audit Log ingestion
    llm_analyze.py       # LLM extraction + batching
    schemas.py           # Pydantic contracts
    security.py          # Policy guardrails
    report.py            # Deterministic report rendering
    storage.py           # SQLite persistence
scripts/
    prep_evtx.ps1        # EVTX -> JSONL converter
    aws_csv_to_jsonl.py  # CloudTrail CSV converter
    check_demo_db.py     # DB verification helper
    export_gcp_logs.ps1  # GCP Audit Logs export (PowerShell)
    export_gcp_logs.sh   # GCP Audit Logs export (bash)
    append_exposure.py   # Demo data helper
    verify_gcp_enrichment.py
    README.md

data/
    evtx_sample/         # Small JSONL demo set for Windows
    evtx_parsed/         # Local JSONL outputs (optional)
    sample_cloudtrail.csv
    gcp_synthetic_minilab.jsonl
    gcp_log_pack/
```

## Known Weaknesses and Constraints
- CLI-only; no GUI.
- One source type per run (no mixed-source correlation).
- Windows EVTX must be pre-parsed into JSONL; binary EVTX parsing is out of scope.
- AWS CloudTrail CSV requires preprocessing; only JSON/JSONL is ingested directly.
- GCP and AWS plane tagging is heuristic and conservative; unknown is a valid outcome.
- LLM output is non-deterministic; reports are deterministic but extraction quality depends on the model and input quality.
- **This tool does not make determinations or take actions** - it provides structured evidence for analyst review.
- **AWS CloudTrail Dataset Anonymization:** The Kaggle CloudTrail dataset contains anonymized/truncated IP addresses (e.g., "255.253" instead of full IPs like "255.253.176.24"). This limits geolocation analysis but is typical for security training datasets that protect user privacy.
- Raw CloudTrail records and sensitive request/response payloads are intentionally not stored.
- Models that do not support `response_format` will fail.

## Future Enhancements
- Streamlit or web UI for analyst workflows.
- Multi-source correlation across Windows, AWS, and GCP in a single run.
- Streaming ingestion for near-real-time analysis.
- Provider-agnostic LLM adapter with offline/fallback modes.
- MITRE ATT&CK tagging in schemas and reports.
- Secondary validator model for semantic guardrails.
- IOC enrichment and normalization (e.g., SID resolution, hash metadata).
- Event caching and deduplication to reduce repeated analysis cost.
- Report de-duplication via semantic merging to reduce overlap.
- Production database (PostgreSQL/MySQL) for multi-user environments and RBAC.
- Analyst determination records linked to `run_id` for auditability.
- Expanded security scanning for PII/PHI, prompt injection signals, and safety violations.


## License and Attribution
- License: MIT (`LICENSE`)
- EVTX dataset: https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- AWS dataset: https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud
- OpenAI or Gemini API required for LLM extraction

## Documentation
Additional guides and runbooks live in `docs/`:
- `docs/ARCHITECTURE.md`
- `docs/DEMO_SCRIPT.md`
- `docs/TROUBLESHOOTING.md`
