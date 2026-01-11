# Lesson: AIOps for Security Engineers - Operability First (PurpleLens Anchor)

Time: 45-60 minutes

Goal: Understand AIOps in plain English, then apply it to a CLI pipeline (PurpleLens) with real run artifacts and failure drills.

---

## Branch note (recommended for new work)

If you are implementing or extending AIOps in this repo, create a branch:
```bash
git checkout -b enhancement/aiops-v1
```

---

## Section 1 - What AIOps is (plain language)

**Definition:** AIOps is operations + telemetry + automation that reduces time-to-detect and time-to-recover.

**What it is NOT:**
- Not a single vendor product.
- Not auto-remediation everywhere.
- Not "let the model decide."

Think of AIOps as the system that makes your AI tool run, debug, and recover under pressure.

---

## Section 2 - Why AIOps matters for AI systems

AI adds:
- nondeterminism (outputs vary),
- cost variability (tokens, batch size),
- new failure modes (schema errors, refusals, API timeouts).

Security systems require auditability and evidence. AIOps makes failures visible, traceable, and explainable.

---

## Section 3 - The Thin AIOps Spine

Core flow:

```
OBSERVE -> DETECT -> DIAGNOSE -> RESPOND (safely)
```

**Observe:** structured logs + metrics + artifacts.  
**Detect:** find anomalies (errors, spikes, missing outputs).  
**Diagnose:** identify stage + root cause with evidence.  
**Respond:** recover safely (no destructive automation).

Minimal viable implementation = run_id + JSONL logs + metrics.json + a runbook.

---

## Section 4 - PurpleLens mapping (anchor example)

PurpleLens is CLI-first, so a **request = one CLI run**.

**Correlation ID:** `run_id` (one run, one folder, one timeline)

**Pipeline stages (examples):**
ingest -> normalize -> sanitize -> enrich -> llm_analyze -> validate_output -> report -> persist

**AIOps mapping table:**

| AIOps concept | PurpleLens implementation |
| --- | --- |
| Observe | `runs/<run_id>/run_log.jsonl`, `runs/<run_id>/metrics.json` |
| Detect | `error_count`, `top_errors`, exception logs |
| Diagnose | `stage` + `error_type` in run_log.jsonl |
| Respond | Fix input / rerun; no auto-remediation |

---

## Section 5 - Defensive patterns (prompt injection)

Logs are untrusted input. The pipeline now includes a prompt firewall that:
- Detects instruction-like strings inside logs.
- Redacts unsafe content before it reaches the LLM.
- Quarantines events when necessary.

Operational proof lives in artifacts:
- `run_log.jsonl` sanitize stage shows counts + affected event IDs.
- `metrics.json` includes `prompt_injection_hits`, `events_sanitized`, `events_quarantined`.

---

## Section 6 - Build steps (hands-on)

### Repo sample artifacts (included for readers)

The repo includes two sample run artifact sets so readers can follow along without generating their own runs:
- `Lessons/LESSON_ASSETS/run_samples/good_run/`
- `Lessons/LESSON_ASSETS/run_samples/broken_run/`

The good_run sample includes an `llm_analyze` stage and token totals so you can see the full AIOps signal path without running the model.

If you want to refresh these samples later, copy from `runs/<run_id>/` into those folders.

### Step 1: Run PurpleLens

PowerShell:
```powershell
python -m src.main --input data/evtx_parsed --dry-run
```

bash:
```bash
python -m src.main --input data/evtx_parsed --dry-run
```

### Step 2: Locate run artifacts

The CLI prints:
```
Ops artifacts written to runs/<run_id>
```

PowerShell (latest run):
```powershell
$latest = Get-ChildItem runs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host $latest.FullName
```

bash:
```bash
ls -t runs | head -n 1
```

### Step 3: Inspect logs and metrics

PowerShell:
```powershell
Get-Content runs/<run_id>/run_log.jsonl | Select-Object -First 3
Get-Content runs/<run_id>/metrics.json
```

bash:
```bash
head -n 3 runs/<run_id>/run_log.jsonl
cat runs/<run_id>/metrics.json
```

### Step 4: Generate evidence artifact

```powershell
python scripts/evidence_artifact.py --run-id <run_id>
```

```bash
python scripts/evidence_artifact.py --run-id <run_id>
```

This writes `runs/<run_id>/evidence.txt`.

---

## Section 7 - Failure Drill #1 (hands-on)

### Good run baseline

```powershell
python -m src.main --input data/evtx_parsed --dry-run
```

### Break it intentionally (bad path)

```powershell
python -m src.main --input data/does_not_exist
```

Optional (auto-run both good and broken runs):
```powershell
python scripts/failure_drill_1.py --execute
```

### Diagnose using artifacts

PowerShell:
```powershell
Get-Content runs/<run_id>/run_log.jsonl | Select-String "exception"
Get-Content runs/<run_id>/metrics.json
Get-Content runs/<run_id>/what_broke.md
```

bash:
```bash
grep \"exception\" runs/<run_id>/run_log.jsonl
cat runs/<run_id>/metrics.json
cat runs/<run_id>/what_broke.md
```

You should see:
- `stage` and `error_type`
- `error_count` > 0
- a `what_broke.md` mini-postmortem

---

## Practical application (AIOps on this project)

1) Walk the lesson and fill the RCA using the broken run:
- Use `Lessons/LESSON_ASSETS/run_samples/broken_run/what_broke.md`
- Fill out `Lessons/LESSON_ASSETS/rca_template.md` with the same failure

2) Run a clean dry-run:
```powershell
python -m src.main --input data/evtx_parsed --dry-run
```

3) Run the failure drill:
```powershell
python scripts/failure_drill_1.py --execute
```

4) Open the run artifacts for the broken run and fill out:
- `runs/<run_id>/what_broke.md`
- `Lessons/LESSON_ASSETS/rca_template.md`

5) Generate evidence:
```powershell
python scripts/evidence_artifact.py --run-id <run_id>
```

This gives you real AIOps experience on PurpleLens: run correlation, failure diagnosis, and evidence capture.

---

## Full run (LLM stage capture)

To capture LLM stages in `run_log.jsonl`, run a non-dry-run:

```powershell
# Requires OPENAI_API_KEY or GEMINI_API_KEY
python -m src.main --input data/evtx_parsed --provider openai --model gpt-4o
```

When complete, check the run artifacts for `llm_analyze` stage entries and token/cost estimates. Token totals are estimated from prompt/response size. Cost is estimated for OpenAI models; Gemini runs report 0.0 unless pricing is configured.

---

## Section 8 - Generalize beyond PurpleLens

Apply the same spine to:

**APIs:** request_id in logs, latency and error metrics.  
**Async pipelines:** job_id + queue depth + retry counts.  
**Agent systems:** tool-call latency + refusal spikes.  
**SOC workflows:** alert_id + triage time + escalation rate.

Examples:
- agent tool timeout -> stage=tool_call, error_type=TimeoutError  
- prompt injection attempt -> refusal spike in metrics  
- token cost explosion -> llm_cost_usd_total spike

---

## Section 9 - The build rubric

**Ship -> Observe -> Break/Fix -> Explain -> Teach -> Harden**

This creates portfolio proof:
- You can run it.
- You can debug it.
- You can explain failures with evidence.

---

## Section 10 - Checklists and templates

Use these assets:
- `Lessons/LESSON_ASSETS/do_d_checklist.md`
- `Lessons/LESSON_ASSETS/rca_template.md`
- `Lessons/LESSON_ASSETS/diagram_aiops_spine.txt`

---

## Section 11 - Reflection + interview talk track

Reflection questions:
1) What failed first in your broken run?
2) Which log line proved the root cause?
3) What metric was most useful?
4) What would you add to prevent this class of failure?
5) How would this scale to 10,000 events?

2-minute talk track:
> "PurpleLens is a CLI SOC assistant. I added an AIOps V1 harness so each run produces structured JSONL logs and a metrics summary tied to a run_id. I can break the pipeline on purpose and recover using only logs and metrics, then write a mini RCA. This proves the system is operable and audit-ready, not just a demo."

---

## Required exercises (complete all three)
1) Confirm `run_id` appears in every log line of `run_log.jsonl`.  
2) Compare two runs and detect a failure trend using `error_count`.  
3) Run Failure Drill #1 and produce a mini RCA.  

---

## Security constraints to remember
- Do not log secrets or API keys.
- Avoid logging raw sensitive payloads.
- Log evidence pointers only (file name, record index, event ID).
- Treat LLM output as hints; rely on deterministic reporting for claims.
