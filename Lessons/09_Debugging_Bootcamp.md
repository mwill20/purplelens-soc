# Lesson 09: Debugging Bootcamp

This lesson teaches you how to troubleshoot issues across all phases of your pipeline. You will learn to read error messages, diagnose problems, and fix common issues with a repeatable method.

Prerequisites: Complete Lessons 01-06 (core pipeline understanding)

---

## Code Modification Note

This lesson is diagnostic. You are learning to read and fix errors, not making permanent changes. If you want to add temporary debug logging during practice, work on your lessons-practice branch.

Optional: Create or switch to the practice branch:

```powershell
# If you do not have a practice branch yet
git checkout -b lessons-practice

# If you already have one from Lessons 07-08
git checkout lessons-practice
```

You can also read through this lesson without modifying anything.

---

## Learning Goals

By the end of this lesson, you will be able to:
- Read Python error messages and tracebacks
- Diagnose issues across all five pipeline phases
- Use logging effectively for debugging
- Fix common errors (file not found, API failures, validation errors)
- Debug like a senior engineer in interviews
- Explain your debugging method step by step

---

## The Debugging Mindset

Junior approach:
- "Its broken"
- Randomly change things hoping it works
- Ask for help immediately

Senior approach:
- "What specifically failed?"
- Read the error message carefully
- Form a hypothesis, test it, iterate
- Ask targeted questions with context

This lesson teaches the senior approach.

---

## Part 1: Reading Python Errors

### Anatomy of a Traceback

Example (missing input directory):

```
Traceback (most recent call last):
  File "C:\\Projects\\Bespin AI Security Analyst Assistant\\src\\main.py", line 85, in main
    events = load_events(args.input)
  File "C:\\Projects\\Bespin AI Security Analyst Assistant\\src\\ingest.py", line 16, in load_events
    raise FileNotFoundError("Input path does not exist or is not a directory: data\\evtx_parsed")
FileNotFoundError: Input path does not exist or is not a directory: data\\evtx_parsed
```

Read bottom to top:
1) Error type and message: FileNotFoundError, missing directory
2) Where it happened: src/ingest.py in load_events
3) Call chain: src/main.py called load_events

### Debugging Strategy for This Error

Step 1: Understand what failed
- The input directory does not exist or is not a directory.

Step 2: Form hypotheses
- The path is wrong
- The directory was not created

Step 3: Test hypotheses

```powershell
Test-Path "data\\evtx_parsed"
Get-ChildItem "data\\evtx_parsed"
```

Step 4: Fix the issue

```powershell
# Create the directory (and then generate JSONL files)
New-Item -ItemType Directory -Path "data\\evtx_parsed" -Force
```

Step 5: Re-run and verify

```powershell
python -m src.main --input data\\evtx_parsed --model gpt-4o
```

---

## Part 2: Common Errors by Phase

### Phase 1: Ingest Errors

#### Error 1: FileNotFoundError

```
FileNotFoundError: Input path does not exist or is not a directory: data\\evtx_parsed
```

Fix:
- Verify the path
- Ensure the directory exists

#### Error 2: No JSONL Files Found

```
ValueError: No JSONL files found in data\\evtx_parsed
```

Fix:
- Confirm JSONL files are present
- Re-run the EVTX conversion step

#### Error 3: JSONDecodeError (malformed input)

Your ingest logic skips malformed lines. If all lines are bad, you will get:

```
ValueError: No valid events were loaded from the provided directory
```

Debug tips:

```powershell
Get-Content data\\evtx_parsed\\sample.jsonl -Head 5
Get-Content data\\evtx_parsed\\sample.jsonl -Tail 5
```

#### Error 4: File Too Large

Files larger than 10 MB are skipped with a warning, and you will fail only if no valid events remain:

```
Skipping <file> because it exceeds 10 MB limit
```

Fix options:
- Split the file into smaller JSONL chunks
- Adjust MAX_FILE_SIZE_BYTES in src/ingest.py (if appropriate)

---

### Phase 2: LLM Analysis Errors

#### Error 5: Authentication Error

```
openai.AuthenticationError: Error code: 401 - Incorrect API key provided
```

Fix:
```powershell
$env:OPENAI_API_KEY
$env:OPENAI_API_KEY = "sk-proj-YOUR_KEY"
```

#### Error 6: Rate Limit

```
openai.RateLimitError: Error code: 429 - Rate limit exceeded
```

Fix:
- Let retry logic handle it
- Reduce batch size in src/llm_analyze.py
- Check your OpenAI rate limits

#### Error 7: Unsupported response_format

```
Invalid parameter: 'response_format' of type 'json_object' is not supported with this model.
```

Fix:
- Use a JSON-mode compatible model such as gpt-4o or gpt-4o-mini

#### Error 8: Malformed JSON from the LLM

```
LLM returned malformed JSON.
```

Debug tip:
Add temporary logging in src/llm_analyze.py to print the raw response before parsing.

---

### Phase 3: Validation Errors

#### Error 9: Pydantic ValidationError

Example (invalid severity or confidence):

```
pydantic.ValidationError: 2 validation errors for AnalysisOutput
findings.0.severity
  Input should be 'info', 'low', 'medium', 'high', or 'critical'
confidence
  Input should be less than or equal to 1
```

Fix:
- Tighten the SYSTEM_PROMPT to enforce allowed values
- Check the LLM output and adjust prompt or validation

#### Error 10: Security Validation Failed

```
Prohibited pattern detected: (?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}
```

Fix:
- Review the offending recommendation or output
- Adjust patterns in src/security.py if it is a false positive

---

### Phase 4: Report Generation Errors

#### Error 11: UnicodeEncodeError

```
UnicodeEncodeError: 'charmap' codec can't encode character
```

Fix:
- Use UTF-8 output

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

- Or use `--output file`

---

### Phase 5: Database Errors

#### Error 12: Database Locked

```
sqlite3.OperationalError: database is locked
```

Fix:
- Close any DB browsers using db/analysis.db

#### Error 13: Integrity Error

```
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

Fix:
- Ensure the parent run is inserted before child records (already handled in src/storage.py)

---

## Part 3: Debugging Tools and Techniques

### Technique 1: Logging

Use the built-in logging and the CLI verbose flag:

```powershell
python -m src.main --input data\\evtx_parsed --model gpt-4o --verbose
```

To add temporary logging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Loading events")
```

### Technique 2: Interactive Debugging (pdb)

```python
import pdb; pdb.set_trace()
```

Useful commands:
- n (next)
- s (step)
- c (continue)
- p <var>
- l (list)
- q (quit)

### Technique 3: Validate Data at Each Phase

```python
assert isinstance(events, list)
assert events, "No events to analyze"
```

### Technique 4: Test with Minimal Data

Create a minimal directory and file:

```powershell
New-Item -ItemType Directory -Force data\\test_minimal
'{"Event":{"System":{"EventID":4624}}}' | Out-File data\\test_minimal\\sample.jsonl -Encoding utf8
python -m src.main --input data\\test_minimal --model gpt-4o --dry-run
```

### Technique 5: Read Tracebacks Bottom Up

Always start with the last line (error message), then move up to identify the code line and call chain.

---

## Interview Explanation: Debugging Methodology

Use a structured story:

Situation:
- "During a run, the pipeline failed with an unsupported response_format error."

Task:
- "Identify the cause and fix it without changing core logic."

Action:
- "I traced the error to the model configuration, verified that json_object requires a compatible model, and re-ran with gpt-4o."

Result:
- "The pipeline completed successfully, and I documented the model compatibility requirement."

---

## Practice Exercises

1) Reduce file size limit temporarily
- Edit MAX_FILE_SIZE_BYTES in src/ingest.py to a very small number, run the pipeline, then revert.

2) Add logging in src/main.py
- Log the event count after ingest, and validate the number is expected.

3) Debug missing API key
- Unset OPENAI_API_KEY, run the pipeline, observe the error, then fix it.

---

## Quick Reference: Error Cheat Sheet

| Error Type | Likely Phase | Common Cause | Quick Fix |
|-----------|--------------|--------------|-----------|
| FileNotFoundError | Phase 1 | Wrong path or missing directory | Test-Path, create directory |
| ValueError (No JSONL files) | Phase 1 | Empty input directory | Add JSONL files |
| JSONDecodeError | Phase 1 or 2 | Invalid JSON input or LLM output | Inspect file or raw response |
| AuthenticationError | Phase 2 | Missing or invalid API key | Set OPENAI_API_KEY |
| RateLimitError | Phase 2 | Too many API calls | Retry or reduce batch size |
| ValidationError | Phase 3 | LLM output schema mismatch | Update prompt or validators |
| UnicodeEncodeError | Phase 4 | Console encoding issue | Use UTF-8 or file output |
| OperationalError | Phase 5 | Database locked | Close DB tools |

---

## Next Steps

Continue with:
- Lesson 10: Database Deep Dive
- Lesson 11: Interview Q and A Practice
