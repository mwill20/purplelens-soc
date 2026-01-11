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

## Interview Talking Points (updated)

> "I use a modular architecture. `main.py` is the harness: it routes inputs to the right adapter, sanitizes untrusted content, enriches GCP signals, calls the LLM, validates output with schema and policy checks, and optionally runs a semantic judge. It also writes ops artifacts per run. This keeps the pipeline deterministic, testable, and auditable."

---

## Next Steps

1. Open `src/main.py` and read the full `main()` flow.
2. Trace one adapter (Windows/AWS/GCP) end-to-end.
3. Move to Lesson 03 (Phase 1: Ingest).
