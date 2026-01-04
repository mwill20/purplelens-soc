<div align="center">
  <img src="docs/PurpleLens-SOC-Logo.png" alt="PurpleLens SOC Logo" width="400"/>
</div>

# PurpleLens - AI-Assisted SOC Analysis with Deterministic Guardrails

> **Branch:** `enhancement/gcp-mini-lab` - Multi-source log analysis with AWS CloudTrail + GCP Audit Logs (Mini-Lab)  
> **Status:** AWS CloudTrail Enhancement Complete (Phases 0-4) | GCP Mini-Lab Complete (Phases 1-3, GCP prompt, enrichment, deterministic IOCs)  
> **Baseline:** Verified Windows EVTX functionality preserved

## Overview
- CLI-driven SOC assistant that ingests parsed Windows EVTX telemetry (JSONL), **AWS CloudTrail logs (JSON/JSONL, CSV supported via prep script)**, and **GCP Audit Logs (JSON/JSONL)**.
- Uses an LLM strictly as a structured extraction engine; **deterministic Python renders the SOC report and persists run metadata**.
- Guardrails enforce evidence-backed findings, policy-compliant narratives, and SQLite persistence for auditability.

### 🌍 The Big Picture: What Problem Are We Solving?
In plain English:
You're a SOC analyst drowning in event logs. You need to find suspicious activity, but:

- Reading raw .evtx files is painful (binary format)
- You have hundreds or thousands of events
- You need to explain what you found 
- You want to remember what you analyzed before

### What PurpleLens does:
It's like having a smart assistant that:

1. Converts messy binary logs into readable text
2. Reads through all the events looking for patterns
3. Writes a professional security report
4. Saves everything in a database so you can search later

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
3. Configure your OpenAI API key.
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your API key:
   # OPENAI_API_KEY=sk-proj-...
   ```
   
   **Note:** The `.env` file is gitignored and will not be committed to version control.

### Dataset Preparation (PowerShell)
1. Clone EVTX-ATTACK-SAMPLES.
   ```powershell
   git clone https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git
   ```
2. Copy 2–4 relevant `*.evtx` files into `data\evtx_raw\` (e.g., Execution, Credential Access, Lateral Movement).
3. Convert to JSONL.
   ```powershell
   .\scripts\prep_evtx.ps1 -InputPath ".\data\evtx_raw" -OutputPath ".\data\evtx_parsed"
   ```
4. Verify JSONL contents using any text viewer.

### Usage Examples

**Model Selection and JSON Output Compatibility**

PurpleLens relies on OpenAI models that support structured JSON output using the `response_format={"type": "json_object"}` parameter. For best results, use models like `gpt-4o`, `gpt-4-1106-preview`, or `gpt-3.5-turbo-1106`. Older models (e.g., `gpt-4`, `gpt-3.5-turbo`) do not support this parameter and will return an error. Always specify a compatible model using the `--model` argument:

```bash
python -m src.main --input data/evtx_parsed/ --model gpt-4o --output file
```

If you use an unsupported model, the tool will not generate a report and will return an API error. See OpenAI documentation for the latest list of supported models.
```bash
# Minimal run
python -m src.main --input data/evtx_parsed/

# Verbose logging
python -m src.main --input data/evtx_parsed/ --verbose

# Dry run (validation only)
python -m src.main --input data/evtx_parsed/ --dry-run

# Custom model and output to file
python -m src.main --input data/evtx_parsed/ --model gpt-4o --output file
```

## Data Sources
PurpleLens supports multiple log formats:
- **Windows EVTX** - Fully implemented and tested
- **AWS CloudTrail** - Fully implemented with plane tagging, correlation, and LLM batching
- **GCP Audit Logs (Mini-Lab)** - Ingestion + enrichment + GCP prompt + deterministic IOC extraction

### Source Detection
PurpleLens automatically detects log format based on:
1. File extension (`.evtx`, `.json`, `.jsonl`)
2. Content analysis (CloudTrail schema markers)
3. Directory contents (mixed directories require `--source` flag)

Use `--source aws|windows|gcp` to override auto-detection when needed.

**Important:** Each analysis run processes **one source type only** (Windows EVTX, AWS CloudTrail, or GCP Audit Logs). This design keeps different security contexts logically separated. If analyzing multiple sources, run PurpleLens separately per source.

### Dataset Information

**Windows EVTX:** Uses EVTX-ATTACK-SAMPLES dataset (included in repository)
- Located in `data/evtx_parsed/` and related directories
- Ready to use for immediate testing

**AWS CloudTrail:** Uses Kaggle Flaws CloudTrail dataset  
- **Sample data:** Small CloudTrail sample included at `data/sample_cloudtrail.csv` (50 records, 13KB)
- **Full dataset:** Download [AWS CloudTrails dataset from Flaws Cloud](https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud) 
- **File:** Save full dataset as `data/dec12_18features.csv` (830MB - excluded from git)
- **Usage:** Sample data sufficient for testing and development; full dataset for production analysis
- **Conversion:** CSV requires preprocessing via `scripts/aws_csv_to_jsonl.py`
- **Features:** Captures assumed roles, plane tagging, correlation clustering, security context
- **Security:** Raw CloudTrail records never stored in database; only normalized events + SHA256 hash

### AWS CloudTrail Usage

**Quick Start (Sample Data)**
```powershell
# Test with included sample (50 records)
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
python -m src.main --input data/sample_aws.jsonl --source aws
```

**Full Dataset Workflow**
```powershell
# 1. Download Kaggle dataset to data/dec12_18features.csv
# 2. Convert CSV to JSONL format
python scripts/aws_csv_to_jsonl.py data/dec12_18features.csv data/aws_cloudtrail.jsonl
# 3. Run analysis
python -m src.main --input data/aws_cloudtrail.jsonl --source aws
```

### AWS CloudTrail Capabilities
- **Plane tagging:** Conservative control/data/telemetry classification with unknown fallback
- **Correlation:** Proximity-based clustering with 5-minute time windows and deterministic IDs
- **LLM batching:** AWS-specific prompts with 25-event batches for token efficiency

### GCP Audit Logs Usage (Mini-Lab)

**Quick Start (Synthetic JSONL)**
```powershell
# Validate input only (no LLM calls) against the 3-event synthetic JSONL
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

**Quick Start (Mini-Lab Data)**
```powershell
# Validate input only (no LLM calls) against the consolidated mini-lab dataset
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --source gcp --dry-run

# Debug mode (prints one enrichment line per event)
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --source gcp --dry-run --debug
```

**Notes:**
- `--debug` sets log level to DEBUG (overrides `--verbose`/default).
- Evidence citations include `event_id` (insertId) for GCP runs.
- Enrichment debug lines are emitted by the GCP ingestion adapter.

**Mini-Lab Procedure (How the dataset was generated):**
- See [docs/GCP_LAB_PROCEDURE.md](docs/GCP_LAB_PROCEDURE.md)

---

## 🎯 AWS CloudTrail Demo

### Demo Data Policy

**Core Capabilities:**
- ✅ Tool supports AWS CloudTrail ingestion from JSON/JSONL; CSV requires prep script
- ✅ Raw CloudTrail is not stored in DB (hash + minimal replay fields only)
- ✅ LLM outputs JSON-only and is schema validated
- ✅ Findings require evidence (source_file + record_index)
- ✅ Tool never claims it executed remediation/actions

**Security Guardrails:**
- No raw CloudTrail stored (data minimization)
- Evidence-backed findings only (no speculation without provenance)
- Conservative plane tagging (unknown fallback, not definitive impact assessment)
- Proximity correlation only (cluster_id indicates timing, not causality)

### Dataset Limitations & Disclosure

**Source:** Kaggle "AWS CloudTrails dataset from Flaws Cloud" (training/CTF-derived)
**Data Type:** Training/CTF scenarios, not production exports

**Strengths:**
- Realistic IAM/STS authentication patterns
- Known attack scenarios with documented TTPs
- Consistent account structure for correlation testing
- Representative AWS service coverage for security events

**Weaknesses:**
- Limited service coverage (primarily IAM, S3, CloudTrail management)
- Artificial timing patterns (condensed attack timeline)
- Missing cross-account and organizational context
- Single-account scope (no multi-org federation scenarios)

**Claim Boundary:** "Demonstrates the harness and guardrails, not full production AWS coverage."

### Reproducible Demo Commands

**Step 1: Prep CSV → JSONL**
```powershell
# Convert sample data (50 records, quick demo)
python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/aws_demo.jsonl

# OR convert full dataset (if available locally)
python scripts/aws_csv_to_jsonl.py data/dec12_18features.csv data/aws_full.jsonl
```

**Step 2: Run Analysis**
```powershell
# Analyze with AWS-specific prompts and batching
python -m src.main --source aws --input data/aws_demo.jsonl

# Verbose mode (see plane tagging and correlation details)
python -m src.main --source aws --input data/aws_demo.jsonl --verbose

# Save to file instead of console
python -m src.main --source aws --input data/aws_demo.jsonl --output file
```

**What You Should See:**
- **Parsing:** `X events parsed, Y events skipped` (field validation)
- **Plane Counts:** `control: A, data: B, telemetry: C, unknown: D`
- **Cluster Counts:** `X correlation clusters created` (5-minute time windows)
- **LLM Batching:** `Processing N AWS batches with M total events`
- **Report:** Generated analysis with AWS-specific findings and hypotheses

**Step 3: Verify Database**
```powershell
# Use the provided verification script
python scripts/check_demo_db.py

# Expected output:
# - Tables: analysis_runs, findings, hypotheses, indicators_of_compromise, reports
# - Analysis run count
# - Recent findings with confidence scores
```

### Demo Subset Strategy (License-Safe)

**Approach:** Path A - No large data committed, local placement instructions

**For Interviews/Demos:**
1. Use included `data/sample_cloudtrail.csv` (50 records, 13KB) - minimal non-sensitive subset for demonstration
2. For full testing: Download Kaggle dataset to `data/dec12_18features.csv` (excluded from git, no redistribution)
3. All commands work with either sample or full dataset

**Expected Output Shape (Sample Data):**
- ~40-45 successfully parsed CloudTrail events
- ~2-4 plane categories detected
- ~8-12 correlation clusters (5-minute proximity windows)
- 2-3 LLM batches processed
- AWS-specific security findings with CloudTrail evidence

*Note: Exact numbers may vary due to LLM nondeterminism, but structure and guardrails remain consistent.*

---

## ✅ Acceptance Criteria (AWS Enhancement)

All of the following are verified:
- ✅ CSV to JSONL converter functional and tested
- ✅ CloudTrail JSONL ingests into normalized envelopes
- ✅ Provenance preserved (source_file + record_index)
- ✅ Plane tagging + proximity correlation applied
- ✅ LLM batching enforced with schema validation
- ✅ Raw CloudTrail never stored (data minimization)
- ✅ Windows EVTX workflow unchanged
- ✅ All tests passing (76/76)
- ✅ Documentation complete

**CLI Validation:**
```powershell
# Convert sample data
python scripts/aws_csv_to_jsonl.py data/dec12_18features.csv data/test.jsonl

# Test ingestion
python -m src.main --input data/test.jsonl --source aws --dry-run
# Expected: Normalized events created, provenance tracked, no raw storage
```

**SQLite Validation:**
- New normalized events present with source="aws_cloudtrail"
- Each event has source_file, record_index, raw_hash
- No raw CloudTrail records in database
- Windows EVTX data unchanged

### CloudTrail Data Security & Storage

**Never Stored (Security Risk):**
- `requestParameters` / `responseElements` - Contains API keys, passwords, user data, infrastructure secrets
- Full raw records - Preserves sensitive operational details and configuration data

**Never Stored (Storage Efficiency):**
- Raw events: 2-10KB each with 90% irrelevant nested metadata
- Massive redundancy across thousands of events from same environment

**Always Stored (Analysis Value):**
- Normalized security-relevant fields: actor, action, source, outcome, resources
- SHA256 hash: Verifies data integrity and enables deduplication without storing sensitive content
- Minimal replay fields: Event ID, region, timestamps for correlation

This approach supports incident response while maintaining data minimization and operational security.

### Known Limitations
- CLI only; GUI is a future enhancement.
- Requires pre-parsed JSONL EVTX files; raw EVTX parsing is out of scope.
- Windows telemetry focus and single-dataset demo (EVTX-ATTACK-SAMPLES subsets).
- Single OpenAI model call per run; no multi-turn reasoning.
- LLM outputs can still contain redundant summaries or overlapping recommendations; report post-processing mitigates but does not fully eliminate this.
- **This tool does not make determinations or take actions** - it provides structured evidence for analyst review.
- **Guardrail Coverage:** Structural validation via Pydantic schemas, pattern-based policy enforcement via `security.py`, semantic reasoning intentionally simplified for demo. See Security & Guardrails section in Demo Data Policy above.
- **AWS CloudTrail Dataset Anonymization:** The Kaggle CloudTrail dataset contains anonymized/truncated IP addresses (e.g., "255.253" instead of full IPs like "255.253.176.24"). This limits geolocation analysis but is typical for security training datasets that protect user privacy.

### Future Enhancements
1. Streamlit/GUI wrapper for analysts.
2. Multi-source log ingestion (Sysmon, firewall, cloud identity).
3. Streaming/real-time ingestion.
4. Provider-agnostic LLM abstraction and offline reasoning modes.
5. MITRE ATT&CK tagging within schemas and reports.
6. Select an AI Model tuned for analysis of security events or fine-tune a model.
7. **Semantic Guardrails:** Implement LLM-as-validator pattern (secondary model validates reasoning), rule-based security logic checker (validates findings align with known attack patterns), or confidence score calibration (validates confidence matches evidence strength).
8. **Event Caching:** Hash-based deduplication to avoid re-analyzing identical events across runs, reducing API costs and latency for repeated analysis workflows.
9. **Advanced Security Scanning:** Extend guardrails to detect PII/PHI leakage (SSNs, credit cards, health data in analyst notes), prompt injection attacks (direct: malicious prompts in event data; indirect: poisoned logs attempting LLM manipulation), and model safety violations (attempts to jailbreak model constraints or elicit harmful outputs). Note: As an internal SOC tool with controlled inputs (parsed telemetry), priority is lower than public-facing systems, but relevant for defense-in-depth against compromised log sources or insider threats.
10. **Production Database:** Replace SQLite with MySQL or PostgreSQL for multi-user environments, concurrent access, and enterprise-scale deployments requiring RBAC, replication, and performance optimization.
11. **Report De-duplication:** Improve semantic merging of findings and recommendations (e.g., similarity scoring or LLM-assisted clustering) to reduce overlap without losing detail.
12. **IOC Enrichment:** Add normalization and context for IOCs (e.g., SID resolution or hash metadata) to improve interpretability in reports.
13. **Analyst Determinations:** Add a post-run analyst decision record (analyst name, determination, notes, IR/customer notification flags, timestamp) linked to `run_id` for auditability and SLA tracking.

### Architecture

<div align="center">
   <img src="docs/PurpleLens_SOC_Architecture.svg" alt="PurpleLens Architecture Overview" width="900"/>
</div>

See the full architecture guide for details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
**GCP Mini-Lab Docs:**
- [docs/gcp/PHASE_1_IMPLEMENTATION.md](docs/gcp/PHASE_1_IMPLEMENTATION.md)
- [docs/gcp/PHASE_2_IMPLEMENTATION.md](docs/gcp/PHASE_2_IMPLEMENTATION.md)
- [docs/gcp/PHASE_3_IMPLEMENTATION.md](docs/gcp/PHASE_3_IMPLEMENTATION.md)

**GCP Mini-Lab Log Pack:**
- [data/gcp_log_pack/README.md](data/gcp_log_pack/README.md)

### Testing
```bash
python tests/test_phase1a.py
python tests/test_phase1b.py
python tests/test_phase1c.py
python tests/test_phase1d.py
python tests/test_full_flow.py  # mocked LLM, end-to-end
```

### Project Structure
```
src/
    __init__.py
    main.py
    ingest.py
    llm_analyze.py
    report.py
    storage.py
    schemas.py
    security.py
tests/
    __init__.py
    test_phase1a.py
    test_phase1b.py
    test_phase1c.py
    test_phase1d.py
    test_full_flow.py
scripts/prep_evtx.ps1
data/evtx_raw/        # selected EVTX files (from EVTX-ATTACK-SAMPLES)
data/evtx_parsed/     # JSONL output consumed by CLI
db/analysis.db        # created automatically
validation/           # overseer approvals
```

### License & Attribution

**License:** [MIT License](LICENSE) - Free to use for educational, portfolio, and commercial purposes.

**Third-Party Attributions:**
- **EVTX Dataset:** [sbousseaden/EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) - Sample Windows event logs for testing
- **AWS Dataset:** [Kaggle Flaws CloudTrail Dataset](https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud) - AWS CloudTrail logs for cloud security analysis
- **OpenAI API:** Requires valid API key and compliance with [OpenAI Terms of Service](https://openai.com/policies/terms-of-use)

### Development Notes (AWS CloudTrail Enhancement)

**Branch Safety:** 
- Baseline commit `2b25fc0d9af9b39dc5cf87a6ea18a13813409fe1` verified and tagged
- Windows EVTX workflow unchanged and fully functional
- Rollback procedures documented in `Fallback.md`

**Current Status:**
- **AWS CloudTrail Enhancement ✅:** CSV conversion, ingestion, plane tagging, correlation, LLM batching complete
- **Testing:** All tests passing (76/76) - 16 AWS-specific, 60 Windows baseline
- **Documentation:** Interview-ready with demo runbook and dataset limitations disclosure

**Purpose:** This project is designed for cybersecurity portfolio demonstration and technical interviews.
