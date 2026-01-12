# Lesson 20: Jailbreak Hardening Lab (Replay Harness)

Time: 20-30 minutes

Goal: Run the jailbreak harness against our prompts/policies, review results, and decide on guardrail updates. No code changes to ingestion/output; this is a replay/measurement exercise.

---

## Prerequisites
- Repo setup with dependencies installed.
- LLM provider key set (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
- Familiarity with Lesson 01 (Architecture) and Lesson 02 (Harness).

---

## Why this matters
Jailbreak attempts evolve. A replay harness lets you:
- Measure prompt/policy resilience.
- Track success/failure per variant.
- Adjust guardrails deliberately (no auto self-heal).

---

## What you’ll use
- Harness script: `scripts/jailbreak_harness.py`
- Corpus: `data/redteam/jailbreak_prompts.jsonl`
- Outputs: `runs/<run_id>/jailbreak_results.json`, `runs/<run_id>/run_log.jsonl`, `runs/<run_id>/metrics.json` (fields `jailbreak_attempts`, `jailbreak_successes`).

---

## Hands-on steps

### Step 1: Run the harness (Gemini default)
```powershell
python scripts/jailbreak_harness.py --prompts data/redteam/jailbreak_prompts.jsonl --provider gemini --model gemini-flash-latest
```
```bash
python scripts/jailbreak_harness.py --prompts data/redteam/jailbreak_prompts.jsonl --provider gemini --model gemini-flash-latest
```

Expected console output:
```
Jailbreak harness complete. Attempts=X, successes=Y
Results written to runs/<run_id>/jailbreak_results.json
Ops artifacts written to runs/<run_id>
```

### Step 2: Inspect results
```powershell
Get-Content runs\<run_id>\jailbreak_results.json
Get-Content runs\<run_id>\metrics.json
```
```bash
cat runs/<run_id>/jailbreak_results.json
cat runs/<run_id>/metrics.json
```

### Step 3: Filter failures
```powershell
Get-Content runs\<run_id>\jailbreak_results.json | ConvertFrom-Json | % { $_.details } | Where-Object { -not $_.guardrail_holds } | Select-Object index,prompt_excerpt,reason
```
```bash
python - <<'PY'
import json,sys
from pathlib import Path
run_dir = Path("runs")
latest = max(run_dir.iterdir(), key=lambda p: p.stat().st_mtime)
details = json.loads((latest/"jailbreak_results.json").read_text(encoding="utf-8"))["details"]
for d in details:
    if not d["guardrail_holds"]:
        print(f"{d['index']}: {d['prompt_excerpt'][:120]} ... | reason={d['reason']}")
PY
```

### Step 4: Decide actions (manual)
- If `jailbreak_successes` > 0: review failed prompts, adjust prompts/policy/regex as needed.
- If all hold: record the run_id and metrics for baseline.

---

## Interview/talk track
> "We run a jailbreak replay harness against our prompts/policies. It measures attempts vs successes and writes a JSON summary plus metrics. We don’t auto self-heal; humans review failed variants and update guardrails deliberately. This keeps hardening reproducible and auditable."

---

## Evidence checklist
- Harness run completes (exit code 0).
- `runs/<run_id>/jailbreak_results.json` exists with attempts/successes.
- `metrics.json` includes `jailbreak_attempts` and `jailbreak_successes`.
- Failures (if any) are listed with reasons.

---

## Next steps
- If failures exist: update prompts/policy/regex and rerun the harness.
- If clean: keep the run as a baseline; consider expanding the corpus over time.
