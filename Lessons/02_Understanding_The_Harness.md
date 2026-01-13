# Lesson 02: Understanding The Harness - How Files Connect

This lesson explains the harness (orchestrator) and how Python files connect through imports.

---

## What is the "Harness"?

Plain English: the harness is the backbone that:
1. Imports functions from other files
2. Calls them in the correct order
3. Connects every phase into one pipeline

In this project: the harness is `src/main.py`.

Think of it like a conductor:
- Ingest, LLM analysis, security, and storage each play a part
- `main.py` brings them in at the right time

---

## How Python Files Talk to Each Other

Import pattern:
```python
from [package].[module] import [function_or_class]
```

Example:
```python
from src.ingest import load_events
```

Translation:
- `src` = folder
- `ingest` = file name
- `load_events` = function

---

## The Real Imports in `src/main.py` (current)

Open `src/main.py` and look near the top. These are the core imports the harness uses:

```python
from src.llm_analyze import analyze_events, run_semantic_judge
from src.ops.ops_context import create_ops_context
from src.report import generate_report
from src.schemas import AnalysisOutput
from src.security import validate_output, validate_semantic_output
from src.storage import initialize_database, save_analysis
```

### What each import does

**LLM analysis**
```python
from src.llm_analyze import analyze_events, run_semantic_judge
```
- `analyze_events()` sends batched events to the LLM
- `run_semantic_judge()` is optional (enabled via `--semantic-judge`)

**Ops harness**
```python
from src.ops.ops_context import create_ops_context
```
- Creates `run_id` and writes `runs/<run_id>/run_log.jsonl` and `metrics.json`

**Report**
```python
from src.report import generate_report
```
- Builds the deterministic report text (no model calls)

**Schema**
```python
from src.schemas import AnalysisOutput
```
- Pydantic contract for LLM output structure

**Security and validation**
```python
from src.security import validate_output, validate_semantic_output
```
- `validate_output()` enforces policy guardrails
- `validate_semantic_output()` checks evidence references match events

**Storage**
```python
from src.storage import initialize_database, save_analysis
```
- Creates SQLite tables and persists analysis results

---

## Adapter Imports (done inside the harness)

The harness imports source-specific adapters inside the flow, based on `--source`:

- Windows: `from src.ingest import load_events`
- AWS: `from src.ingest_aws import ingest_cloudtrail`
- GCP: `from src.ingest_gcp import load_gcp_log_file, normalize_gcp_audit`

This keeps unused adapters from loading when not needed.

---

## The Harness in Action (current pipeline)

This is the actual sequence in `main()` (simplified but accurate):

```python
def main() -> int:
    run_id = uuid4()
    args = parse_args()
    configure_logging(args.verbose, args.debug, run_id)
    ops = create_ops_context(run_id)

    ensure_environment(args)
    decision, reason = detect_source(args.input)

    # Ingest + normalize
    events = ingest_adapter(decision, args.input)

    # Normalize (AWS correlation if needed)
    events = normalize_if_needed(events)

    # Sanitize (prompt firewall)
    events = sanitize_events(events)

    # Enrich (GCP only)
    events = enrich_if_gcp(events)

    if args.dry_run:
        return 0

    initialize_database(args.db)
    analysis_data = analyze_events(events, model=args.model, provider=args.provider)

    # Validate output (schema + policy + semantic + optional judge)
    analysis = AnalysisOutput.model_validate(analysis_data)
    validate_output(...)
    validate_semantic_output(...)
    if args.semantic_judge:
        run_semantic_judge(...)

    report_text = generate_report(analysis)
    save_analysis(..., report_text=report_text)
```

Key idea: the harness is responsible for **order**, **error handling**, and **run artifacts**.

---

## Visual Map (updated)

```
src/main.py (the harness)
|
|-- Ingest adapters (Windows/AWS/GCP)
|-- Normalize (envelope + AWS correlation)
|-- Sanitize (prompt firewall)
|-- Enrich (GCP deterministic signals)
|-- LLM Analyze
|-- Validate Output (schema + policy + semantic + optional judge)
|-- Report (deterministic)
|-- Persist (SQLite)
`-- Ops artifacts (runs/<run_id>/...)
```

---

## Key Takeaways

1) The harness controls the pipeline order.  
2) Imports show the exact dependencies between files.  
3) Source adapters are loaded on demand.  
4) Validation is layered (schema + policy + semantic + optional judge).  
5) Ops artifacts prove what happened on each run.

---

## Exercise: Trace a Real Import

Pick one import and trace it:

Example: `analyze_events`
1. Find it in `src/main.py`
2. Ctrl+Click to open `src/llm_analyze.py`
3. Locate `analyze_events()` and read the first 20 lines
4. Explain what it expects as input and what it returns

---
## Answer to 4. 

I'll explain this code in simple terms! This file is essentially a translator between security logs and AI assistants.

### What This Code Does (Big Picture)
Think of this as a security guard assistant that reads through security camera footage (logs) and summarizes what happened. Instead of a human reading thousands of log entries, an AI (like ChatGPT or Google Gemini) does it.

### The Main Function: analyze_events
This is the "boss" function starting at line 170. Here's what it does step-by-step:

1. Takes In Security Events

events: List[Dict[str, Any]]
Gets a list of security log entries (like login attempts, file access, API calls)
Each event is a dictionary (think: a box of information with labels)

2. Figures Out What Type of Logs

aws_events = [e for e in events if ...]gcp_events = [e for e in events if ...]
Checks if these are Windows logs, Amazon AWS logs, or Google Cloud logs
Each type needs different instructions for the AI (like different languages)

3. Splits Into Batches

batches = build_aws_batches(events, MAX_EVENTS_PER_BATCH)
Why? AIs can't read unlimited text at once (like how you can't memorize a whole book in one go)
Splits events into smaller chunks (batches) of 50 or fewer events
Like feeding a giant meal in bite-sized portions

4. Sends Each Batch to the AI

batch_result = _process_aws_batch(batch["events"], model, provider, ops)
For each batch, it sends the logs to the AI with specific instructions
The instructions are in those SYSTEM_PROMPT variables at the top
AI responds with structured findings (threats found, suspicious activities, etc.)

5. Combines All Results

merged_result = _merge_batch_results(merged_result, batch_result)
Takes all the AI's responses from different batches
Merges them into one comprehensive report
Returns the final analysis
The Different "Instruction Manuals" (Prompts)
The code has 3 different sets of instructions for the AI:

SYSTEM_PROMPT - For Windows security logs (focuses on user behavior, file access)
AWS_SYSTEM_PROMPT - For Amazon cloud logs (focuses on permissions, identity theft)
GCP_SYSTEM_PROMPT - For Google cloud logs (focuses on service accounts, automation)

Each tells the AI:

- What format to respond in (JSON only - structured data)
- What to look for (suspicious patterns)
- How to cite evidence (which log entry it found something in)
- Not to make things up or speculate without evidence

### Why This Matters
Imagine you're a security analyst drowning in 10,000 log entries.
This code:

✅ Automatically reads all logs
✅ Identifies potential security threats
✅ Provides evidence for each finding
✅ Suggests what to investigate next
✅ Does it in minutes instead of days

### In one sentence

This code feeds security logs to an AI, gets back a structured report of potential threats, and handles all the complexity of talking to different AI services and log formats.
---

## Interview Talking Points (updated)

> "I use a modular architecture. `main.py` is the harness: it routes inputs to the right adapter, sanitizes untrusted content, enriches GCP signals, calls the LLM, validates output with schema and policy checks, and optionally runs a semantic judge. It also writes ops artifacts per run. This keeps the pipeline deterministic, testable, and auditable."

---

## Next Steps

1. Open `src/main.py` and read the full `main()` flow.
2. Trace one adapter (Windows/AWS/GCP) end-to-end.
3. Move to Lesson 03 (Phase 1: Ingest).
