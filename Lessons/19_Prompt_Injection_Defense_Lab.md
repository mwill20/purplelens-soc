# Lesson 19: Prompt Injection Defense Lab (ThreatPrism)

Time: 30-45 minutes

Goal: Practice prompt-injection defense using ThreatPrism run artifacts and verify that the sanitize stage blocks or redacts malicious strings before the LLM.

---

## Branch note (only if you plan to edit the dataset)

If you want to modify the red-team dataset as part of the lab, create a branch:
```bash
git checkout -b lab/prompt-injection-defense
```

---

## Section 1 - Why this matters

Security logs are untrusted input. Attackers can embed instructions inside log fields to trick the model.

ThreatPrism defends against this with:
- A prompt firewall that **redacts** instruction-like strings.
- **Quarantine** logic that removes unsafe events before LLM analysis.
- Ops artifacts that prove the defense worked.

---

## Section 2 - Red-team dataset (provided)

Use this dataset:
```
data/redteam/prompt_injection_windows.jsonl
```

It includes:
- One benign event.
- One event with "Ignore previous instructions" (quarantine).
- One event with "run this command" (redact only).

---

## Section 3 - Run the lab (dry-run)

PowerShell:
```powershell
python -m src.main --input data/redteam/prompt_injection_windows.jsonl --source windows --debug --dry-run
```

bash:
```bash
python -m src.main --input data/redteam/prompt_injection_windows.jsonl --source windows --debug --dry-run
```

This run will not call the LLM, but it will execute the sanitize stage and write ops artifacts.

---

## Section 4 - Verify sanitize evidence

1) Find the run directory:
```powershell
$latest = Get-ChildItem runs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latest.FullName
```

2) Inspect the sanitize stage log line:
```powershell
Get-Content runs/<run_id>/run_log.jsonl | Select-String "\"stage\":\"sanitize\""
```

You should see fields like:
- `prompt_injection_hits`
- `events_sanitized`
- `events_quarantined`
- `affected_event_ids`
- `quarantined_event_refs`

3) Inspect metrics:
```powershell
Get-Content runs/<run_id>/metrics.json
```

Confirm:
- `prompt_injection_hits` > 0
- `events_quarantined` >= 1

---

## Section 5 - Optional full run (LLM)

If you have API keys set and want to confirm quarantined events never reach the LLM:

```powershell
python -m src.main --input data/redteam/prompt_injection_windows.jsonl --source windows --debug
```

The run should complete with fewer events passed to `llm_analyze` than were ingested.

---

## Practical application (AIOps on this project)

1) Add a new injection string to the dataset (on your branch).
2) Re-run the dry-run.
3) Verify `prompt_injection_hits` and `events_sanitized` increase.
4) Capture evidence with:
```powershell
python scripts/evidence_artifact.py --run-id <run_id>
```

This gives you hands-on proof of pipeline defense + AIOps validation.

---

## Required exercises
1) Confirm the sanitize stage logs affected event IDs.
2) Confirm the quarantined event is not counted as processed downstream.
3) Explain why redaction vs quarantine is safer for different cases.
