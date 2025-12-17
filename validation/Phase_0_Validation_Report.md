# Phase 0 Validation Report
**Date:** December 16, 2025  
**Phase:** Phase 0 — System Boundaries, Repo Structure, Schemas  
**Status:** ⚠️ REQUIRES ENHANCEMENTS BEFORE HANDOFF

---

## Executive Summary

Phase 0 specification has been reviewed against:
- North Star document
- Rubric requirements (sections 1-12)
- Known security constraints
- AI-to-AI handoff clarity

**Result:** Phase 0 is architecturally sound but requires **enhancements and clarifications** before handoff to principle engineer.

---

## ✅ What Is Correct

### 1. System Boundaries
- **In/Out scope is accurate** and matches North Star
- Correctly excludes real-time, remediation, determinations
- Aligns with interview constraints

### 2. Repo Structure
- **File naming is clear and maps 1:1 to responsibilities**
- No hidden magic folders
- Rubric-aligned structure

### 3. Schema Design
- **Forces evidence-backed claims** ✅
- Prevents hallucinated prose ✅
- Pydantic-validatable ✅

### 4. LLM Constraints
- **Extraction-only role** is clear
- Output format constrained to JSON
- No action/determination paths

---

## ⚠️ Gaps & Inconsistencies (Must Fix Before Phase 1)

### **GAP 1: Missing Provenance Schema**
**Location:** Section 4 (Schema Design)  
**Issue:** Schema includes `evidence: ["string"]` but does not enforce provenance metadata.

**Current Schema:**
```json
"evidence": ["string"]
```

**Required Schema Enhancement:**
```json
"evidence": [
  {
    "source_file": "string",
    "event_id": "string | null",
    "record_index": "int",
    "excerpt": "string"
  }
]
```

**Why This Matters:**
- Rubric Section 6 requires evidence referencing "specific artifact identifiers or line numbers"
- Without structured provenance, evidence becomes unverifiable

**Fix Required:** ✅ Update schema in Phase 0 doc  
**Principle Engineer Impact:** Must implement provenance tracking in `ingest.py`

---

### **GAP 2: Missing Severity Enum Values**
**Location:** Section 4 (Schema Design)  
**Issue:** Severity is defined as `"low | medium | high"` but lacks "info" or "critical" levels commonly used in SOC operations.

**Current:**
```json
"severity": "low | medium | high"
```

**Recommendation:**
```json
"severity": "info | low | medium | high | critical"
```

**Why This Matters:**
- SOC analysts expect 5-level severity scales
- "Info" is needed for benign/contextual findings
- "Critical" is needed for high-confidence adversarial indicators

**Fix Required:** ⚠️ Architect decision needed (keep 3-level or expand to 5-level)  
**Principle Engineer Impact:** Validation logic in `schemas.py`

---

### **GAP 3: Missing Error Handling Schema**
**Location:** Section 4 (Schema Design)  
**Issue:** No schema defined for LLM failure cases (malformed JSON, schema violations, timeout).

**Required Addition:**
```json
{
  "status": "success | validation_error | llm_error | timeout",
  "error_message": "string | null",
  "findings": [...],
  ...
}
```

**Why This Matters:**
- Principle engineer needs explicit guidance on failure modes
- Report generation (`report.py`) must handle partial/failed outputs
- Rubric Section 11 requires "Output validation"

**Fix Required:** ✅ Add error handling schema  
**Principle Engineer Impact:** Must implement error paths in `llm_analyze.py` and `report.py`

---

### **GAP 4: Data Flow Missing Failure Paths**
**Location:** Section 3 (Data Flow)  
**Issue:** Data flow diagram only shows "happy path" — no failure/rejection flows.

**Current Flow:**
```
Input → Ingestion → Extraction → Validation → Report → Persist
```

**Enhanced Flow (Required):**
```
Input
  ↓
Ingestion (ingest.py)
  ├─ SUCCESS → Extraction (llm_analyze.py)
  └─ FAIL → Log error, exit with status 1

Extraction (llm_analyze.py)
  ├─ SUCCESS → Validation (schemas.py)
  └─ FAIL → Log error, generate partial report

Validation (schemas.py, security.py)
  ├─ PASS → Report (report.py)
  └─ REJECT → Log violation, generate error report

Report (report.py)
  ├─ SUCCESS → Persist + Print
  └─ FAIL → Log error, print to stderr
```

**Fix Required:** ✅ Update data flow with failure paths  
**Principle Engineer Impact:** Must implement exit codes and error reporting

---

### **GAP 5: Missing Dataset Preprocessing Specification**
**Location:** Section 1 (System Boundaries) and Section 3 (Data Flow)  
**Issue:** Phase 0 says "Parsed Windows EVTX events (JSON/JSONL)" but does not specify:
- How EVTX → JSON conversion happens
- What tool/library to use (`python-evtx`, `evtx2json`, manual?)
- Where parsed files will be stored (`data/evtx_parsed/`)

**Required Clarification:**
```
EVTX Processing (Pre-Phase 1):
1. Use python-evtx library OR manual conversion
2. Store parsed JSON in data/evtx_parsed/
3. Expected format: 
   [
     {
       "Event": { "System": {...}, "EventData": {...} },
       "EventID": 4624,
       "TimeCreated": "..."
     }
   ]
```

**Why This Matters:**
- Principle engineer needs exact input format expectations
- `ingest.py` cannot be implemented without this

**Fix Required:** ✅ Add preprocessing specification  
**Principle Engineer Impact:** Must implement EVTX parsing OR expect pre-parsed files

---

### **GAP 6: Missing Security Policy Specification**
**Location:** Section 5 (LLM Prompt Contract)  
**Issue:** "Policy checks" mentioned in data flow but no concrete policies defined.

**Required Policy Definitions:**
```python
# security.py policy checks (to be implemented)
PROHIBITED_OUTPUT_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed)",
    r"System (modified|updated|patched)"
]

REQUIRED_OUTPUT_PATTERNS = [
    r"Evidence:",
    r"Hypothesis:",
    r"Recommendation:"
]

CONFIDENCE_THRESHOLD = 0.0  # Accept all confidences but flag <0.3 as "low"
```

**Fix Required:** ✅ Add policy specification to Phase 0  
**Principle Engineer Impact:** Must implement `security.py` validation functions

---

### **GAP 7: Missing Storage Schema (SQLite Tables)**
**Location:** Section 2 (Repo Structure) — `storage.py` and `db/analysis.db`  
**Issue:** SQLite persistence is specified but table schemas are not defined.

**Required Table Definitions:**
```sql
-- Table: analysis_runs
CREATE TABLE analysis_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    input_files TEXT NOT NULL,  -- JSON array
    status TEXT NOT NULL  -- success | partial | failed
);

-- Table: findings
CREATE TABLE findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    severity TEXT NOT NULL,
    evidence TEXT NOT NULL,  -- JSON array
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);

-- Table: hypotheses
CREATE TABLE hypotheses (
    hypothesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);

-- Table: reports
CREATE TABLE reports (
    run_id TEXT PRIMARY KEY,
    report_text TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
);
```

**Fix Required:** ✅ Add SQLite schema to Phase 0  
**Principle Engineer Impact:** Must implement `storage.py` with these exact tables

---

### **GAP 8: Missing CLI Argument Specification**
**Location:** Section 6 (Commands We Will Use)  
**Issue:** Only one example command shown. Full CLI interface not specified.

**Current:**
```bash
python main.py --input data/evtx_parsed/ --output console
```

**Required Full CLI Specification:**
```bash
# Required arguments
python main.py --input <path>  # Path to parsed EVTX JSON files

# Optional arguments
--output <console|file>        # Default: console
--model <model-name>           # Default: gpt-4
--db <path>                    # Default: db/analysis.db
--verbose                      # Enable debug logging
--dry-run                      # Validate inputs only, no LLM call

# Examples
python main.py --input data/evtx_parsed/
python main.py --input data/evtx_parsed/ --output file --verbose
python main.py --input data/evtx_parsed/ --dry-run
```

**Fix Required:** ✅ Add full CLI specification  
**Principle Engineer Impact:** Must implement argparse with these exact flags

---

## 🔧 Required Enhancements for AI-to-AI Clarity

### **Enhancement 1: Add Type Hints Requirement**
**Issue:** Phase 0 does not specify type hints/annotations for principle engineer.

**Required Addition:**
```
Code Quality Requirements:
- All functions must include type hints
- Use Python 3.10+ syntax
- Pydantic models for all schemas
- No 'Any' types unless explicitly justified
```

**Why This Matters:** Prevents ambiguity in implementation.

---

### **Enhancement 2: Add Dependency Specification**
**Issue:** `requirements.txt` mentioned but not defined.

**Required `requirements.txt` Content:**
```
openai>=1.0.0
pydantic>=2.0.0
python-evtx>=0.7.4  # If EVTX parsing is in-scope
# OR: Explicitly state that pre-parsed JSON is expected
```

**Fix Required:** ✅ Define dependencies in Phase 0

---

### **Enhancement 3: Add Testing Requirements**
**Issue:** No testing guidance for principle engineer.

**Required Addition:**
```
Verification Requirements (for Overseer):
- Unit tests for schema validation
- Integration test for full data flow
- Negative tests for malformed inputs
- LLM output rejection tests
```

**Fix Required:** ⚠️ Add testing requirements (not in original Phase 0 scope but critical for Overseer role)

---

## 📋 Phase 0 Exit Checklist (Current Status)

- ☑ Repo structure agreed and created  
- ☑ Dataset choice locked (EVTX-ATTACK-SAMPLES)  
- ⚠️ Data flow explainable end-to-end (needs failure paths)  
- ⚠️ Output schema defined (needs provenance + error handling)  
- ☑ LLM role constrained  
- ☑ No action/determination paths exist  
- ❌ SQLite schema not defined  
- ❌ CLI specification incomplete  
- ❌ Security policies not enumerated  

**Overall Status:** 5/9 complete

---

## 🎯 Recommendations to Architect

### **Priority 1 (Blocking):**
1. ✅ Define provenance schema for evidence
2. ✅ Add SQLite table definitions
3. ✅ Add error handling schema
4. ✅ Complete CLI argument specification

### **Priority 2 (High):**
5. ⚠️ Add data flow failure paths
6. ⚠️ Define security.py policies explicitly
7. ⚠️ Specify EVTX preprocessing approach

### **Priority 3 (Recommended):**
8. ℹ️ Expand severity enum to 5 levels
9. ℹ️ Add type hint requirements
10. ℹ️ Define requirements.txt

---

## 📤 Next Steps

**For Architect:**
1. Review gaps and make decisions on severity levels, EVTX preprocessing
2. Enhance Phase 0 document with missing specifications
3. Return updated Phase 0 to Overseer for re-validation

**For Overseer (me):**
1. Upon receiving updated Phase 0:
   - Validate all gaps resolved
   - Generate "Phase 0 AI-Ready Handoff Document"
   - Update Rubric_Filled_Knowns.md with Phase 0 completion status

**For Principle Engineer (future):**
- Will receive enhanced Phase 0 with zero ambiguity
- All implementation decisions pre-made
- Clear success/failure criteria

---

## Overseer Signature

**Validation Performed By:** Overseer AI  
**Review Date:** December 16, 2025  
**Status:** Phase 0 requires enhancements (not approved for handoff yet)  
**Estimated Time to Address Gaps:** 30-45 minutes (Architect)

---

**End of Phase 0 Validation Report**
