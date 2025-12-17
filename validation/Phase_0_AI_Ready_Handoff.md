# Phase 0 AI-Ready Handoff Document
**For:** Principle Engineer AI  
**From:** Overseer AI  
**Date:** December 16, 2025  
**Status:** ✅ APPROVED — READY FOR IMPLEMENTATION

---

## Document Purpose

This document provides **zero-ambiguity specifications** for implementing the AI Security Analyst Assistant. All architectural decisions have been made. All schemas are defined. All failure modes are specified.

**Your job:** Implement exactly what is documented below. No guessing. No assumptions.

---

## 1. Project Overview

### What You Are Building:
A CLI-invoked Python tool that:
1. Ingests pre-parsed Windows EVTX events (JSON/JSONL)
2. Sends delimited events to an LLM for structured extraction
3. Validates output against strict schemas and security policies
4. Generates a deterministic SOC-style analyst report
5. Persists results to SQLite
6. Prints report to console

### Interface Design (Architect Lock):
**The CLI is the canonical interface for this assignment.**

**Rationale:**
- Deterministic execution
- Fast, reliable live demo
- Minimal attack surface
- Easier to explain under interview pressure

**Future Enhancement:**
A GUI wrapper (e.g., Streamlit) is a natural future extension and can be added without changing the core architecture. GUI is explicitly out-of-scope for Phase 1–2.

### What You Are NOT Building:
- Real-time monitoring
- Automated remediation
- Determination logic (benign/malicious)
- EVTX file parsing (expect pre-parsed JSON)
- Multi-agent orchestration
- GUI interface (future enhancement only)

---

## 2. Repository Structure (Implement Exactly)

```
bespin-ai-security-analyst/
├── main.py                 # CLI entrypoint + orchestration
├── ingest.py               # Load JSONL + attach provenance
├── llm_analyze.py          # LLM call + structured extraction
├── report.py               # Deterministic report formatting
├── storage.py              # SQLite persistence
├── schemas.py              # Pydantic models for validation
├── security.py             # Policy checks + prohibited patterns
├── data/
│   ├── evtx_raw/            # (Not used by tool, reference only)
│   └── evtx_parsed/         # Input: Pre-parsed JSONL files
├── db/
│   └── analysis.db          # SQLite database (auto-created)
├── scripts/
│   └── prep_evtx.ps1        # PowerShell: EVTX → JSONL (Phase 1)
├── requirements.txt
└── README.md
```

### File Responsibilities (One Per File):

| File | Responsibility | Key Functions |
|------|---------------|---------------|
| `main.py` | CLI + orchestration | `main()`, argparse setup |
| `ingest.py` | Load files, attach provenance | `load_events(path)` → list of events |
| `llm_analyze.py` | LLM call, handle errors | `analyze_events(events)` → structured output |
| `schemas.py` | Pydantic models | `AnalysisOutput`, `Finding`, `Evidence` |
| `security.py` | Policy validation | `validate_output(response)` → bool |
| `report.py` | Deterministic text generation | `generate_report(analysis)` → string |
| `storage.py` | SQLite CRUD | `save_analysis(run_id, data)` |

---

## 3. Data Flow (Implement Exactly)

```
1. main.py
   ├─ Parse CLI arguments
   ├─ Generate run_id (UUID)
   └─ Call ingest.load_events()

2. ingest.py
   ├─ Load JSON/JSONL files from --input path
   ├─ Attach provenance: {source_file, record_index, event_id, raw_event}
   ├─ On error: Log, exit code 1
   └─ Return: list[dict]

3. llm_analyze.py
   ├─ Format events with delimiters
   ├─ Call LLM (OpenAI API)
   ├─ On success: Parse JSON response
   ├─ On error: Set status="llm_error", return partial output
   └─ Return: dict (conforms to schema)

4. schemas.py
   ├─ Validate LLM response with Pydantic
   ├─ On validation error: Raise exception
   └─ Return: AnalysisOutput object

5. security.py
   ├─ Check for prohibited patterns
   ├─ On violation: Set status="validation_error"
   └─ Return: bool (pass/fail)

6. report.py
   ├─ Check analysis.status
   ├─ If success: Generate full report
   ├─ If partial: Generate degraded report with warnings
   └─ Return: string (report text)

7. storage.py
   ├─ Save to SQLite (analysis_runs, findings, hypotheses, reports)
   └─ Commit transaction

8. main.py
   ├─ Print report to console (or write to file if --output=file)
   └─ Exit with status code (0=success, 1=error)
```

---

## 4. LLM Output Schema (Pydantic Models)

### File: `schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Evidence(BaseModel):
    source_file: str = Field(..., description="Path to source file")
    record_index: int = Field(..., description="Record number in file")
    event_id: Optional[str] = Field(None, description="Event ID if applicable")
    excerpt: str = Field(..., description="Relevant excerpt from event")

class Finding(BaseModel):
    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    evidence: List[Evidence]

class Hypothesis(BaseModel):
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class AnalysisOutput(BaseModel):
    status: Literal["success", "validation_error", "llm_error", "timeout"]
    error_message: Optional[str] = None
    findings: List[Finding]
    hypotheses: List[Hypothesis]
    indicators_of_compromise: List[str]
    recommended_next_steps: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
```

### Why This Schema:
- **Provenance enforced**: Every evidence item has `source_file` + `record_index`
- **5-level severity**: SOC-standard (info, low, medium, high, critical)
- **Error handling**: `status` field enables graceful degradation
- **Validation**: Pydantic enforces structure; no free-form text

---

## 5. Security Policies (Implement Exactly)

### File: `security.py`

```python
import re
from typing import Tuple

# Prohibited patterns (reject if found in LLM response text)
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that"
]

def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate LLM output against security policies.
    
    Returns:
        (is_valid, error_message)
    """
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Prohibited pattern detected: {pattern}"
    
    return True, None
```

### Validation Strategy:
1. **Schema validation** (Pydantic) enforces structure
2. **Pattern matching** detects prohibited language
3. **Evidence presence** enforced via schema (not regex)

### On Policy Violation:
- Set `status="validation_error"`
- Log violation details
- Generate error report (do not use LLM output)

---

## 6. SQLite Schema (Implement Exactly)

### File: `storage.py`

#### Table Definitions:

```sql
-- Table: analysis_runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,              -- UUID
    timestamp TEXT NOT NULL,              -- ISO 8601 format
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
    generated_at TEXT NOT NULL,           -- ISO 8601 format
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);
```

#### Implementation Notes:
- Use `sqlite3` standard library
- Create tables on first run
- Use parameterized queries (prevent SQL injection)
- JSON arrays stored as TEXT (use `json.dumps()`)

---

## 7. CLI Specification (Implement Exactly)

### File: `main.py`

```python
import argparse
import uuid
from datetime import datetime

def parse_args():
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
    
    return parser.parse_args()

def main():
    args = parse_args()
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # TODO: Implement orchestration logic
    # 1. Load events (ingest.py)
    # 2. Analyze (llm_analyze.py) if not --dry-run
    # 3. Validate (schemas.py, security.py)
    # 4. Generate report (report.py)
    # 5. Save (storage.py)
    # 6. Print to console or file
    
    return 0  # Exit code

if __name__ == "__main__":
    exit(main())
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

---

## 8. Input Format Specification

### Expected Input:
Pre-parsed JSONL files in `data/evtx_parsed/`

### EVTX Preprocessing (Phase 1 Dataset Prep — NOT Tool Logic)

**Architect Lock:** EVTX → JSON/JSONL conversion is **out-of-scope** for the Python tool.

**What This Means:**
- Conversion is a **one-time dataset preparation step**
- The tool assumes input already exists in `data/evtx_parsed/*.jsonl`
- A PowerShell prep script will be provided in Phase 1 under `scripts/`

**Rationale:**
Keeps focus on AI security analysis, guardrails, and evidence handling; avoids platform-specific EVTX parsing complexity.

**Phase 1 Prep Script (PowerShell):**
```powershell
# scripts/prep_evtx.ps1
# Uses Get-WinEvent to stream EVTX → compact JSONL
# This script is NOT imported by the tool
# Details provided in Phase 1
```

### Format (JSONL):
```json
{"Event": {"System": {"EventID": 4688, "TimeCreated": "2024-01-15T10:30:00Z", "Computer": "WORKSTATION01"}, "EventData": {"ProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "CommandLine": "powershell.exe -NoProfile -ExecutionPolicy Bypass", "SubjectUserName": "admin"}}}
```

**Note:** One JSON object per line (JSONL format), not a JSON array.

### Provenance Attachment (in `ingest.py`):
For each event, attach:
```python
{
    "source_file": "data/evtx_parsed/execution_sample.jsonl",
    "record_index": 42,
    "event_id": "4688",
    "raw_event": {...}  # Original event dict
}
```

---

## 9. LLM Prompt Contract (NOT the actual prompt)

### Constraints:
- **Input:** Delimited events only
- **Output:** Valid JSON conforming to `AnalysisOutput` schema
- **Prohibited:** Action claims, determinations, ungrounded assertions

### Error Handling:
| Error Type | Status Code | Behavior |
|------------|-------------|----------|
| LLM timeout | `timeout` | Return partial output if available |
| API error | `llm_error` | Log error, set error_message field |
| Malformed JSON | `llm_error` | Log error, attempt to salvage |
| Schema violation | `validation_error` | Reject output, generate error report |
| Policy violation | `validation_error` | Reject output, log pattern |

---

## 10. Report Generation (Deterministic)

### File: `report.py`

```python
def generate_report(analysis: AnalysisOutput) -> str:
    """
    Generate SOC-style analyst report from structured analysis.
    
    Args:
        analysis: Validated AnalysisOutput object
    
    Returns:
        Formatted report string
    """
    
    # Check status
    if analysis.status != "success":
        return generate_error_report(analysis)
    
    # Build deterministic report
    sections = []
    
    # Header
    sections.append("=" * 80)
    sections.append("BESPIN AI SECURITY ANALYST ASSISTANT")
    sections.append("Analysis Report")
    sections.append("=" * 80)
    sections.append("")
    
    # Findings
    sections.append("## FINDINGS")
    for finding in analysis.findings:
        sections.append(f"### [{finding.severity.upper()}] {finding.title}")
        sections.append(f"Summary: {finding.summary}")
        sections.append("Evidence:")
        for ev in finding.evidence:
            sections.append(f"  - {ev.source_file}:{ev.record_index} | {ev.excerpt}")
        sections.append("")
    
    # Hypotheses
    sections.append("## HYPOTHESES")
    for hyp in analysis.hypotheses:
        sections.append(f"- {hyp.description} (confidence: {hyp.confidence:.2f})")
    sections.append("")
    
    # IOCs
    sections.append("## INDICATORS OF COMPROMISE")
    for ioc in analysis.indicators_of_compromise:
        sections.append(f"- {ioc}")
    sections.append("")
    
    # Recommendations
    sections.append("## RECOMMENDED NEXT STEPS")
    for step in analysis.recommended_next_steps:
        sections.append(f"- {step}")
    sections.append("")
    
    # Footer
    sections.append("=" * 80)
    sections.append(f"Overall Confidence: {analysis.confidence:.2f}")
    sections.append("=" * 80)
    
    return "\n".join(sections)

def generate_error_report(analysis: AnalysisOutput) -> str:
    """Generate degraded report for partial/failed analysis."""
    # TODO: Implement error report formatting
    pass
```

### Report Characteristics:
- **Human-readable**
- **Deterministic** (no LLM involvement)
- **SOC-appropriate tone**
- **Explicit uncertainty** (confidence scores)
- **No action claims**

---

## 11. Dependencies

### File: `requirements.txt`

```
openai>=1.0.0
pydantic>=2.0.0
```

### Notes:
- No EVTX parsing libraries needed (out-of-scope)
- Use `sqlite3` from standard library
- Python 3.10+ required (for type hints)

---

## 12. Code Quality Requirements

### Type Hints:
- **All functions must include type hints**
- Use Python 3.10+ syntax
- No `Any` types unless explicitly justified

### Error Handling:
- Wrap LLM calls in try/except
- Log all errors with context
- Return appropriate status codes

### Logging:
- Use `logging` module
- Log level controlled by `--verbose` flag
- Format: `[TIMESTAMP] [LEVEL] [MODULE] Message`

---

## 13. Testing Requirements (For Overseer Validation)

### Unit Tests:
- `test_schemas.py`: Schema validation
- `test_security.py`: Policy violation detection
- `test_ingest.py`: File loading + provenance

### Integration Tests:
- `test_full_flow.py`: End-to-end with mock LLM

### Negative Tests:
- Malformed JSON input
- Invalid severity values
- Prohibited patterns in LLM output

---

## 14. Exit Criteria (Definition of Done)

Your implementation is complete when:

- ☐ All 7 Python files implemented
- ☐ CLI accepts all specified arguments
- ☐ SQLite tables created correctly
- ☐ Pydantic models validate successfully
- ☐ Security policies enforced
- ☐ Reports generated deterministically
- ☐ Error handling works (no crashes)
- ☐ `--dry-run` validates inputs without LLM call
- ☐ All tests pass (unit + integration)

---

## 15. Implementation Order (Recommended)

1. **schemas.py** — Define Pydantic models first
2. **security.py** — Implement policy checks
3. **ingest.py** — File loading + provenance
4. **storage.py** — SQLite setup
5. **llm_analyze.py** — LLM call + error handling
6. **report.py** — Deterministic text generation
7. **main.py** — Orchestration + CLI

---

## 16. Known Constraints

### What NOT to Implement:
- EVTX file parsing (expect pre-parsed JSONL)
- Real-time monitoring
- Automated remediation
- Multi-agent orchestration
- GUI interface (future enhancement only)
- Complex CLI commands (keep it simple)

### What to Assume:
- OpenAI API key in environment variable `OPENAI_API_KEY`
- Pre-parsed JSONL files exist in `data/evtx_parsed/`
- SQLite database will be created if it doesn't exist
- Windows environment (PowerShell for dataset prep)

### CLI Design Philosophy (Architect Lock):
The CLI is intentionally **non-intimidating**:
- **Minimal commands:** Primary command + `--dry-run` for validation
- **Clear `--help`:** Self-documenting interface
- **Friendly errors:** Human-readable error messages
- **Deterministic output:** Same input = same output
- **Simple recovery:** Standard commands (`dir`, `python --version`)

**Target User:** SOC analyst comfortable with basic CLI, not DevOps engineer.

### Phase Gating Rule (Architect Lock):
**Do NOT advance phases automatically.**

Next phase begins **only after explicit user confirmation**:
```
"Phase X is complete. Proceed to Phase Y."
```

**Your responsibility:** After completing Phase 1, notify Overseer and wait for approval before Phase 2.

---

## 17. Handoff Checklist

Before you begin implementation:

- ☑ You have read this entire document
- ☑ You understand the data flow (section 3)
- ☑ You know the schema (section 4)
- ☑ You know the SQL tables (section 6)
- ☑ You know the CLI interface (section 7)
- ☑ You understand failure modes (section 9)

**If anything is unclear, STOP and request clarification from Overseer.**

---

## 18. Communication Protocol

### During Implementation:
- Implement one file at a time
- No assumptions or guesses
- If ambiguous: Ask Overseer for clarification

### After Implementation:
- Notify Overseer when complete
- Provide test results
- Report any blockers or issues

---

## 19. Architectural Summary (Architect Lock)

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

## Overseer Final Statement

This document contains **zero ambiguity**. Every decision has been made by the Architect. Every schema is defined. Every failure mode is specified.

**Your job is to code exactly what is written here.**

If you encounter a situation not covered in this document, stop and ask the Overseer. Do not guess.

**Phase Gating:** After completing implementation, notify Overseer and **wait for explicit approval** before proceeding to next phase.

---

**Phase 0 Complete. Phase 1 Approved. Begin Implementation.**

---

**Overseer AI**  
December 16, 2025  
**Updated:** December 17, 2025 (Architect clarifications added)
