# 📄 **Lesson 06: Phases 4 & 5 Deep Dive - Report Generation & Database Storage**

This lesson takes you inside the final two phases: **Phase 4** generates human-readable markdown reports ([src/report.py](../src/report.py)) and **Phase 5** persists data to SQLite for long-term storage and querying ([src/storage.py](../src/storage.py)).

---

## **🎯 Learning Goals**

By the end of this lesson, you'll be able to:
- ✅ Explain the dual storage strategy (markdown report + structured data tables)
- ✅ Walk through YOUR markdown report generation logic
- ✅ Understand YOUR SQLite database schema (5 tables)
- ✅ Trace how validated data flows into database tables
- ✅ Query the database to retrieve analysis results
- ✅ Understand foreign key relationships
- ✅ Debug report generation and database issues

---

## **📚 Understanding the Output Strategy**

After validation in Phase 3, you have a structured `AnalysisOutput` Pydantic object. This data needs to be presented and stored in different ways:

### **Phase 4: Generate Markdown Report (Human-Readable)**

**What it creates:** A single markdown text string formatted for human readers

**Who reads this:** SOC analysts, managers, auditors

**Why markdown:**
- ✅ Human-readable (formatted text, not raw JSON)
- ✅ Easy to share (email, Slack, tickets)
- ✅ Rendered nicely (GitHub, VS Code, Notion, etc.)
- ✅ Structured but flexible
- ✅ Copy-paste friendly

**Example use cases:**
- Email to your manager: "Here's today's analysis"
- Attach to incident ticket
- Share with other teams
- Archive for compliance

---

### **Phase 5: Persist to Database (Dual Storage)**

**What it stores:** TWO representations of the same data

**1. Markdown Report (reports table):**
- Stores the full markdown text from Phase 4
- Archived for historical retrieval
- One report per run (1:1 relationship via run_id)

**2. Structured Data (findings/hypotheses/IOCs tables):**
- Stores the underlying data in queryable relational format
- Normalized across multiple tables
- Enables SQL queries and aggregations

**Who uses the database:**
- **Reports table:** Humans retrieving past reports
- **Data tables:** Scripts, dashboards, SIEM integrations, trend analysis tools

**Why store both:**
- ✅ **Report text:** Preserves exact formatting for compliance/archives
- ✅ **Structured tables:** Enables SQL queries like "show all high-severity findings from last week"
- ✅ **Together:** Complete audit trail (what was found + how it was reported)

**Example database use cases:**
- "Show me all high-severity findings from last week"
- "Which IOCs appear most frequently?"
- "What's the trend in confidence scores over time?"
- Dashboard showing analysis metrics
- Feed findings into SIEM/EDR
- Retrieve markdown report from 3 runs ago

---

## **📄 Phase 4: Report Generation**

Open [src/report.py](../src/report.py) - this converts validated data to markdown.

### **The Entry Point: generate_report() (Lines 18-37)**

Let's read YOUR implementation:

```python
def generate_report(analysis: AnalysisOutput) -> str:
    """Generate deterministic SOC report from the structured analysis object."""

    if analysis.status != "success":
        return generate_error_report(analysis)
    sections: List[str] = []
    sections.extend(_header_lines("Analysis Report"))
    sections.append("## FINDINGS")
    sections.extend(_format_findings(analysis.findings))
    sections.append("## HYPOTHESES")
    sections.extend(_format_hypotheses(analysis.hypotheses))
    sections.append("## INDICATORS OF COMPROMISE")
    sections.extend(_format_list(analysis.indicators_of_compromise))
    sections.append("## RECOMMENDED NEXT STEPS")
    sections.extend(_format_list(analysis.recommended_next_steps))
    sections.append("=" * 80)
    sections.append(f"Overall Confidence: {analysis.confidence:.2f}")
    sections.append("=" * 80)
    return "\n".join(sections)
```

**Let's break this down section by section:**

---

#### **Understanding the Flow**

**If status != "success":** Returns `generate_error_report(analysis)` (lines 40-67) - we'll cover this next

**If status == "success":** Builds report in sections using helper functions:

1. `_header_lines("Analysis Report")` - Creates banner header (lines 70-77)
2. `_format_findings()` - Formats all findings with evidence (lines 80-97)
3. `_format_hypotheses()` - Formats hypotheses with confidence (lines 100-104)
4. `_format_list()` - Formats IOCs and recommendations (lines 107-110)
5. Footer with overall confidence score

**What this creates:**

```markdown
================================================================================
PURPLELENS AI SOC ASSISTANT
Analysis Report
================================================================================

## FINDINGS
### [HIGH] Credential Dumping via lsass.exe Access
Summary: Process wmic.exe accessed lsass.exe memory
Evidence:
  - Credential_hashdump.jsonl:0 | "Image": "C:\\Windows\\System32\\wmic.exe"

## HYPOTHESES
- Attacker used WMIC to dump credentials (confidence: 0.80)

## INDICATORS OF COMPROMISE
- wmic.exe
- lsass.exe

## RECOMMENDED NEXT STEPS
- Review process tree for wmic.exe
- Check authentication logs

================================================================================
Overall Confidence: 0.85
================================================================================
```

---

#### **Error Report: generate_error_report() (Lines 40-67)**

```python
def generate_error_report(analysis: AnalysisOutput) -> str:
    """Generate degraded report describing partial results and next actions."""

    sections: List[str] = []
    sections.extend(_header_lines("Analysis Report — INCOMPLETE"))
    sections.append(f"STATUS: {analysis.status}")
    explanation = STATUS_EXPLANATIONS.get(
        analysis.status, "Analysis did not complete successfully."
    )
    sections.append(f"ERROR: {analysis.error_message or explanation}")
    sections.append("")
    sections.append(f"PARTIAL FINDINGS: {len(analysis.findings)} extracted before failure")
    if analysis.findings:
        sections.extend(_format_findings(analysis.findings))

    sections.append("RECOMMENDED ACTION:")
    sections.append("- Review logs for additional details.")
    if analysis.status == "llm_error":
        sections.append("- Check OpenAI API connectivity and credentials.")
    if analysis.status == "timeout":
        sections.append("- Re-run analysis with fewer events or during lower load.")
    if analysis.status == "validation_error":
        sections.append("- Inspect LLM output logs for policy or schema violations.")
    sections.append("- Retry the CLI with --verbose for additional diagnostics.")
    sections.append("- Verify input files are valid JSONL if the issue persists.")
    sections.append("=" * 80)
    return "\n".join(sections)
```

**Error report features:**
- Shows status (validation_error, llm_error, timeout)
- Displays error message with explanation
- Shows partial findings if any were extracted before failure
- Provides actionable troubleshooting steps based on error type

**This section won't appear in successful analyses!**

---

#### **Section 3: Findings (Lines 41-49)**

```python
lines.append("## 🔍 Findings")
lines.append("")
if analysis.findings:
    for idx, finding in enumerate(analysis.findings, 1):
        lines.extend(_format_finding(idx, finding))
else:
    lines.append("*No findings identified.*")
    lines.append("")
```

**What this does:**
- Creates "Findings" section header
- If findings exist, format each one (we'll see `_format_finding()` next)
- If no findings, show "*No findings identified.*"

---

#### **Helper Functions**

**_header_lines() (Lines 70-77):**
```python
def _header_lines(subtitle: str) -> List[str]:
    return [
        "=" * 80,
        "PURPLELENS AI SOC ASSISTANT",
        subtitle,
        "=" * 80,
        "",
    ]
```

**_format_findings() (Lines 80-97):**
```python
def _format_findings(findings: List[Finding]) -> List[str]:
    if not findings:
        return ["(none)", ""]

    sections: List[str] = []
    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.index(f.severity))

    for finding in ordered:
        sections.append(f"### [{finding.severity.upper()}] {finding.title}")
        sections.append(f"Summary: {finding.summary}")
        sections.append("Evidence:")
        for ev in finding.evidence:
            sections.append(
                f"  - {ev.source_file}:{ev.record_index} | {ev.excerpt}"
            )
        sections.append("")

    return sections
```

**Key features:**
- Sorts findings by severity (critical → high → medium → low → info)
- Each finding shows title, summary, and evidence with full provenance
- Evidence includes source_file, record_index, and excerpt from event data
- No emojis - clean professional format

---

**_format_hypotheses() (Lines 100-104):**
```python
def _format_hypotheses(hypotheses: List[Hypothesis]) -> List[str]:
    if not hypotheses:
        return ["(none)", ""]
    return [f"- {h.description} (confidence: {h.confidence:.2f})" for h in hypotheses] + [
        ""
    ]
```

**_format_list() (Lines 107-110):**
```python
def _format_list(items: List[str]) -> List[str]:
    if not items:
        return ["(none)", ""]
    return [f"- {item}" for item in items] + [""]
```

**Key points:**
- Hypotheses: Simple list with description and confidence (no supporting evidence arrays)
- IOCs and recommendations: Both use `_format_list()` - just bullet points of strings
- All helpers return empty placeholder "(none)" if list is empty

**Example output:**

```markdown
## FINDINGS
### [HIGH] Credential Dumping via lsass.exe Access
Summary: Process wmic.exe accessed lsass.exe memory
Evidence:
  - Credential_hashdump.jsonl:0 | "Image": "C:\\Windows\\System32\\wmic.exe"
  - Credential_hashdump.jsonl:1 | "TargetImage": "lsass.exe"

## HYPOTHESES
- Attacker used WMIC to dump credentials (confidence: 0.80)
- Lateral movement preparation detected (confidence: 0.75)

## INDICATORS OF COMPROMISE
- wmic.exe
- lsass.exe
- mimikatz.exe

## RECOMMENDED NEXT STEPS
- Review process tree for wmic.exe
- Check authentication logs
```

---

## **💾 Phase 5: Database Storage**

Open [src/storage.py](../src/storage.py) - this persists data to SQLite.

### **Why SQLite?**

**SQLite** = Lightweight, serverless, file-based SQL database

**Advantages:**
- ✅ Zero configuration (no server to install/manage)
- ✅ Single file (`purplelens.db`)
- ✅ Full SQL support (JOIN, aggregation, indexes)
- ✅ ACID transactions (atomic, consistent, isolated, durable)
- ✅ Perfect for local/demo apps
- ✅ Easy to backup (just copy the .db file)

**Production alternative:** PostgreSQL, MySQL for multi-user environments

---

### **YOUR Database Schema: 5 Tables**

Let's visualize YOUR schema:

```
┌─────────────────────────────┐
│   analysis_runs             │  Main table
│─────────────────────────────│
│ run_id TEXT (PK)            │←──┐
│ timestamp TEXT              │   │
│ input_files TEXT (JSON)     │   │
│ status TEXT (tri-state)     │   │
│ model_used TEXT             │   │
└─────────────────────────────┘   │
                                  │ Foreign Key (TEXT UUID)
┌─────────────────────────────┐   │
│   findings                  │───┘
│─────────────────────────────│
│ finding_id (PK AUTO)        │
│ run_id TEXT (FK)            │
│ title TEXT                  │
│ summary TEXT                │
│ severity TEXT (CHECK)       │
│ evidence TEXT (JSON array)  │
└─────────────────────────────┘
                                  │
┌─────────────────────────────┐   │
│   hypotheses                │───┤
│─────────────────────────────│   │
│ hypothesis_id (PK AUTO)     │   │
│ run_id TEXT (FK)            │   │
│ description TEXT            │   │
│ confidence REAL (CHECK)     │   │
└─────────────────────────────┘   │
                                  │
┌─────────────────────────────┐   │
│   indicators_of_compromise  │───┤
│─────────────────────────────│   │
│ ioc_id (PK AUTO)            │   │
│ run_id TEXT (FK)            │   │
│ indicator TEXT              │   │
└─────────────────────────────┘   │
                                  │
┌─────────────────────────────┐   │
│   reports                   │───┘
│─────────────────────────────│
│ run_id TEXT (PK & FK)       │  ← 1:1 relationship!
│ report_text TEXT            │
│ generated_at TEXT           │
└─────────────────────────────┘
```

**Key concepts:**
- **Primary Key (PK):** Unique identifier
  - `run_id` = TEXT UUID (not auto-increment integer!)
  - Other PKs = INTEGER AUTOINCREMENT (finding_id, hypothesis_id, ioc_id)
- **Foreign Key (FK):** Links to analysis_runs via TEXT UUID
- **One-to-Many:** One run → many findings/hypotheses/IOCs
- **One-to-One:** One run → one report (run_id is PK in reports table)
- **JSON columns:** input_files, evidence (stored as TEXT, parsed as JSON)
- **CHECK constraints:** Enforce status tri-state, severity enum, confidence 0-1

---

### **Schema Definition: initialize_database() (Lines 18-137)**

Let's read YOUR SQL schema:

```python
def initialize_database(db_path: str = "purplelens.db") -> None:
    """
    Create SQLite database and tables if they don't exist.
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table 1: analysis_runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL,
            error_message TEXT
        )
    """)
    
    # Table 2: findings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence REAL NOT NULL,
            source_file TEXT NOT NULL,
            record_index INTEGER NOT NULL,
            event_id TEXT,
            FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
        )
    """)
    
    # Table 3: hypotheses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hypotheses (
            hypothesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            hypothesis TEXT NOT NULL,
            confidence REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
        )
    """)
    
    # Table 4: iocs (indicators_of_compromise)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS iocs (
            ioc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            context TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
        )
    """)
    
    # Table 5: reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            report_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", db_path)
```

**Let's understand each table:**

---

#### **Table 1: analysis_runs (Lines 15-22)**

```sql
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    input_files TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'partial', 'failed')),
    model_used TEXT
)
```

**Stores:** Top-level metadata for each pipeline run

**Columns:**
- `run_id` - UUID string (e.g., "d87b14c8-89c9-42e7-aa80-2c8bb9e3081c"), NOT auto-increment
- `timestamp` - When the analysis ran (ISO 8601 format)
- `input_files` - JSON array of source JSONL files
- `status` - **Tri-state**: "success", "partial", or "failed"
  - success: All validation passed
  - partial: Validation failed but some findings extracted
  - failed: No usable data extracted
- `model_used` - OpenAI model name (e.g., "gpt-4o")

**Example rows:**
| run_id | timestamp | input_files | status | model_used |
|--------|-----------|-------------|--------|------------|
| d87b14c8... | 2024-03-15T10:00:00Z | ["Credential_hashdump.jsonl"] | success | gpt-4o |
| a12f3e89... | 2024-03-15T11:00:00Z | ["Lateral_wmic.jsonl"] | failed | gpt-4o |

---

#### **Table 2: findings (Lines 24-32)**

```sql
CREATE TABLE IF NOT EXISTS findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('info', 'low', 'medium', 'high', 'critical')),
    evidence TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
)
```

**Stores:** Individual security findings

**Key columns:**
- `run_id` - Links to `analysis_runs` (TEXT UUID, not INTEGER)
- `title` - Finding title
- `summary` - Description of the finding (NOT "description")
- `severity` - CHECK constraint enforces exact values (includes "info")
- `evidence` - **JSON TEXT** array of Evidence objects (source_file, record_index, event_id, excerpt)
- **No confidence column** - only overall run confidence stored
- **No source_file, record_index, event_id columns** - all in evidence JSON

**Example row:**
| finding_id | run_id | title | severity | evidence |
|------------|--------|-------|----------|----------|
| 1 | d87b14c8... | Credential Dumping | high | [{"source_file":"Credential_hashdump.jsonl","record_index":0,"excerpt":"wmic.exe"}] |

---

#### **Table 3: hypotheses (Lines 34-41)**

```sql
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
)
```

**Stores:** Investigative hypotheses

**Key columns:**
- `run_id` - TEXT UUID (not INTEGER)
- `description` - Hypothesis text (NOT "hypothesis")
- `confidence` - CHECK constraint enforces 0.0-1.0 range

---

#### **Table 4: indicators_of_compromise (Lines 43-49)**

```sql
CREATE TABLE IF NOT EXISTS indicators_of_compromise (
    ioc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    indicator TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
)
```

**Stores:** Indicators of Compromise

**Key columns:**
- `run_id` - TEXT UUID (not INTEGER)
- `indicator` - **Just a string** (e.g., "wmic.exe", "lsass.exe")
- **No type, value, context columns** - IOCs are simple strings in this schema

**Example rows:**
| ioc_id | run_id | indicator |
|--------|--------|--------|
| 1 | d87b14c8... | wmic.exe |
| 2 | d87b14c8... | lsass.exe |

---

#### **Table 5: reports (Lines 51-57)**

```sql
CREATE TABLE IF NOT EXISTS reports (
    run_id TEXT PRIMARY KEY,
    report_text TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
)
```

**Stores:** The full markdown report text

**Key columns:**
- `run_id` - TEXT UUID, **PRIMARY KEY** (not report_id!)
- **One report per run** - run_id is PK, ensures 1:1 relationship
- `generated_at` - When report was created (NOT "created_at")
- **No report_id column** - run_id serves as primary key

**Why store reports in DB?**
- Retrieve previous reports without regenerating
- Compare reports over time
- Export to other formats (PDF, HTML)
- Audit trail of what was reported

---

### **Saving Data: save_analysis() (Lines 70-89)**

This is where YOUR validated data gets inserted into the database:

```python
def save_analysis(
    db_path: str,
    run_id: str,
    analysis: AnalysisOutput,
    input_files: List[str],
    model_used: str,
    report_text: str,
    report_generated_at: datetime,
    run_timestamp: datetime | None = None,
) -> None:
    """Persist analysis outputs according to the architect-defined schema."""

    conn = _get_connection(db_path)
    try:
        with conn:
            _insert_analysis_run(conn, run_id, analysis, input_files, model_used, run_timestamp)
            _insert_findings(conn, run_id, analysis)
            _insert_hypotheses(conn, run_id, analysis)
            _insert_iocs(conn, run_id, analysis)
            _insert_report(conn, run_id, report_text, report_generated_at)
    finally:
        conn.close()
```

**Key parameters:**
- `run_id` - **UUID string** (generated by main.py, NOT auto-increment)
- `analysis` - AnalysisOutput Pydantic object (validated)
- `input_files` - List of JSONL source files
- `model_used` - OpenAI model name
- `report_text` - Generated markdown report
- `run_timestamp` - When analysis started

**Flow:** Delegates to helper functions for each table insert

---

#### **Helper: _insert_analysis_run() (Lines 109-126)**

```python
def _insert_analysis_run(
    conn: sqlite3.Connection,
    run_id: str,
    analysis: AnalysisOutput,
    input_files: List[str],
    model_used: str,
    run_timestamp: datetime | None,
) -> None:
    """Insert metadata for the analysis execution."""

    timestamp_source = run_timestamp or datetime.now(timezone.utc)
    timestamp = timestamp_source.isoformat()
    status_value = _derive_run_status(analysis)
    conn.execute(
        """
        INSERT INTO analysis_runs (run_id, timestamp, input_files, status, model_used)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, timestamp, json.dumps(input_files), status_value, model_used),
    )
```

**Key logic:**
- `run_id` is provided (UUID), not auto-generated
- `input_files` JSON-serialized to TEXT
- `status` derived from analysis (success/partial/failed) via `_derive_run_status()`

---

#### **Helper: _derive_run_status() (Lines 191-200)**

```python
def _derive_run_status(analysis: AnalysisOutput) -> str:
    """Map analyzer status into the storage status tri-state."""

    if analysis.status == "success":
        return "success"

    if analysis.findings or analysis.hypotheses or analysis.indicators_of_compromise:
        return "partial"

    return "failed"
```

**Tri-state mapping:**
- **success:** Pydantic and security validation passed
- **partial:** Validation failed BUT extracted some findings/hypotheses/IOCs
- **failed:** Validation failed AND no data extracted

---

#### **Helper: _insert_findings() (Lines 129-143)**

```python
def _insert_findings(conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput) -> None:
    """Persist findings and their evidence arrays."""

    for finding in analysis.findings:
        evidence_json = json.dumps([ev.model_dump() for ev in finding.evidence])
        conn.execute(
            """
            INSERT INTO findings (run_id, title, summary, severity, evidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, finding.title, finding.summary, finding.severity, evidence_json),
        )
```

**Key features:**
- Evidence array serialized to JSON TEXT
- Each Evidence object converted to dict via `.model_dump()`
- No individual confidence per finding (only overall run confidence)

---

#### **Helper: _insert_hypotheses() (Lines 146-156)**

```python
def _insert_hypotheses(conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput) -> None:
    """Persist hypotheses collected from the analysis."""

    for hypothesis in analysis.hypotheses:
        conn.execute(
            """
            INSERT INTO hypotheses (run_id, description, confidence)
            VALUES (?, ?, ?)
            """,
            (run_id, hypothesis.description, hypothesis.confidence),
        )
```

**Simpler than findings** - just description and confidence, no nested objects.

---

#### **Helper: _insert_iocs() (Lines 159-169)**

```python
def _insert_iocs(conn: sqlite3.Connection, run_id: str, analysis: AnalysisOutput) -> None:
    """Persist indicators of compromise."""

    for indicator in analysis.indicators_of_compromise:
        conn.execute(
            """
            INSERT INTO indicators_of_compromise (run_id, indicator)
            VALUES (?, ?)
            """,
            (run_id, indicator),
        )
```

**Simple strings** - no type/value/context structure, just the indicator text.

---

#### **Helper: _insert_report() (Lines 172-188)**

```python
def _insert_report(
    conn: sqlite3.Connection,
    run_id: str,
    report_text: str,
    report_generated_at: datetime,
) -> None:
    """Persist the deterministic SOC report."""

    generated_at = report_generated_at
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)

    conn.execute(
        """
        INSERT INTO reports (run_id, report_text, generated_at)
        VALUES (?, ?, ?)
        """,
        (run_id, report_text, generated_at.isoformat()),
    )
```

**Features:**
- Ensures timezone-aware datetime (adds UTC if naive)
- run_id is PRIMARY KEY (one report per run)
- Full markdown text stored in TEXT column

---

## **🔍 Querying the Database**

Now that data is stored, let's query it!

### **Example 1: Get All Runs**

```python
import sqlite3

conn = sqlite3.connect("db/analysis.db")
cursor = conn.cursor()

cursor.execute("SELECT run_id, timestamp, status, model_used FROM analysis_runs ORDER BY timestamp DESC")
rows = cursor.fetchall()

for row in rows:
    print(f"Run {row[0][:8]}...: {row[2]} (model: {row[3]})")

conn.close()
```

**Output:**
```
Run d87b14c8...: success (model: gpt-4o)
Run a12f3e89...: failed (model: gpt-4o)
```

**Note:** run_id is UUID string, not integer!

---

### **Example 2: Get High-Severity Findings**

```python
conn = sqlite3.connect("db/analysis.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT f.title, f.severity, f.evidence, a.timestamp
    FROM findings f
    JOIN analysis_runs a ON f.run_id = a.run_id
    WHERE f.severity IN ('high', 'critical')
    ORDER BY a.timestamp DESC
""")

rows = cursor.fetchall()

for row in rows:
    print(f"{row[0]} | {row[1].upper()} | {row[3]}")
    # Parse evidence JSON if needed
    import json
    evidence_list = json.loads(row[2])
    for ev in evidence_list:
        print(f"  - {ev['source_file']}:{ev['record_index']}")

conn.close()
```

**Output:**
```
Credential Dumping via lsass.exe | HIGH | 2024-03-15T10:00:00Z
  - Credential_hashdump.jsonl:0
  - Credential_hashdump.jsonl:1
```

**SQL features:**
- `JOIN` - Combine findings with run metadata
- `WHERE f.severity IN (...)` - Filter by severity
- Evidence is JSON TEXT - parse with `json.loads()`

---

### **Example 3: IOC Frequency Analysis**

```python
cursor.execute("""
    SELECT indicator, COUNT(*) as frequency
    FROM indicators_of_compromise
    GROUP BY indicator
    ORDER BY frequency DESC
    LIMIT 10
""")

rows = cursor.fetchall()

print("Top 10 most frequent IOCs:")
for row in rows:
    print(f"{row[0]} (seen {row[1]} times)")
```

**Output:**
```
Top 10 most frequent IOCs:
wmic.exe (seen 5 times)
lsass.exe (seen 5 times)
mimikatz.exe (seen 2 times)
```

**SQL features:**
- `GROUP BY indicator` - Aggregate by indicator text
- `COUNT(*)` - Count occurrences
- `LIMIT 10` - Top 10 only
- No type/value columns - just simple indicator strings
```

**Transaction logic:**
- `conn.commit()` - Save all changes (atomic)
- `conn.rollback()` - Undo all changes if error
- `conn.close()` - Always close connection

**ACID property:** All inserts succeed or all fail (no partial saves).

---

## **🔍 Querying the Database**

Now that data is stored, let's query it!

### **Example 1: Get All Runs**

```python
import sqlite3

conn = sqlite3.connect("purplelens.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM analysis_runs ORDER BY timestamp DESC")
rows = cursor.fetchall()

for row in rows:
    print(f"Run {row[0]}: {row[2]} (confidence: {row[3]})")

conn.close()
```

**Output:**
```
Run 2: timeout (confidence: 0.0)
Run 1: success (confidence: 0.85)
```

---

### **Example 2: Get High-Severity Findings**

```python
conn = sqlite3.connect("purplelens.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT f.title, f.severity, f.confidence, a.timestamp
    FROM findings f
    JOIN analysis_runs a ON f.run_id = a.run_id
    WHERE f.severity IN ('high', 'critical')
    ORDER BY f.confidence DESC
""")

rows = cursor.fetchall()

for row in rows:
    print(f"{row[0]} | {row[1].upper()} | Confidence: {row[2]:.2f} | {row[3]}")

conn.close()
```

**Output:**
```
Credential Dumping via lsass.exe | HIGH | Confidence: 0.85 | 2024-03-15 10:00:00
Lateral Movement via WMI | HIGH | Confidence: 0.80 | 2024-03-15 10:00:00
```

**SQL features used:**
- `JOIN` - Combine findings with run metadata
- `WHERE` - Filter by severity
- `ORDER BY` - Sort by confidence

---

### **Example 3: IOC Frequency Analysis**

```python
cursor.execute("""
    SELECT type, value, COUNT(*) as frequency
    FROM iocs
    GROUP BY type, value
    ORDER BY frequency DESC
    LIMIT 10
""")

rows = cursor.fetchall()

print("Top 10 most frequent IOCs:")
for row in rows:
    print(f"{row[0]}: {row[1]} (seen {row[2]} times)")
```

**Output:**
```
Top 10 most frequent IOCs:
process: wmic.exe (seen 5 times)
file: lsass.exe (seen 5 times)
process: mimikatz.exe (seen 2 times)
```

**SQL features:**
- `GROUP BY` - Aggregate by type + value
- `COUNT(*)` - Count occurrences
- `LIMIT 10` - Top 10 only

---

## **🎯 Key Takeaways**

### **Phase 4: Report Generation**
- ✅ Clean markdown format (no emojis in actual implementation)
- ✅ Structured sections (Findings, Hypotheses, IOCs, Recommendations)
- ✅ Evidence provenance (source_file:record_index | excerpt)
- ✅ Severity-sorted findings (critical → high → medium → low → info)
- ✅ Error reports with actionable troubleshooting steps
- ✅ Overall confidence footer

### **Phase 5: Database Storage**
- ✅ SQLite for queryable persistence (zero-config, single file)
- ✅ 5-table schema (analysis_runs, findings, hypotheses, indicators_of_compromise, reports)
- ✅ **UUID run_id** (TEXT, not INTEGER auto-increment)
- ✅ **Tri-state status** (success, partial, failed)
- ✅ **JSON columns** (input_files, evidence arrays)
- ✅ Foreign key relationships (one run → many findings/hypotheses/IOCs, one report)
- ✅ CHECK constraints (severity enum, confidence 0-1, status tri-state)
- ✅ Parameterized queries (SQL injection protection)
- ✅ Transaction context managers (atomic commits via `with conn:`)

### **Why Both?**
- **Reports** = Human communication (email, tickets, compliance archives)
- **Database** = Machine analysis (SQL queries, trend tracking, dashboards)
- Together = Complete audit trail (what was found + what was reported)

### **Critical Design Decisions**
- **run_id = UUID string** - Globally unique, enables distributed systems
- **Evidence as JSON** - Flexible array storage without separate junction table
- **Tri-state status** - Distinguishes success/partial/failed for analytics
- **1:1 run:report** - run_id is PK in reports table, enforces single report per run

---

## **💬 Interview Talking Points**

### **"How do you present analysis results to different audiences?"**

> "I implement dual output formats in Phases 4 and 5. 

For human consumers - SOC analysts, managers, auditors - I generate markdown reports in `src/report.py` with structured sections for findings, hypotheses, IOCs, and recommendations. I use text-based severity indicators like [HIGH] and [CRITICAL], formatted confidence scores, and evidence citations linking back to source files and record indexes for verification. 

For machine consumers - scripts, dashboards, SIEM integrations - I persist to SQLite in `src/storage.py` using a 5-table relational schema. The schema has `analysis_runs` as the parent table with foreign keys to `findings`, `hypotheses`, `indicators_of_compromise`, and `reports` tables, enabling SQL queries like 'show all high-severity findings from last week' or 'which IOCs appear most frequently.' Both outputs are generated from the same validated AnalysisOutput object, ensuring consistency."

---

### **"Walk me through your database schema design"**

> "I use a relational model with five tables. The `analysis_runs` table is the parent, storing run-level metadata: run_id as UUID text, timestamp, input_files as JSON, status with tri-state CHECK constraint, and model_used. The run_id is provided by main.py as a UUID string, not auto-generated. The four child tables - `findings`, `hypotheses`, `indicators_of_compromise`, and `reports` - all have foreign keys referencing this UUID run_id. The relationship is one-to-many for findings, hypotheses, and IOCs, but one-to-one for reports since run_id serves as the primary key in the reports table. I chose SQLite for its simplicity and zero configuration - it's a single file database perfect for demos and local deployments. Foreign key constraints enforce referential integrity, and I use parameterized queries with question mark placeholders to prevent SQL injection. Transaction handling via context managers ensures ACID properties - either all inserts succeed or all fail, preventing partial saves."

---

### **"How do you handle database errors during saves?"**

> "I wrap the entire save operation in a try-except-finally block with transaction semantics. In the `save_analysis()` function in storage.py, I use the UUID run_id provided by main.py to insert the analysis run record, then loop through findings, hypotheses, and IOCs, inserting each with that same run_id to maintain foreign key relationships. The transaction is managed via a `with conn:` context manager which automatically commits on success or rolls back on exception. If any insert fails - maybe a database lock, disk full, or constraint violation - the context manager handles rollback automatically. In main.py, the except block catches the exception, logs the error with details, and returns exit code 1 to signal failure. The finally block in storage.py ensures `conn.close()` always runs to prevent connection leaks. This transaction pattern is critical because partial saves would create orphaned records - like findings without a parent run - breaking referential integrity and corrupting query results."

---

### **"How would you extend the database for production use?"**

> "Several enhancements for production: First, add indexes on frequently queried columns like `findings.severity`, `analysis_runs.timestamp`, and `indicators_of_compromise.indicator` to speed up filtering and sorting. Second, add a `finding_evidence` junction table since evidence is currently stored as a JSON array in findings - proper normalization would enable direct SQL queries on specific evidence items without JSON parsing. Third, implement database migrations using a tool like Alembic to handle schema changes without data loss. Fourth, add audit columns - `created_at`, `updated_at`, `created_by` - for compliance tracking. Fifth, switch to PostgreSQL or MySQL for multi-user environments with better concurrency, connection pooling, and native JSON column types for flexible event storage. Finally, implement soft deletes with an `is_deleted` flag rather than hard deletes to maintain audit trails."

---

## **🧪 Hands-On Exercises**

### **Exercise 1: Generate a Report Manually**

```python
from src.ingest import load_events
from src.llm_analyze import analyze_events
from src.schemas import AnalysisOutput
from src.report import generate_report

# Load and analyze
events = load_events("data/evtx_parsed")
analysis_data = analyze_events(events, model="gpt-4o-mini")
validated = AnalysisOutput.model_validate(analysis_data)

# Generate report
report_text = generate_report(validated, events)

# Save to file
with open("test_report.md", "w", encoding="utf-8") as f:
    f.write(report_text)

print("Report saved to test_report.md")
print(f"Report length: {len(report_text)} characters")
```

**Then open test_report.md in VS Code to see the formatted output!**

---

### **Exercise 2: Save to Database and Query**

```python
from src.storage import initialize_database, save_analysis
import sqlite3

# Initialize database
initialize_database("test.db")

# Save analysis (assumes you have validated and report_text from Exercise 1)
run_id = save_analysis(validated, report_text, "test.db")
print(f"Saved as run_id: {run_id}")

# Query findings
conn = sqlite3.connect("test.db")
cursor = conn.cursor()

cursor.execute("SELECT title, severity, confidence FROM findings")
findings = cursor.fetchall()

print(f"\nFindings in database:")
for title, severity, confidence in findings:
    print(f"  - {title} ({severity}, confidence: {confidence:.2f})")

conn.close()
```

---

### **Exercise 3: Run Multiple Times and Compare**

```python
# Run analysis 3 times
for i in range(3):
    events = load_events("data/evtx_parsed")
    analysis_data = analyze_events(events, model="gpt-4o-mini")
    validated = AnalysisOutput.model_validate(analysis_data)
    report_text = generate_report(validated, events)
    run_id = save_analysis(validated, report_text, "test.db")
    print(f"Run {i+1}: run_id={run_id}")

# Query all runs
conn = sqlite3.connect("test.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT run_id, timestamp, status, confidence,
           (SELECT COUNT(*) FROM findings WHERE run_id = analysis_runs.run_id) as finding_count
    FROM analysis_runs
    ORDER BY run_id
""")

rows = cursor.fetchall()

print("\nAll runs:")
for row in rows:
    print(f"Run {row[0]}: {row[2]} | Confidence: {row[3]:.2f} | Findings: {row[4]} | {row[1]}")

conn.close()
```

**This demonstrates how the database accumulates history over time!**

---

## **🔗 Connections to Other Phases**

**Where do Phases 4 & 5 fit?**

```
Phase 3B: src/security.py validates content
    ↓
Phase 4: src/report.py generates markdown ← YOU ARE HERE
    ↓
Phase 5: src/storage.py persists to SQLite ← YOU ARE HERE
    ↓
OUTPUT:
  - report.md file (for humans)
  - purplelens.db database (for machines)
```

---

## **📝 Quick Reference**

### **Files:**
- [src/report.py](../src/report.py) - Markdown generation
- [src/storage.py](../src/storage.py) - SQLite persistence

### **Key Functions:**
- `generate_report(analysis, events) -> str` - Lines 10-68
- `initialize_database(db_path)` - Lines 18-137
- `save_analysis(analysis, report_text, db_path) -> int` - Lines 140-231

### **Database Schema:**
- `analysis_runs` - Main metadata table
- `findings` - Security findings (FK to runs)
- `hypotheses` - Investigative theories (FK to runs)
- `iocs` - Indicators of Compromise (FK to runs)
- `reports` - Markdown report text (FK to runs)

### **Report Sections:**
- Header (metadata)
- Findings (with severity emoji)
- Hypotheses (with supporting evidence)
- IOCs (compact list)
- Recommended Next Steps

---

## **🚀 Next Steps**

You now understand Phases 4 & 5! Move on to:
- **Lesson 07**: Hands-On - Add Custom Security Pattern
- **Lesson 08**: Hands-On - Customize Report Format
- **Lesson 09**: Debugging Bootcamp
- **Lesson 10**: Database Deep Dive (advanced queries)

You can now confidently explain output generation and data persistence strategies! 📄💾
