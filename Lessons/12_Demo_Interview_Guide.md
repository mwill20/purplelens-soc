# Lesson 12: Live Demo - Interview Presentation Guide

Demo walkthrough for presenting ThreatPrism live. It is aligned to the current code and repo layout.

Gemini quick-switch (PowerShell):
```powershell
$provider = "gemini"
$model = "gemini-flash-latest"
# Or:
# $provider = "openai"
# $model = "gpt-4o"
```
Use in commands:
```powershell
python -m src.main --input data/evtx_sample --provider $provider --model $model
```

Time: 10-15 minutes of demo + 5-10 minutes of Q&A.

---

## Demo Goals

By the end of the demo, the interviewer should understand:
- The problem solved and why it matters
- How the system works end-to-end
- Design decisions and trade-offs
- Codebase navigation
- How validation and safety controls are enforced

---

## Pre-Demo Checklist

Before the demo, verify:
- Repo is open in VS Code.
- `.env` exists with `GEMINI_API_KEY` (default provider) or `OPENAI_API_KEY` set (do not display the key).
- Virtual environment is available and activated.
- Dependencies installed: `pip install -r requirements.txt`.
- Data folders exist:
  - `data/evtx_sample` (15-event JSONL demo set)
  - `data/evtx_raw` (raw EVTX sample for binary vs JSONL contrast)
  - Optional: `data/evtx_parsed` if you want to show local conversion output
- Optional: `db/analysis.db` has prior runs.
- Architecture diagram ready: `docs/ThreatPrism_Architecture.png`.
- Diagram reflects current pipeline: sanitize (prompt firewall), optional semantic judge, AIOps artifacts, and red-team dataset.
- AWS sample path ready:
  - `data/sample_cloudtrail.csv` (in repo)
  - `data/sample_aws.jsonl` (after conversion)
- GCP sample path ready (choose one):
  - `data/gcp_synthetic_minilab.jsonl` (3-event JSONL, fast)
  - `data/gcp_log_pack/minilab_ground_truth_complete.json` (full mini-lab)

### Quick validation command

Lists each JSONL file in data\evtx_sample and prints the filename along with the number of events (lines) it contains.

```powershell
Get-ChildItem data\evtx_sample\*.jsonl | ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    Write-Host "$($_.Name): $lines events"
}
```

---

## Single Demo Runbook (copy/paste from here)

This is the clean, single place to run the full demo (Windows + AWS + GCP).

```powershell
# Activate virtual environment
.venv\Scripts\Activate

# Choose provider
$provider = "gemini"
$model = "gemini-flash-latest"
# Or:
# $provider = "openai"
# $model = "gpt-4o"

# ----------------------------
# A) WINDOWS DEMO (15 events)
# ----------------------------
$winInput = "data\\evtx_sample"
Write-Host "`n=== Windows Dataset ===" -ForegroundColor Cyan
Get-ChildItem $winInput\*.jsonl | ForEach-Object {
    $lineCount = (Get-Content $_.FullName | Measure-Object -Line).Lines
    Write-Host "$($_.Name): $lineCount events"
}

Write-Host "`n=== Windows Run ===" -ForegroundColor Cyan
python -m src.main --input $winInput --verbose --provider $provider --model $model

# ----------------------------
# B) AWS DEMO (CloudTrail)
# ----------------------------
# Convert the sample CSV (one-time):
# python scripts/aws_csv_to_jsonl.py data/sample_cloudtrail.csv data/sample_aws.jsonl
$awsInput = "data\\sample_aws.jsonl"

Write-Host "`n=== AWS Run ===" -ForegroundColor Cyan
python -m src.main --input $awsInput --source aws --verbose --provider $provider --model $model

# ----------------------------
# C) GCP DEMO (Audit Logs)
# ----------------------------
$gcpInput = "data\\gcp_synthetic_minilab.jsonl"

Write-Host "`n=== GCP Run ===" -ForegroundColor Cyan
python -m src.main --input $gcpInput --source gcp --verbose --provider $provider --model $model
```

Narration tips (short and simple):
- Windows run shows baseline EVTX pipeline.
- AWS run shows adapter + plane tagging + correlation + AWS prompt batching.
- GCP run shows audit log normalization + plane tagging + enrichment + GCP prompt.
- The core pipeline is unchanged; only the adapter and prompt differ.

---

## Demo Script - Act 1: The Problem (2 minutes)

### Opening statement

> "I built ThreatPrism, an AI-assisted Windows event log analysis tool for SOC analysts. Let me show you the problem it solves."

Pain point: Raw EVTX files are binary and not human readable.
```powershell
# Raw EVTX (binary)
Get-Content data\evtx_raw\Execution_wmic.evtx -TotalCount 1
```

This tool converts them into human and machine readable JSONL.
```powershell
# Parsed JSONL from the same EVTX file (readable)
Get-Content data\evtx_parsed\Execution_wmic.jsonl -TotalCount 1 |
  ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }

# If you only have the repo sample:
Get-Content data\evtx_sample\Execution_wmic.jsonl -TotalCount 1 |
  ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }
```

### Show the architecture diagram

- Open `docs/ThreatPrism_Architecture.png`
- Point to sanitize (prompt firewall), validate_output (schema + policy + semantic), and AIOps artifacts

Conversion:
> "The EVTX-to-JSON conversion is handled with PowerShell using `scripts/prep_evtx.ps1` and Get-WinEvent, then the Python pipeline takes over."

---

## Demo Script - Act 2: Live Run (3-4 minutes)

### Run the tool end-to-end

Use the 15-event dataset for a reliable first run.

```powershell
# Activate virtual environment (if not already)
.venv\Scripts\Activate

# Choose the dataset
$demoInput = "data\\evtx_sample"

# Show the demo dataset
Write-Host "`n=== Demo Dataset ===" -ForegroundColor Cyan
Get-ChildItem $demoInput\*.jsonl | ForEach-Object {
    $lineCount = (Get-Content $_.FullName | Measure-Object -Line).Lines
    Write-Host "$($_.Name): $lineCount events"
}

# Run the tool with verbose output (Gemini default)
Write-Host "`n=== Running Analysis ===" -ForegroundColor Cyan
python -m src.main --input $demoInput --verbose --model gemini-flash-latest

# Optional OpenAI run
python -m src.main --input $demoInput --provider openai --model gpt-4o
```

While it runs, narrate:
> "The tool loads events,
> batches them at 50 events or 24k characters,
> sends them to the LLM with a strict JSON schema,
> validates the response,
> generates a deterministic report,
> and saves results to SQLite."

When it completes, point out the actual values on screen:
- Status line (success/partial/failed)
- Number of findings and hypotheses
- Confidence value
- Report output location (if you use `--output file`)

### Optional: AWS run (2-3 minutes)

Use AWS CloudTrail JSONL if you have it (converted from the CSV).

```powershell
$awsInput = "data\\sample_aws.jsonl"
python -m src.main --input $awsInput --source aws --verbose --model gemini-flash-latest
python -m src.main --input $awsInput --source aws --provider openai --model gpt-4o
```

While it runs, narrate:
> "This run uses the AWS adapter. It normalizes CloudTrail into the same evidence envelope,
> adds plane tags (control/data/telemetry), groups events by time proximity,
> and batches events at 25 per prompt for stable JSON extraction."

### Optional: GCP run (2-3 minutes)

Use the synthetic JSONL for a fast demo.

```powershell
$gcpInput = "data\\gcp_synthetic_minilab.jsonl"
python -m src.main --input $gcpInput --source gcp --verbose --model gemini-flash-latest
python -m src.main --input $gcpInput --source gcp --provider openai --model gpt-4o
```

While it runs, narrate:
> "This run uses the GCP adapter. It normalizes Audit Logs into the same evidence envelope,
> adds plane tags, and enriches identity/automation signals so the LLM does not guess.
> Evidence includes insertId for GCP provenance."

#### For a full run of 50 events or 24k tokens

```powershell
python -m src.main --input data\evtx_parsed_50 --verbose --model gemini-flash-latest --output file
python -m src.main --input data\evtx_parsed_50 --provider openai --model gpt-4o --output file
```

---

## Demo Script - Act 3: Code Walkthrough (5-7 minutes)

Follow this in order. Keep each stop to 30-60 seconds.

### 1) `src/main.py` - Harness / orchestrator
Open the file and point to the `main()` flow.

Talking points:

- "This is the entrypoint and control plane: parse args, configure logging, then run the pipeline."
- "The pipeline is a straight line: ingest -> normalize -> sanitize -> enrich -> llm_analyze -> validate_output -> report -> persist."
- "Report output is saved to `reports/` and the path is printed, so the demo can always show the file."

What to point at:
- `parse_args()` for CLI options (input path, output mode, model, db).
- `ensure_environment()` for API key checks and DB path setup.
- `main()` for the one-pass orchestration sequence.

### 2) `src/ingest.py` - Evidence-aware ingestion
Open the file and point to `load_events()` and `_load_file_events()`.

Talking points:
- "Every event gets provenance: `source_file`, `record_index`, and `event_id`."
- "That provenance becomes the evidence citations in the final report."
- "There is a file size cap to prevent oversized input in a single file."

What to point at:
- The `records.append(...)` block with provenance fields.
- `MAX_FILE_SIZE_BYTES` as a safety cap.

### 2b) `src/ingest_gcp.py` + `src/gcp_plane_tagging.py` + `src/gcp_enrichment.py` - GCP adapter
Open the files and point to normalization, plane tagging, and enrichment.

Talking points:
- "GCP supports JSON and JSONL audit logs with auto-detection."
- "Normalization produces the same envelope: source_file, record_index, event_id, raw_event."
- "Plane tagging labels control/data/telemetry for context."
- "Enrichment adds actor_kind and automation signals deterministically."

What to point at:
- `normalize_gcp_audit()` in `src/ingest_gcp.py`.
- `tag_plane()` in `src/gcp_plane_tagging.py`.
- `classify_actor_type()` and `compute_automation_confidence()` in `src/gcp_enrichment.py`.

### 3) `src/schemas.py` - Schema contract for the LLM
Open the file and point to `AnalysisOutput`, `Finding`, and `Evidence`.

Talking points:
- "The LLM must conform to this structure. It is our schema contract."
- "Findings always include evidence and severity. Confidence is bounded 0-1."
- "We normalize `event_id` to string for consistency."

What to point at:
- `AnalysisOutput` and its fields.
- `Evidence` with the `field_validator` for `event_id`.

### 4) `src/llm_analyze.py` - Batching, prompt, and retries
Open the file and point to the batch limits and the system prompt.

Talking points:
- "Windows batches cap at 50 events or ~24k characters."
- "AWS batches are smaller (25 events) for stable CloudTrail prompts."
- "The system prompt injects the schema and rules: JSON only, evidence required, no remediation claims."
- "Retries and timeout handling are built in for reliability."

What to point at:
- `MAX_EVENTS_PER_BATCH` and `MAX_PROMPT_CHARS`.
- `SYSTEM_PROMPT`.
- `AWS_SYSTEM_PROMPT`.
- `GCP_SYSTEM_PROMPT` and `_build_gcp_user_prompt()`.
- `_call_with_retry()` and `_parse_llm_content()`.

### 5) `src/security.py` - Policy guardrails
Open the file and point to `PROHIBITED_PATTERNS` and `validate_output()`.

Talking points:
- "We treat the LLM output as untrusted input."
- "This blocks definitive claims, remediation statements, and encoded PowerShell."

What to point at:
- The regex list and the simple scan in `validate_output()`.

### 6) `src/report.py` - Deterministic report generation
Open the file and point to `generate_report()` and `_generate_executive_summary()`.

Talking points:
- "No extra model calls here. The report is deterministic."
- "We dedupe findings and synthesize a clear executive summary."

What to point at:
- `generate_report()` top-level flow.
- `_merge_findings()` and `_dedupe_*()` helpers.

### 7) `src/storage.py` - Persistence / audit trail
Open the file and point to the tables and `save_analysis()`.

Talking points:
- "Every run is stored for auditability: runs, findings, hypotheses, IOCs, and the report text."
- "Run status is normalized to success/partial/failed."

What to point at:
- `_CREATE_TABLE_STATEMENTS`.
- `save_analysis()` and `_derive_run_status()`.

---

## Demo Script - Act 4: Database Persistence (2 minutes)

```powershell
# Recent runs
python -c "import sqlite3; conn=sqlite3.connect('db/analysis.db'); cur=conn.cursor(); cur.execute('SELECT run_id, status, model_used, timestamp FROM analysis_runs ORDER BY timestamp DESC LIMIT 3'); print('Recent runs:'); [print(f'  {r[0][:8]}... | {r[1]} | {r[2]} | {r[3]}') for r in cur.fetchall()]; conn.close()"

# Total findings
python -c "import sqlite3; conn=sqlite3.connect('db/analysis.db'); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM findings'); print(f'Total findings: {cur.fetchone()[0]}'); conn.close()"
```

Narrate:
> "Every run is stored with a run_id,
> status,
> model name,
> and timestamp,
> so analysis is traceable and auditable."

---

## Demo Script - Act 5: Security Highlights (1 minute)

Emphasize:

- `.env` is gitignored to protect API keys.
- SQL inserts are parameterized.
- LLM output is treated as untrusted input (schema + safety validation).

---

## Closing Statement (1 minute)

"ThreatPrism turns raw Windows event logs into structured, evidence-backed findings.

The pipeline is:
> modular,
> validated,
> and auditable,

The AI is used strictly as an assistant, which provides insight, not determinations or actions. I can explain and test each phase independently."

Transition to Q&A:
> "Happy to dive deeper into the architecture, security controls, testing, or how I would scale this."

---

## Optional Deep Dives (pick 1 if time allows)

### A) Ingest + provenance

Open `src/ingest.py`.

Talking points:

- "Each event is wrapped with `source_file`, `record_index`, and `event_id` so findings can cite exact evidence."
- "We skip oversized files to protect memory and keep input predictable."

### B) Schema contract

Open `src/schemas.py`.

Talking points:

- "This is the contract the LLM must follow; it keeps the output machine-validated."
- "Evidence is required for each finding and confidence is bounded 0-1."

### C) LLM batching + prompt rules

Open `src/llm_analyze.py`.

Talking points:

- "We cap batches at 50 events or ~24k characters to control cost and latency."
- "The system prompt injects the schema and strict rules: JSON only, evidence required, no remediation claims."

### D) Guardrails + deterministic reporting

Open `src/security.py` then `src/report.py`.

Talking points:

- "We scan for prohibited language to prevent overconfident or unsafe claims."
- "Reports are deterministic and deduped; no extra model calls after extraction."

---

## Quick Reference Command Cheat Sheet

```powershell
# Activate environment
.venv\Scripts\Activate

# Run with verbose output (15 events)
python -m src.main --input data\evtx_sample --verbose --model gemini-flash-latest
python -m src.main --input data\evtx_sample --provider openai --model gpt-4o

# Dry run (no API call)
python -m src.main --input data\evtx_sample --dry-run

# Output to file
python -m src.main --input data\evtx_sample --output file --model gemini-flash-latest
python -m src.main --input data\evtx_sample --provider openai --model gpt-4o --output file

# AWS run (CloudTrail JSONL)
python -m src.main --input data\sample_aws.jsonl --source aws --verbose --model gemini-flash-latest
python -m src.main --input data\sample_aws.jsonl --source aws --provider openai --model gpt-4o

# GCP run (Audit Logs)
python -m src.main --input data\gcp_synthetic_minilab.jsonl --source gcp --verbose --model gemini-flash-latest
python -m src.main --input data\gcp_synthetic_minilab.jsonl --source gcp --provider openai --model gpt-4o

# Convert Kaggle CSV to JSONL
python scripts/aws_csv_to_jsonl.py data\sample_cloudtrail.csv data\sample_aws.jsonl

# Show help
python -m src.main --help

# Run a test script
python tests/test_phase1a.py

# Query database
python -c "import sqlite3; conn=sqlite3.connect('db/analysis.db'); cur=conn.cursor(); cur.execute('SELECT run_id, status, model_used, timestamp FROM analysis_runs ORDER BY timestamp DESC LIMIT 3'); [print(r) for r in cur.fetchall()]; conn.close()"
```

---

## Anticipated Questions and Answers

### Q: "Why this architecture?"

"Separating phases keeps concerns isolated:
> ingest handles I/O,
> the LLM is only extraction,
> validation enforces safety,
> reporting is deterministic,
> and storage keeps an audit trail.
Which makes it testable and maintainable."

### Q: "How do you handle hallucinations?"

"Three layers:
> schema validation enforces structure,
> security patterns block unsafe claims,
> and evidence requirements prevent unsupported findings.
The AI never takes automated action."

### Q: "How would you scale to 10,000 events?"

> "I would keep batching but parallelize batch calls, add progress reporting, and move storage to Postgres.
> I would also cache repeated patterns for cost control."

### Q: "Why PowerShell for EVTX conversion?"

"PowerShell Get-WinEvent is native and reliable on Windows,
Python EVTX parsing can be inconsistent.
I use `scripts/prep_evtx.ps1` once and then operate on JSONL."

### Q: "How did you test it?"

"There are targeted test scripts in `tests/` and a full-flow run with a mocked LLM.
For example:
> `tests/test_phase1a.py` checks schema and guardrails,
> and `tests/test_full_flow.py` exercises the CLI pipeline end-to-end."

### Q: "Show me a quick change."

"I would add MITRE ATT&CK technique IDs to each finding so the report shows standardized mappings."

What you change (exact files):

1) `src/schemas.py` (location: `class Finding`)

Add a new optional list field so it is part of the schema contract:

```python
class Finding(BaseModel):
    """Concrete observation identified within the analyzed events."""

    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    evidence: List[Evidence] = Field(..., min_length=1)
    mitre_techniques: List[str] = Field(default_factory=list)
```

2) `src/llm_analyze.py` (location: `SYSTEM_PROMPT` -> RULES)

Add this line to the rules list:

```text
8. When possible, include MITRE ATT&CK technique IDs (e.g., T1047) in each finding's
   mitre_techniques list; use an empty list when unknown.
```

3) `src/report.py` (location: `_format_findings`, after Summary and before Evidence)

Render the MITRE list in the report output:

```python
        if finding.mitre_techniques:
            sections.append(f"MITRE: {', '.join(finding.mitre_techniques)}")
        else:
            sections.append("MITRE: (none)")
```

How you show it works (fast demo):

- Run a 15-event analysis.
- Point to the new `MITRE:` line under each finding in the report output.

```python
python -m src.main --input data\evtx_sample --verbose --model gemini-flash-latest
python -m src.main --input data\evtx_sample --provider openai --model gpt-4o
```

> The only caveat is this is still "best effort"
> - the model may leave MITRE empty.
> "If it's unknown, it stays empty."

---

## Practice Schedule

3 days before:
- Full dry run with a timer (aim for 12 minutes)
- Practice the architecture explanation without notes

1 day before:
- Final dry run
- Verify environment and dataset

Day of:
- 30-minute pre-interview test run
- Keep the architecture diagram and this guide open

You have a real system, clear guardrails, and an auditable pipeline. Keep it crisp and confident.
