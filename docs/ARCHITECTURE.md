# PurpleLens AI SOC Assistant - Architecture Guide

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PURPLELENS AI SOC ASSISTANT                          │
│                    Windows Event Log Analysis System                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│                           INPUT LAYER (Data Preparation)                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌──────────────┐      PowerShell Script                                      │
│  │ .evtx Files  │────► scripts/prep_evtx.ps1 ────────┐                       │
│  │ (Binary)     │      [Get-WinEvent]                 │                       │
│  └──────────────┘      [ConvertTo-Json]               ▼                       │
│                                                  ┌──────────────┐              │
│                                                  │  .jsonl      │              │
│                                                  │  Files       │              │
│                                                  │ (Text-based) │              │
│                                                  └──────┬───────┘              │
│                                                         │                      │
│  Dataset: data/evtx_parsed/*.jsonl                     │                      │
│  - Execution_wmic.jsonl    (8 events)                  │                      │
│  - Credential_hashdump.jsonl (2 events)                │                      │
│  - Lateral_wmic.jsonl     (5 events)                   │                      │
│                                                         │                      │
└─────────────────────────────────────────────────────────┼──────────────────────┘
                                                          │
                                                          ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER (Python 3.13.5)                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         CLI ENTRYPOINT                                   │ │
│  │  src/main.py                                                             │ │
│  │  ┌────────────────────────────────────────────────────────────────┐     │ │
│  │  │ parse_args()      → CLI flag parsing (argparse)                │     │ │
│  │  │ ensure_environment() → API key validation, dir creation        │     │ │
│  │  │ run()             → Full pipeline orchestration                │     │ │
│  │  └────────────────────────────────────────────────────────────────┘     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                   │                                            │
│                                   │ Orchestrates ▼                             │
│  ┌────────────────────────────────┴─────────────────────────────────────┐    │
│  │                                                                        │    │
│  │  PHASE 1: INGEST                    PHASE 2: ANALYZE                  │    │
│  │  ┌──────────────────┐               ┌──────────────────┐             │    │
│  │  │ src/ingest.py    │               │ src/llm_analyze  │             │    │
│  │  ├──────────────────┤               │      .py         │             │    │
│  │  │ load_events()    │───events[]───►│ analyze_events() │             │    │
│  │  │                  │               │                  │             │    │
│  │  │ • Scan dir for   │               │ • Batch events   │             │    │
│  │  │   .jsonl files   │               │ • Build prompt   │             │    │
│  │  │ • Parse JSON     │               │ • Call OpenAI    │             │    │
│  │  │ • Attach         │               │ • Retry logic    │             │    │
│  │  │   provenance:    │               │ • Parse response │             │    │
│  │  │   - source_file  │               │                  │             │    │
│  │  │   - record_index │               │ MAX_EVENTS: 50   │             │    │
│  │  │   - event_id     │               │ MAX_CHARS: 24k   │             │    │
│  │  └──────────────────┘               └────────┬─────────┘             │    │
│  │                                               │ Raw JSON              │    │
│  └───────────────────────────────────────────────┼───────────────────────┘    │
│                                                   ▼                            │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 3: VALIDATE                                                    │    │
│  │  ┌────────────────────┐          ┌────────────────────┐              │    │
│  │  │ src/schemas.py     │◄─────────│ src/security.py    │              │    │
│  │  ├────────────────────┤  Scans   ├────────────────────┤              │    │
│  │  │ Pydantic Models:   │  Text    │ validate_output()  │              │    │
│  │  │                    │          │                    │              │    │
│  │  │ • AnalysisOutput   │          │ 5 PATTERNS:        │              │    │
│  │  │ • Finding          │          │ 1. I have blocked  │              │    │
│  │  │ • Evidence         │          │ 2. This is malicious│             │    │
│  │  │ • Hypothesis       │          │ 3. Action taken    │              │    │
│  │  │                    │          │ 4. System modified │              │    │
│  │  │ ENFORCES:          │          │ 5. Confirmed that  │              │    │
│  │  │ • Status enum      │          │                    │              │    │
│  │  │ • Severity enum    │          │ Returns: True/False│              │    │
│  │  │ • Confidence 0-1   │          │ + error message    │              │    │
│  │  │ • Required fields  │          │                    │              │    │
│  │  │ • event_id coercion│          │                    │              │    │
│  │  └────────┬───────────┘          └────────────────────┘              │    │
│  │           │ Valid AnalysisOutput                                      │    │
│  └───────────┼───────────────────────────────────────────────────────────┘    │
│              ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 4: REPORT                                                      │    │
│  │  ┌────────────────────┐                                               │    │
│  │  │ src/report.py      │                                               │    │
│  │  ├────────────────────┤                                               │    │
│  │  │ generate_report()  │                                               │    │
│  │  │                    │                                               │    │
│  │  │ • Check status     │                                               │    │
│  │  │ • Build banner     │                                               │    │
│  │  │ • Sort findings by │                                               │    │
│  │  │   severity         │                                               │    │
│  │  │ • Format sections  │                                               │    │
│  │  │                    │                                               │    │
│  │  │ NO LLM CALLS       │                                               │    │
│  │  │ 100% Deterministic │                                               │    │
│  │  └────────┬───────────┘                                               │    │
│  │           │ Formatted Text                                            │    │
│  └───────────┼───────────────────────────────────────────────────────────┘    │
│              ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 5: PERSIST                                                     │    │
│  │  ┌────────────────────┐                                               │    │
│  │  │ src/storage.py     │                                               │    │
│  │  ├────────────────────┤                                               │    │
│  │  │ initialize_db()    │                                               │    │
│  │  │ save_analysis()    │                                               │    │
│  │  │                    │                                               │    │
│  │  │ 5 TABLES:          │                                               │    │
│  │  │ 1. analysis_runs   │ ──┐                                           │    │
│  │  │    (run_id PK)     │   │ Foreign Key                               │    │
│  │  │                    │   │ Relationships                             │    │
│  │  │ 2. findings        │ ──┤                                           │    │
│  │  │    (run_id FK)     │   │                                           │    │
│  │  │                    │   │                                           │    │
│  │  │ 3. hypotheses      │ ──┤                                           │    │
│  │  │    (run_id FK)     │   │                                           │    │
│  │  │                    │   │                                           │    │
│  │  │ 4. iocs            │ ──┤                                           │    │
│  │  │    (run_id FK)     │   │                                           │    │
│  │  │                    │   │                                           │    │
│  │  │ 5. reports         │ ──┘                                           │    │
│  │  │    (run_id FK)     │                                               │    │
│  │  │                    │                                               │    │
│  │  │ • Parameterized    │                                               │    │
│  │  │   queries (no SQL  │                                               │    │
│  │  │   injection)       │                                               │    │
│  │  │ • UTC timestamps   │                                               │    │
│  │  │ • Foreign keys ON  │                                               │    │
│  │  └────────────────────┘                                               │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT LAYER                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌──────────────────┐         ┌──────────────────┐                           │
│  │ Console Output   │         │ File Output      │                           │
│  │ (--output console│         │ (--output file)  │                           │
│  │  or default)     │         │                  │                           │
│  │                  │         │ reports/         │                           │
│  │ Markdown-formatted│        │ analysis_<UUID>  │                           │
│  │ report to stdout │         │ .txt             │                           │
│  └──────────────────┘         └──────────────────┘                           │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐        │
│  │ Database Persistence                                              │        │
│  │ db/analysis.db (SQLite3)                                          │        │
│  │                                                                    │        │
│  │ Query examples:                                                   │        │
│  │ • List all runs:                                                  │        │
│  │   SELECT * FROM analysis_runs ORDER BY timestamp DESC;            │        │
│  │                                                                    │        │
│  │ • Get findings for specific run:                                  │        │
│  │   SELECT * FROM findings WHERE run_id = '<uuid>';                 │        │
│  │                                                                    │        │
│  │ • Count HIGH severity findings across all runs:                   │        │
│  │   SELECT COUNT(*) FROM findings WHERE severity = 'high';          │        │
│  └──────────────────────────────────────────────────────────────────┘        │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DEPENDENCIES                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────┐    ┌────────────────────┐    ┌──────────────────┐   │
│  │ OpenAI API         │    │ Pydantic v2        │    │ python-dotenv    │   │
│  ├────────────────────┤    ├────────────────────┤    ├──────────────────┤   │
│  │ • gpt-4o-mini      │    │ • Schema validation│    │ • .env loading   │   │
│  │ • gpt-4 (optional) │    │ • Type coercion    │    │ • API key mgmt   │   │
│  │ • JSON mode        │    │ • Error messages   │    │                  │   │
│  │ • Retry logic      │    │                    │    │                  │   │
│  │   (3 attempts)     │    │                    │    │                  │   │
│  └────────────────────┘    └────────────────────┘    └──────────────────┘   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Trace: One Event's Journey

```
1. RAW EVTX FILE
   ├─ Location: data/evtx_raw/Execution_wmic.evtx
   └─ Format: Binary Windows Event Log

2. POWERSHELL CONVERSION (scripts/prep_evtx.ps1)
   ├─ Command: Get-WinEvent -Path $evtxFile
   ├─ Transform: | ConvertTo-Json -Depth 10
   └─ Output: data/evtx_parsed/Execution_wmic.jsonl
      │
      └─ Example line:
         {"Event": {"System": {"EventID": 1}, "EventData": {...}}}

3. PYTHON INGEST (src/ingest.py)
   ├─ Function: load_events("data/evtx_parsed")
   ├─ Process:
   │  ├─ Scan directory for *.jsonl
   │  ├─ Parse each line as JSON
   │  └─ Attach provenance metadata
   │
   └─ Output: List[Dict]
      [
        {
          "_source_file": "Execution_wmic.jsonl",
          "_record_index": 0,
          "_event_id": "1",
          "Event": {"System": {"EventID": 1}, ...}
        },
        ...
      ]

4. LLM ANALYZE (src/llm_analyze.py)
   ├─ Function: analyze_events(events, "gpt-4o-mini")
   ├─ Process:
   │  ├─ Batch events (max 50 or 24k chars)
   │  ├─ Build prompt with system instructions + event JSON
   │  ├─ Call OpenAI API with response_format="json_object"
   │  ├─ Retry up to 3 times on error
   │  └─ Parse JSON response
   │
   └─ Output: Raw JSON string
      {
        "status": "success",
        "findings": [
          {
            "title": "Suspicious WMIC Execution",
            "severity": "high",
            "evidence": [
              {
                "source_file": "Execution_wmic.jsonl",
                "record_index": 0,
                "event_id": "1",
                "excerpt": "wmic process list /format:https://..."
              }
            ]
          }
        ],
        "confidence": 0.8
      }

5. SCHEMA VALIDATION (src/schemas.py)
   ├─ Class: AnalysisOutput.model_validate(json_data)
   ├─ Process:
   │  ├─ Parse JSON into Pydantic model
   │  ├─ Validate status enum (success/error/timeout/validation_error)
   │  ├─ Validate severity enum (info/low/medium/high/critical)
   │  ├─ Validate confidence is 0.0-1.0
   │  ├─ Coerce event_id integers to strings
   │  └─ Ensure all required fields present
   │
   └─ Output: AnalysisOutput object (typed, validated)

6. SECURITY VALIDATION (src/security.py)
   ├─ Function: validate_output(analysis_output)
   ├─ Process:
   │  ├─ Scan all text fields recursively
   │  ├─ Check against 5 prohibited patterns (regex)
   │  └─ Return True or raise ValueError
   │
   └─ Output: Validated AnalysisOutput (no policy violations)

7. REPORT GENERATION (src/report.py)
   ├─ Function: generate_report(analysis_output)
   ├─ Process:
   │  ├─ Check status (success vs error)
   │  ├─ Sort findings by severity (CRITICAL > HIGH > MEDIUM > LOW > INFO)
   │  ├─ Build ASCII banner
   │  ├─ Format sections (Findings, Hypotheses, IOCs, Recommendations)
   │  └─ Append confidence score
   │
   └─ Output: String (Markdown-formatted report)

8. PERSISTENCE (src/storage.py)
   ├─ Function: save_analysis(db_path, analysis_output, metadata)
   ├─ Process:
   │  ├─ INSERT INTO analysis_runs (run_id, status, model_used, ...)
   │  ├─ INSERT INTO findings (run_id, title, severity, evidence_json, ...)
   │  ├─ INSERT INTO hypotheses (run_id, description, confidence)
   │  ├─ INSERT INTO indicators_of_compromise (run_id, indicator)
   │  └─ INSERT INTO reports (run_id, report_text)
   │
   └─ Output: Data persisted to db/analysis.db

9. OUTPUT
   ├─ Console: Print report to stdout
   └─ File: Write to reports/analysis_<run_id>.txt
```

---

## File Responsibilities Matrix

| File | Primary Role | Key Functions | Dependencies |
|------|-------------|---------------|--------------|
| **src/main.py** | CLI orchestrator & entrypoint | `parse_args()`, `ensure_environment()`, `run()` | All other src/* modules |
| **src/ingest.py** | Load JSONL files, attach provenance | `load_events()` | json, pathlib |
| **src/llm_analyze.py** | OpenAI API integration & batching | `analyze_events()`, `_parse_llm_response()` | openai, schemas |
| **src/schemas.py** | Data models & validation rules | `AnalysisOutput`, `Finding`, `Evidence` | pydantic |
| **src/security.py** | Policy enforcement (regex patterns) | `validate_output()`, `PROHIBITED_PATTERNS` | re, schemas |
| **src/report.py** | Deterministic report formatting | `generate_report()`, `_build_banner()` | schemas |
| **src/storage.py** | SQLite persistence layer | `initialize_database()`, `save_analysis()` | sqlite3 |
| **scripts/prep_evtx.ps1** | Convert .evtx to .jsonl | PowerShell script | Get-WinEvent |
| **tests/test_phase1*.py** | Unit & integration tests | Pytest & script-based tests | All src/* modules |

---

## Error Handling Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                           │
└─────────────────────────────────────────────────────────────────┘

1. MISSING API KEY
   ├─ Detection: ensure_environment() in main.py
   ├─ Error: "OPENAI_API_KEY environment variable is not set"
   ├─ Exit Code: 1
   └─ User Action: Set API key in .env file

2. EMPTY DIRECTORY
   ├─ Detection: load_events() in ingest.py
   ├─ Error: "No JSONL files found in {directory}"
   ├─ Exit Code: 1
   └─ User Action: Check input path, ensure .jsonl files exist

3. MALFORMED JSON
   ├─ Detection: load_events() in ingest.py
   ├─ Handling: Log warning, skip line, continue processing
   ├─ Exit Code: 0 (graceful degradation)
   └─ User Action: Review logs, fix source data if needed

4. LLM API ERROR
   ├─ Detection: analyze_events() in llm_analyze.py
   ├─ Retry Logic: 3 attempts with exponential backoff (0s, 1s, 2s)
   ├─ Status: "llm_error"
   ├─ Report: Partial findings + error message
   └─ User Action: Check API key, network, OpenAI status

5. SCHEMA VALIDATION FAILURE
   ├─ Detection: Pydantic model validation in schemas.py
   ├─ Status: "validation_error"
   ├─ Report: Error details in logs
   └─ User Action: Review LLM output logs, adjust prompt if needed

6. SECURITY POLICY VIOLATION
   ├─ Detection: validate_output() in security.py
   ├─ Status: "validation_error"
   ├─ Report: Pattern that triggered violation
   └─ User Action: Review LLM output, adjust system prompt

7. DATABASE ERROR
   ├─ Detection: save_analysis() in storage.py
   ├─ Handling: Log error, continue with report output
   ├─ Exit Code: 0 (report still generated)
   └─ User Action: Check db/ directory permissions, disk space
```

---

## Architecture Decisions & Rationale

### 1. **Why JSONL instead of direct .evtx parsing in Python?**
   - **Reason**: Python .evtx parsing libraries are complex and platform-dependent
   - **Benefit**: PowerShell's Get-WinEvent is native, robust, well-documented
   - **Trade-off**: Extra preprocessing step, but cleaner separation of concerns

### 2. **Why separate schemas.py and security.py?**
   - **Reason**: Single Responsibility Principle
   - **schemas.py**: Structural validation (types, required fields, ranges)
   - **security.py**: Business logic validation (policy enforcement)
   - **Benefit**: Easy to modify policies without touching core data models

### 3. **Why deterministic report.py (no LLM)?**
   - **Reason**: Avoid double API costs and latency
   - **Benefit**: Fast, predictable, testable report generation
   - **Trade-off**: Less "natural" language, but more reliable

### 4. **Why SQLite instead of JSON files for persistence?**
   - **Reason**: Structured queries, relationships, indexing
   - **Benefit**: Can query across runs, aggregate statistics, join tables
   - **Example**: "Find all HIGH severity findings from last 30 days"

### 5. **Why batch events instead of one-by-one LLM calls?**
   - **Reason**: Reduce API calls, provide cross-event context
   - **Benefit**: Lower cost, better correlation of related events
   - **Limit**: 50 events or 24k chars to stay within token limits

---

