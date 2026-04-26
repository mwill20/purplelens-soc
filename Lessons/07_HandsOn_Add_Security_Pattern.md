# Lesson 07: Hands-On - Add a Custom Security Pattern

This lesson adds a new output guardrail to `src/security.py`, updates tests, and explains the trade-offs.

Prerequisites: Lessons 01-06.

---

## Why this matters

ThreatPrism treats LLM output as untrusted input. The prompt firewall sanitizes input logs before the LLM, but we still need output guardrails in case the model recommends unsafe actions. This lesson extends those guardrails.

---

## Step 0: Create a practice branch

```powershell
git status
git checkout -b lessons-practice
```

If your default branch is `main` instead of `master`, replace the branch name accordingly when you merge later.

---

## Step 1: Threat model a new output risk

Pick a concrete risk that could show up in `recommended_next_steps`.

Example risk:
LLM suggests disabling security tooling to "speed up" investigation.

Example malicious recommendation:
```
Disable Windows Defender before running the scan.
```

Why this matters:
Security tools should never be disabled based on LLM output.

---

## Step 2: Add a guardrail pattern

Open `src/security.py` and find `PROHIBITED_PATTERNS`.

Add this new pattern (with a short comment):

```python
PROHIBITED_PATTERNS = [
    # ... existing patterns ...
    r"(?i)(disable|turn off|stop).*(defender|antivirus|edr)",  # NEW: block disabling security tooling
]
```

Notes:
- `(?i)` makes it case-insensitive.
- This focuses on explicit disablement language.

---

## Step 3: Update tests

Open `tests/test_new_pattern.py` and add two new tests:

```python
def test_guardrail_blocks_disable_security_tools() -> None:
    response_text = _payload(["Disable Windows Defender before running the scan."])
    is_valid, _ = validate_output(response_text)
    assert not is_valid


def test_guardrail_allows_security_review() -> None:
    response_text = _payload(["Review Defender alerts for the affected host."])
    is_valid, _ = validate_output(response_text)
    assert is_valid
```

---

## Step 4: Run the tests

```powershell
pytest tests/test_new_pattern.py -q
```

Expected:
- The disablement recommendation is blocked.
- The benign review recommendation passes.

---

## Step 5: Understand where this runs in the pipeline

In `src/main.py`, the output validation phase happens after the LLM step:
1. `AnalysisOutput.model_validate(...)` (schema)
2. `validate_output(...)` (policy guardrails)
3. `validate_semantic_output(...)` (evidence mapping)
4. `run_semantic_judge(...)` (optional, if `--semantic-judge` is set)

If any of these fail, the run is marked as `validation_error` and the report is generated in a degraded state.

---

## Trade-offs to explain in an interview

- **False positives**: A benign instruction like "stop a process" could match if phrased poorly.
- **False negatives**: Indirect phrasing ("pause security agent") might not match.

Why this pattern is acceptable for the lesson:
It blocks explicit disablement language while keeping review steps safe.

---

## Interview talking points (short version)

> "We already sanitize untrusted logs before the LLM. This change adds an output guardrail so the model can?t recommend disabling security tooling. I added a focused pattern, updated unit tests, and validated it in the policy stage. It?s a trade-off between false positives and coverage, but it materially reduces risk in analyst workflows."

---

## Next steps

Move to Lesson 08 (Customize Report Format).
