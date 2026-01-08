✅ VS Code Markdown Preview - Press Ctrl+Shift+V (or Cmd+Shift+V on Mac) to see a beautiful rendered version :

# 🎓 **PurpleLens Architecture - SOC Analyst's Guide**


## **What Problem Are We Solving?**

You're a SOC Analyst drowning in Windows event logs.
- You need to FIND SUSPICIOUS.

but:
- READING RAW `.evtx` files is PAINFUL (binary format)
- You have HUNDREDS of them
- You need to EXPLAIN what you found
- You want to REMEMBER what you analyzed

**What PurpleLens does:**
It's a smart assistant tool that:
1. CONVERTS messy binary logs into READABLE text
2. Reads through all events looking for PATTERNS
3. Writes a professional SECURITY REPORT
4. SAVES everything in a database so you can SEARCH LATER

---

## 📚 **Key Concepts to keep in mind**

| Term | What It Means in Plain English | Example |
|------|-------------------------------|---------|
| **Pipeline** | A series of steps that happen in order, like a workflow or an assembly line | Making coffee: grind beans → brew → pour → drink |
| **Orchestrator** | The "manager" that tells each step when to run | You are the orchestrator when you make breakfast - you coordinate toast, eggs, coffee. This is your main.py file. |
| **Schema** | A strict format/template that data MUST follow | A form with required fields - if you don't fill out "Name" and "Date", it's rejected |
| **Validation** | Checking if data follows the rules | TSA checking if your ID matches your boarding pass |
| **Deterministic** | Always produces the same output for the same input (no randomness) | A calculator: 2+2 always equals 4 |
| **Persistence** | Saving data permanently so it survives restarts | Writing notes in a notebook vs. remembering them in your head |
| **JSONL** | Text file format where each line is a separate event (easy for computers to read) | Like a spreadsheet saved as text, one row per line |

---

## 🏗️ **The Architecture: 5 Phases**

Think of this like a **security investigation workflow**, but automated:

### **🔹 Phase 0: Data Preparation (Before the Tool Runs)**

**What happens:** Convert binary Windows logs into text format


**Technical details:**
- **Input**: `.evtx` files (binary Windows Event Logs - unreadable by humans)
- **Tool**: PowerShell script [scripts/prep_evtx.ps1](../scripts/prep_evtx.ps1)
- **Process**: Uses Windows' built-in `Get-WinEvent` command to read the events, then converts to JSON
- **Output**: `.jsonl` files (text-based, one event per line)

**Why this matters:** 
- Python CAN'T easily read `.evtx` files (Microsoft proprietary format)
- PowerShell CAN, is native to Windows and designed for this
- JSONL is HUMAN-READABLE and MACHINE-PARSEABLE

**Example:**
```powershell
# This command reads binary logs and converts them
.\scripts\prep_evtx.ps1 -InputPath "data\evtx_raw" -OutputPath "data\evtx_parsed"
```

---

### **🔹 Phase 1: Ingest (Load the Data)**

**What happens:** Read all the JSONL files and ATTATCH TRACKING info


**Technical details:**
- **File**: [src/ingest.py](../src/ingest.py)
- **Function**: `load_events()`
- **What it does:**
  1. SCANS the DIRectory for all `.jsonl` files
  2. READS EACH file line-by-line
  3. ATTACHES **provenance** Metadata to EACH Event:
     - `_source_file`: Which file did this come from? (e.g., "Credential_hashdump.jsonl")
     - `_record_index`: Which line number in the file? (e.g., line 3)
     - `_event_id`: What Windows Event ID? (e.g., 4688 = Process Creation)

**Why provenance matters:**

When the tool says "I found suspicious activity", you can TRACE it back to the exact LOG FILE and LINE NUMBER.

**Technical term learned:** **Provenance** = proof of where data came from (chain of custody for digital evidence)

---

### **🔹 Phase 2: Analyze (Ask AI to Find Threats)**

**What happens:** SEND EVENTS to LLM and ask "What looks suspicious?"


**Technical details:**
- **File**: [src/llm_analyze.py](../src/llm_analyze.py)
- **Function**: `analyze_events()`
- **What it does:**
  1. **Batches** events (max 50 at a time or 24,000 characters)
     - *Why batch?* Sending 1,000 events one-by-one would take forever and cost $$$
  2. Builds a **prompt** (instructions for the AI):
     - "You are a SOC analyst. Analyze these Windows events..."
     - Includes the SCHEMA (format the AI must follow)
     - Includes the ACTUAL event DATA
  3. Calls OpenAI API with `response_format="json_object"` (forces structured output)
  4. **Retry logic**: If the API fails, TRIES 3 times with delays (0s, 1s, 2s)
  5. Parses the JSON response

**Key constraints:**
- **MAX_EVENTS_PER_BATCH = 50** (prevents overwhelming the AI)
- **MAX_PROMPT_CHARS = 24,000** (stays under OpenAI's token limits)

**Why use AI here?**
- Reading 1,000 events manually takes HOURS
- AI can SPOT PATTERNS humans miss (e.g., "These 5 events together indicate credential dumping")
- AI provides NATURAL language EXPLANATIONS

**Technical terms:**
- **Batch** = Grouping items together for efficiency
- **API (Application Programming Interface)** = A way for programs to talk to each other (like a restaurant menu - you order, kitchen delivers)

---

### **🔹 Phase 3: Validate (Check for Quality & Safety)**

**What happens:** Make sure the AI's RESPONSE FOLLOWS RULES and doesn't say dangerous things


**This happens in TWO steps:**

#### **Step 3A: Schema Validation** 
- **File**: [src/schemas.py](../src/schemas.py)
- **Technology**: Pydantic (Python library for data validation)
- **What it checks:**
  - **Structure**: Does the response have ALL required fields? (findings, hypotheses, confidence, etc.)
  - **Types**: Is `confidence` a number between 0-1? Is `severity` one of (info/low/medium/high/critical)?
  - **Required fields**: Every FINDING MUST have EVIDENCE. Every evidence must have a SOURCE file.

**If validation fails:** The tool reports "validation_error" and shows you what's wrong.

#### **Step 3B: Policy Enforcement (Security Rules)**
- **File**: [src/security.py](../src/security.py)
- **Function**: `validate_output()`
- **What it checks:** SCANS ALL text for **5 prohibited patterns** (using regex):

| Pattern | Why It's Prohibited | Example |
|---------|---------------------|---------|
| "I have blocked..." | AI shouldn't claim to take actions | ❌ "I have removed the malware" |
| "This is malicious" | AI shouldn't make absolute judgments | ❌ "This is definitely malicious" |
| "Action taken" | AI shouldn't pretend to execute commands | ❌ "Action taken to isolate the host" |
| "System modified" | AI shouldn't claim to change systems | ❌ "System modified to block the IP" |
| "Confirmed that" | AI shouldn't express certainty | ❌ "Confirmed that this is an attack" |

**Why these rules exist:**
- The AI is an **ANALYST**, not an **operator**
- It provides **INTELLIGENCE**, not **automated remediation**
- The HUMAN make decisions and takes actions

**Technical terms:**
- **Schema** = A template defining what data must look like
- **Validation** = Checking if data matches rules
- **Regex (Regular Expression)** = Pattern matching for text (like Ctrl+F on steroids)

---

### **🔹 Phase 4: Report (Generate the Final Document)**

**What happens:** Take VALIDATED findings and FORMATS them into a professional SOC REPORT


**Technical details:**
- **File**: [src/report.py](../src/report.py)
- **Function**: `generate_report()`
- **What it does:**
  1. Checks the status (success vs. error)
  2. Builds an ASCII banner header
  3. Sorts findings by **severity** (CRITICAL → HIGH → MEDIUM → LOW → INFO)
  4. Formats sections:
     - **Findings** (with evidence citations)
     - **Hypotheses** (theories to investigate)
     - **IOCs** (Indicators of Compromise)
     - **Recommended Next Steps**
  5. Appends overall CONFIDENCE SCORE

**Critical detail:** This phase uses **NO AI**. It's 100% deterministic Python code.
- *Why?* Avoid DOUBLE API costs and ensure CONSISTENCEY
- *Benefit:* Same FINDINGS = Same REPORT every time

**Technical terms:**
- **Deterministic** = Predictable, reproducible output (no randomness)

---

### **🔹 Phase 5: Persist (Save to Database)**

**What happens:** STORE EVERYTHING in a SQLite DB for future reference

**Technical details:**
- **File**: [src/storage.py](../src/storage.py)
- **Functions**: `initialize_database()`, `save_analysis()`
- **Database**: SQLite (`db/analysis.db`)
- **5 Tables:**

| Table Name | What It Stores | Example |
|------------|----------------|---------|
| `analysis_runs` | Metadata per run | Run ID, timestamp, model used, status |
| `findings` | Security findings | Title, severity, summary, evidence JSON |
| `hypotheses` | Investigation theories | Description, confidence score |
| `indicators_of_compromise` | IOCs | Malicious IPs, file hashes, commands |
| `reports` | Full report text | The final markdown report |

**Key features:**
- **Foreign keys**: All tables link to `analysis_runs` via `run_id` (keeps related data together)
- **Parameterized queries**: Prevents SQL INJECTION ATTACKS
- **UTC timestamps**: No timezone confusion

**Why use a database instead of text files?**
- You can QUERY: "Show me all HIGH severity findings from last month"
- You can AGGREGATE: "How many times have we seen T1003 (Credential Dumping)?"
- You can JOIN: "What IOCs appeared in multiple runs?"

**Technical terms:**
- **Database** = Structured storage for queryable data
- **SQL (Structured Query Language)** = Language for asking databases questions
- **Foreign Key** = A field that links one table to another (like a reference number)
- **UTC (Coordinated Universal Time)** = Standard time zone (prevents "is that 3pm EST or PST?" confusion)

---

## 🎯 **How It All Fits Together**

```
YOU (SOC Analyst) → Run command:
   python -m src.main --input data/evtx_parsed/ --verbose

↓

PHASE 1: Ingest
   - Load 15 events from 3 JSONL files
   - Tag each event with source file + line number

↓

PHASE 2: Analyze  
   - Batch all 15 events into one prompt
   - Send to OpenAI: "Analyze these Windows events for threats"
   - Receive JSON response with findings

↓

PHASE 3A: Schema Validation (Structure)
   - Pydantic checks: "Does this JSON match our template?"
   - Validates severity, confidence, required fields

↓

PHASE 3B: Security Validation (Language Policy)
   - Regex scans stringified JSON: "Does this violate language policy?"
   - Blocks phrases like "I have blocked..." or "This is malicious"

↓

PHASE 4: Report
   - Python code formats findings into markdown
   - Sorts by severity, adds banner, appends recommendations

↓

PHASE 5: Persist
   - Saves run metadata to analysis_runs table
   - Saves findings to findings table
   - Saves full report to reports table

↓

YOU receive:
   - Console output (or file in reports/)
   - Database record you can query later
```

---

## 🔧 **The Orchestrator: [src/main.py](../src/main.py)**

This file is the **manager** that runs all 5 phases in order.

**Key functions:**
1. `parse_args()` - Reads your command-line flags (--input, --verbose, etc.)
2. `ensure_environment()` - Checks API key exists, creates directories
3. `run()` - Executes the full pipeline

**Think of it like a recipe:**
```python
def run():
    events = ingest.load_events()          # Phase 1
    analysis = llm_analyze.analyze(events) # Phase 2
    validate(analysis)                     # Phase 3
    report = generate_report(analysis)     # Phase 4
    storage.save(analysis)                 # Phase 5
    print(report)                          # Show results
```

---

## ❓ **Common Questions**

**Q: Why not just feed raw .evtx files to Python?**
A: `.evtx` is a Microsoft proprietary binary format. Python libraries for it are unreliable. PowerShell's `Get-WinEvent` is native and robust.

**Q: Why not let the AI write the report too?**
A: Costs double (two API calls) and introduces randomness. Deterministic formatting is faster, cheaper, and more predictable.

**Q: What if the AI hallucinates or gives bad advice?**
A: The security.py rules block dangerous phrases. The schema validation ensures structure. But YOU still review the findings - the tool is an assistant, not a replacement for analyst judgment.

**Q: Can I query old analyses?**
A: Yes! The SQLite database stores everything. You can write SQL queries or use tools like DB Browser for SQLite.

---


You now have the foundation to confidently explain this system in an interview!
