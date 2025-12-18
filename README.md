<div align="center">
  <img src="docs/PurpleLens-SOC-Logo.png" alt="PurpleLens SOC Logo" width="400"/>
</div>

# PurpleLens AI SOC Assistant

## Overview
- CLI-driven SOC assistant that ingests parsed Windows EVTX telemetry (JSONL).
- Uses a constrained LLM only for structured extraction; deterministic Python builds the SOC report.
- Guardrails enforce evidence-backed findings, policy-compliant narratives, and SQLite persistence for auditability.

### Installation
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

### Known Limitations
- CLI only; GUI is a future enhancement.
- Requires pre-parsed JSONL EVTX files; raw EVTX parsing is out of scope.
- Windows telemetry focus and single-dataset demo (EVTX-ATTACK-SAMPLES subsets).
- Single OpenAI model call per run; no automated remediation or determinations.

### Future Enhancements
1. Streamlit/GUI wrapper for analysts.
2. Multi-source log ingestion (Sysmon, firewall, cloud identity).
3. Streaming/real-time ingestion.
4. Provider-agnostic LLM abstraction and offline reasoning modes.
5. MITRE ATT&CK tagging within schemas and reports.

### Architecture

<div align="center">
  <img src="docs/architecture-overview.png" alt="PurpleLens Architecture Overview" width="900"/>
</div>

**Quick Overview:** Input JSONL is ingested with provenance (`source_file`, `record_index`). The tool batches events into a schema-defined LLM prompt, requesting structured JSON only. Pydantic validation and regex guardrails enforce policy compliance. Python renders a deterministic SOC report and persists run metadata to SQLite (`analysis_runs`, `findings`, `hypotheses`, `indicators_of_compromise`, `reports`). CLI remains the primary interface for predictable demos.

**Detailed Documentation:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for:
- Complete system architecture diagrams
- End-to-end data flow trace
- File responsibility matrix
- Error handling paths
- Architecture decision rationale

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
- **OpenAI API:** Requires valid API key and compliance with [OpenAI Terms of Service](https://openai.com/policies/terms-of-use)

**Purpose:** This project is designed for cybersecurity portfolio demonstration and technical interviews.
