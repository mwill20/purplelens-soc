# Phase 0 — System Boundaries, Repo Structure, Schemas

## Phase 0 Goal (what "done" means)

By the end of Phase 0, you should be able to:

- **Point to a clean repo layout** and explain why it's shaped this way
- **Show the schemas** that govern LLM behavior before calling a model
- **Explain the full data flow** end-to-end in under 60 seconds
- **Hand Phase 1 to an IDE** and say "build exactly this"

**No code correctness yet. Only architectural correctness.**

---

## 1. System Boundaries (Final Lock)

### In scope (re-affirmed)

- **CLI-invoked Python tool** (canonical interface)
- Local file ingestion
- Parsed Windows EVTX events (JSONL)
- One LLM call for structured extraction
- Deterministic report generation
- SQLite persistence
- Console output

### Explicitly out of scope

- GUI interface (future enhancement only)
- Streaming ingestion
- Real-time SOC integration
- Automated remediation
- Determinations (benign/malicious)
- Multi-agent orchestration
- EVTX file parsing (pre-step, not tool logic)

### Interface Design (Architect Lock)

**The CLI is the canonical interface for this assignment.**

**Rationale:**
- Deterministic execution
- Fast, reliable live demo
- Minimal attack surface
- Easier to explain under interview pressure
- Non-intimidating for SOC analysts

**Future Enhancement:** GUI wrapper (e.g., Streamlit) can be added without changing core architecture.

> This exactly matches the assignment's intent to assess rapid, well-reasoned implementation rather than production scope.

---

## 2. Canonical Repo Structure (Lock This)

This is the minimal, interview-safe layout. Nothing extra.

```
bespin-ai-security-analyst/
├── main.py                 # CLI entrypoint
├── ingest.py               # Load JSONL + attach provenance
├── llm_analyze.py          # LLM call + structured extraction
├── report.py               # Deterministic report formatting
├── storage.py              # SQLite persistence
├── schemas.py              # Pydantic / JSON schemas
├── security.py             # Guardrails + policy checks
├── data/
│   ├── evtx_raw/            # Selected raw EVTX files (2–4)
│   └── evtx_parsed/         # Parsed JSONL events
├── db/
│   └── analysis.db
├── scripts/
│   └── prep_evtx.ps1        # PowerShell: EVTX → JSONL (Phase 1)
├── requirements.txt
└── README.md
```

### Why this structure works

- **One file per responsibility** (easy to explain)
- **Clear trust boundary** between raw input → parsed → analyzed
- **No hidden "magic" folders**
- **Matches rubric sections 3–7 one-to-one**

> **If a file doesn't map to a rubric requirement, it doesn't belong.**

---

## 3. Data Flow (Mental Model You'll Explain)

This is the flow you should be able to draw on a whiteboard:

### Input
**EVTX files** (pre-parsed JSON/JSONL, untrusted)

### Ingestion (`ingest.py`)
- Load parsed JSON/JSONL
- Attach provenance (file, record index)
- **On failure:** Log error, exit with status code 1

### Extraction (`llm_analyze.py`)
- Send delimited events to LLM
- Receive JSON only
- **On failure (timeout, API error):** Set status="llm_error", continue with partial output

### Validation (`schemas.py`, `security.py`)
- Schema validation (Pydantic)
- Policy checks (prohibited patterns)
- **On rejection:** Set status="validation_error", log violation

### Report (`report.py`)
- Deterministic text generation
- SOC-style sections
- Handle partial results (check status field)
- **On failure:** Print to stderr, exit with status code 1

### Persist + Print (`storage.py`, `main.py`)
- Save results to SQLite
- Print single report to console
- Exit with appropriate status code (0=success, 1=error)

> This directly satisfies Core Requirements 1–4.

---

## 4. Schema Design (Critical Phase-0 Artifact)

This is the **contract with the LLM**. Nothing moves forward without this.

### Structured Output Schema (conceptual)

```json
{
  "status": "success | validation_error | llm_error | timeout",
  "error_message": "string | null",
  "findings": [
    {
      "title": "string",
      "summary": "string",
      "severity": "info | low | medium | high | critical",
      "evidence": [
        {
          "source_file": "string",
          "record_index": 0,
          "event_id": "string | null",
          "excerpt": "string"
        }
      ]
    }
  ],
  "hypotheses": [
    {
      "description": "string",
      "confidence": 0.0
    }
  ],
  "indicators_of_compromise": ["string"],
  "recommended_next_steps": ["string"],
  "confidence": 0.0
}
```

### Why this schema is right

- **Forces evidence-backed claims** with structured provenance (source_file, record_index, event_id)
- **Prevents free-form hallucinated prose**
- **Easy to validate with Pydantic**
- **Maps directly to SOC thinking** (5-level severity scale)
- **Resilient to failures** (status + error_message enable graceful degradation)
- **Enforceable** (schema validation removes ambiguity)

> This enforces your "LLM = extractor, Python = narrator" rule from the North Star.

---

## 5. EVTX Preprocessing (Pre-Tool Requirement)

**EVTX → JSONL conversion is OUT OF SCOPE for the Python tool.**

### Architect Lock:
- **Conversion is a one-time dataset preparation step**
- The tool assumes input already exists in `data/evtx_parsed/*.jsonl`
- A **PowerShell prep script** will be provided in Phase 1 under `scripts/`

### Assumption:
The tool expects **pre-parsed JSONL files** in `data/evtx_parsed/`.

### Expected Input Format (JSONL):
```json
{"Event": {"System": {"EventID": 4688, "TimeCreated": "2024-01-15T10:30:00Z"}, "EventData": {"ProcessName": "powershell.exe", "CommandLine": "..."}}}
```
**Note:** One JSON object per line (JSONL format), not a JSON array.

### Phase 1 Prep Script (PowerShell):
```powershell
# scripts/prep_evtx.ps1
# Uses Get-WinEvent to stream EVTX → compact JSONL
# This script is NOT imported by the tool
# Details provided in Phase 1
```

### Rationale:
This assignment tests AI + security reasoning, not Windows EVTX parsing. Keeping conversion out-of-scope preserves the North Star: "clear, safe, boring in the right ways."

### Environment Requirement:
All dataset prep commands and scripts must be **PowerShell compatible** (Windows environment).

---

## 6. LLM Prompt Contract (Phase-0 Definition)

We are **not writing the prompt yet**, but we define its constraints now:

### Input:
- Delimited events only
- No instructions from data

### Output:
- Valid JSON
- Must conform to schema
- No claims of action
- No determinations

**If the model violates this, the system rejects output.**

> This addresses GenAI Skill + Security Acumen evaluation criteria.

---

## 7. Security Policy Specification (`security.py`)

### Prohibited Output Patterns (reject if found in LLM response):
```python
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that"
]
```

### Validation Strategy:
- **Schema validation** (Pydantic) enforces structure
- **Pattern matching** detects prohibited language
- **Evidence presence** enforced via schema (not regex)

### On Policy Violation:
- Set `status="validation_error"`
- Log violation details
- Generate error report (no LLM output used)

---

## 8. SQLite Schema Definition (`storage.py`)

### Table Definitions:

```sql
-- Table: analysis_runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,              -- UUID
    timestamp TEXT NOT NULL,              -- ISO 8601
    input_files TEXT NOT NULL,            -- JSON array of file paths
    status TEXT NOT NULL,                 -- success | partial | failed
    model_used TEXT                       -- e.g., "gpt-4"
);

-- Table: findings
CREATE TABLE IF NOT EXISTS findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('info', 'low', 'medium', 'high', 'critical')),
    evidence TEXT NOT NULL,               -- JSON array
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);

-- Table: hypotheses
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);

-- Table: indicators_of_compromise
CREATE TABLE IF NOT EXISTS indicators_of_compromise (
    ioc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    indicator TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);

-- Table: reports
CREATE TABLE IF NOT EXISTS reports (
    run_id TEXT PRIMARY KEY,
    report_text TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);
```

### Why This Schema:
- **Auditability:** Every run tracked with UUID
- **Referential integrity:** Foreign keys enforce consistency
- **Reproducibility:** Can replay analysis from stored data
- **Constraints:** CHECKs prevent invalid data

---

## 9. Commands We Will Use (Defined, Not Run)

These are planned, not executed yet.

### Full CLI Specification:

```python
# main.py argparse interface

import argparse

parser = argparse.ArgumentParser(
    description="Bespin AI Security Analyst Assistant"
)

# Required arguments
parser.add_argument(
    "--input",
    required=True,
    help="Path to directory containing parsed EVTX JSON files"
)

# Optional arguments
parser.add_argument(
    "--output",
    choices=["console", "file"],
    default="console",
    help="Output destination (default: console)"
)

parser.add_argument(
    "--model",
    default="gpt-4",
    help="OpenAI model to use (default: gpt-4)"
)

parser.add_argument(
    "--db",
    default="db/analysis.db",
    help="Path to SQLite database (default: db/analysis.db)"
)

parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose logging"
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Validate inputs only, do not call LLM"
)
```

### Example Commands:

```bash
# Minimal execution
python main.py --input data/evtx_parsed/

# With options
python main.py --input data/evtx_parsed/ --output file --verbose

# Dry run (validation only, no LLM call)
python main.py --input data/evtx_parsed/ --dry-run

# Custom model and database
python main.py --input data/evtx_parsed/ --model gpt-4-turbo --db custom.db
```

**No ambiguity about how the tool runs.**

---

## 10. Phase 0 Exit Checklist (Must All Be True)

Before moving to Phase 1:

- ☑ Repo structure agreed and created
- ☑ Dataset choice locked (EVTX-ATTACK-SAMPLES)
- ☑ Data flow explainable end-to-end (with failure paths)
- ☑ Output schema defined (with provenance + error handling)
- ☑ LLM role constrained
- ☑ No action/determination paths exist
- ☑ SQLite schema defined
- ☑ CLI specification complete
- ☑ Security policies enumerated
- ☑ EVTX preprocessing approach locked (out-of-scope, PowerShell prep)
- ☑ CLI vs GUI decision locked (CLI canonical, GUI future)
- ☑ Phase gating rule established

**All boxes checked. Phase 1 approved.**

---

## 11. CLI Design Philosophy (Architect Lock)

The CLI is intentionally **non-intimidating**:

- **Minimal commands:** Primary command + `--dry-run` for validation
- **Clear `--help`:** Self-documenting interface
- **Friendly errors:** Human-readable error messages
- **Deterministic output:** Same input = same output
- **Simple recovery:** Standard commands (`dir`, `python --version`)

**Target User:** SOC analyst comfortable with basic CLI, not DevOps engineer.

---

## 12. Phase Gating Rule (Architect Lock)

**Do NOT advance phases automatically.**

Next phase begins **only after explicit user confirmation**:
```
"Phase X is complete. Proceed to Phase Y."
```

**Overseer responsibility:** After completing each phase, notify Architect and wait for approval.

---

## ## 13. Architectural Summary (Architect Lock)

The system is intentionally layered:

1. **Dataset preparation (EVTX parsing)** is a pre-step, not tool logic
2. **The CLI is the canonical execution interface** (deterministic, demo-friendly)
3. **The analysis engine remains deterministic, safe, and interview-ready**
4. **GUI support is a future usability enhancement**, not a core dependency

This architecture ensures:
- **Clear separation of concerns** (prep vs. analysis)
- **Minimal attack surface** (CLI only)
- **Interview readiness** (can explain any component in 30 seconds)
- **Extensibility** (can add GUI, streaming, multi-source later)

---

## 14. Architect Teaching Moment (why Phase 0 matters)

Most candidates jump straight to:
- Parsing logs
- Calling an LLM
- Printing text

**You didn't.**

You defined:
- **Contracts**
- **Boundaries**
- **Failure modes**
- **Interface philosophy**
- **Phase discipline**

**That's why this project will sound senior even if the code is small.**
