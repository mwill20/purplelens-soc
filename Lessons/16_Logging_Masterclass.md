# Lesson 16: Logging Masterclass (PurpleLens)

This lesson is a complete guide to logging in the PurpleLens project. You will learn how logging is configured, how to read logs, how to add safe log statements, and how to use logs for debugging and forensic traceability.

Prerequisites: Lesson 09 (Debugging Bootcamp) or Lesson 15 (Debugging Project Lab).

---

## Code Modification Note

Some exercises add or tweak log statements. Use a practice branch so you can experiment safely.

```powershell
# If you do not have a practice branch yet
git checkout -b lessons-practice

# If you already have one
git checkout lessons-practice
```

---

## Learning Goals

By the end of this lesson, you will be able to:
- Explain how logging is configured in PurpleLens
- Control verbosity with `--verbose` and `--debug`
- Add safe, useful log statements without leaking sensitive data
- Read run logs to trace a single pipeline execution end-to-end
- Describe logging best practices in an interview

---

## Part 1: Logging Architecture in This Project

### Where logging is configured
Open [src/main.py](../src/main.py) and find `configure_logging()`.

Key points:
- Console and file handlers have separate levels.
- Console shows warnings by default, info with `--verbose`, debug with `--debug`.
- File logs default to info, and only include debug when `--debug` is set.

Why this matters:
- Console is for quick feedback.
- File logs are the durable audit trail.
- Debug is opt-in to reduce sensitive data exposure.

### Log format
The formatter is:
```
%(asctime)s [%(levelname)s] [%(name)s] %(message)s
```

This gives you:
- Timestamp
- Severity level
- Logger name (phase)
- Message

---

## Part 2: Logging Levels (What to Use and When)

Use this mental model:
- DEBUG: Developer-only details, safe metadata only
- INFO: Normal operations and high-level progress
- WARNING: Non-fatal issues, recoverable conditions
- ERROR: Run failed or a major component failed

Project examples:
- `src.ingest`: uses DEBUG for per-file/per-event details, INFO for totals
- `src.llm_analyze`: DEBUG for prompt sizes and response hashes, INFO for batch counts
- `src.security`: DEBUG for policy checks, ERROR for violations

---

## Part 3: Running the Pipeline With Different Log Levels

Run with default logging (warnings only on console):

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest
```

Run with verbose logging (info on console):

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --verbose
```

Run with debug logging (debug on console and in logs):

```powershell
python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --debug
```

What to observe:
- The log file path is printed at the end of each run.
- Debug logs include metadata like LLM response length and hash.

---

## Part 4: How to Read a Run Log

Use this checklist:
1) Find the run header in the first few lines (model, provider, input path).
2) Identify each phase by logger name:
   - `src.ingest` (ingestion)
   - `src.llm_analyze` (LLM analysis)
   - `src.security` (validation)
   - `src.report` (report generation)
   - `src.storage` (database persistence)
3) Look for the first WARNING or ERROR.
4) Read upward and downward to see the context around that line.

---

## Part 5: Logging Best Practices (Security Focus)

Do:
- Log metadata, not raw content.
- Use stable identifiers: lengths, hashes, counts, run IDs.
- Keep debug logs opt-in.
- Avoid secrets, access tokens, or raw payloads.

Do not:
- Log raw LLM responses.
- Log full event payloads unless explicitly required.
- Log API keys or secrets.

This project already follows this:
- LLM responses are logged by length and hash only.
- Debug logs are opt-in with `--debug`.

---

## Part 6: Hands-On - Add a Safe Log Statement

Goal: add a single log line that improves traceability without leaking data.

Task: In [src/ingest.py](../src/ingest.py), add a log line that captures:
- total events loaded
- number of files scanned

Look for:
```python
logger.info("Loaded %d events from %s files", len(events), len(jsonl_files))
```

This is already present and is a perfect example of safe logging.

Reflection:
- It is high value for debugging.
- It contains no sensitive data.
- It scales to large inputs.

---

## Part 7: Structured Logging (Conceptual)

In `src/main.py`, the code uses:
```python
LOGGER.info(
    "source_detect",
    extra={"source": decision, "reason": reason, "input": str(args.input)},
)
```

By default, `extra` fields are not shown in the format.

Why this matters:
- If you want structured logs, you need a formatter that includes those fields
  or you need a JSON logger.
- For this project, a simple message format is enough, but you now know where
  to extend it in the future.

---

## Part 8: Mini Lab - Correlate a Run

Goal: trace one run end-to-end using logs only.

Steps:
1) Run:
   ```powershell
   python -m src.main --input data\evtx_sample --provider gemini --model gemini-flash-latest --verbose
   ```
2) Open the newest log in `logs/`.
3) Write down:
   - run id
   - source detection decision
   - event count
   - report file path

This is how you prove you can trace pipeline state from logs alone.

---

## Interview Story Template (Logging Focus)

Situation:
- "The pipeline failed intermittently, and we needed a reliable audit trail."

Task:
- "Improve logging so we could isolate failures without storing sensitive data."

Action:
- "I set debug logging to opt-in, kept file logs at info by default, and
  logged stable metadata like event counts and LLM response hashes instead
  of raw content."

Result:
- "We could correlate runs end-to-end while reducing data exposure risk."

---

## Key Takeaways

- Logging is a safety feature, not just a debugging tool.
- Default logs should be useful but low risk.
- Debug logs should add insight without leaking content.
- You can trace a full run with log timestamps and phase names.

---

## Next Steps

Continue with:
- Lesson 10: Database Deep Dive
- Lesson 11: Interview Q and A Practice
