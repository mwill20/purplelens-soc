# Lesson 14: GCP Audit Log Enhancements (Branch: enhancement/gcp-mini-lab)

This lesson explains the GCP-specific upgrades added for the mini-lab. It is the GCP equivalent of:
- Lesson 03: Phase 1 Ingest (Windows JSONL)
- Lesson 04: Phase 2 LLM Analysis (Windows prompts)
- Lesson 13: AWS CloudTrail Enhancements

You do NOT need to be a developer. The goal is to understand what the system does and why.

---

## Learning goals

By the end of this lesson, you will be able to:
- Explain how GCP audit logs are detected and loaded (JSON vs JSONL).
- Describe the normalized event envelope for GCP.
- Explain plane tagging (control/data/telemetry) in plain English.
- Explain enrichment ("cheat codes") for actor and automation signals.
- Explain how GCP prompts differ from Windows and AWS.
- Run a basic GCP dry-run from the command line.

---

## Big picture: GCP path vs Windows and AWS

Windows path (existing lessons):
1. EVTX files -> JSONL (PowerShell script)
2. `src/ingest.py` loads JSONL, attaches provenance
3. `src/llm_analyze.py` uses Windows prompt

AWS path (Lesson 13):
1. CSV -> JSONL
2. `src/ingest_aws.py` normalizes CloudTrail
3. Plane tagging + correlation + AWS prompt

GCP path (this lesson):
1. JSON or JSONL audit logs -> `src/ingest_gcp.py`
2. `src/gcp_plane_tagging.py` assigns control/data/telemetry
3. `src/gcp_enrichment.py` adds deterministic identity/automation signals
4. `src/llm_analyze.py` uses GCP prompt + deterministic IOC extraction

---

## Step 1: GCP detection and loading

File: `src/ingest_gcp.py`

What it supports:
- JSON arrays (one file with many events)
- JSONL (one JSON object per line)

How detection works:
- Auto-detect by schema markers (protoPayload / insertId / logName)
- Or override with `--source gcp`

Example command:
```powershell
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

Expected output:
```
Validation successful. Loaded 3 events from data\gcp_synthetic_minilab.jsonl.
```

---

## Step 2: Normalization and envelope

File: `src/ingest_gcp.py`

Every event is normalized into the same evidence envelope:
```python
{
  "source_file": "...",
  "record_index": 0,
  "event_id": "insertId",
  "raw_event": {
    "source": "gcp",
    "event_time": "...",
    "actor": "...",
    "action": "...",
    "resource": "...",
    "plane": "control",
    "severity": "...",
    "src_ip": "...",
    "user_agent": "...",
    "insertId": "...",
    "raw_hash": "...",
    "raw": { ...original GCP log... }
  }
}
```

Key safety rule:
- The raw log is never stored to SQLite. Only the normalized fields and hash are used.

---

## Step 3: Plane tagging (control, data, telemetry)

File: `src/gcp_plane_tagging.py`

Examples:
- `iam.googleapis.com` -> control
- `logging.googleapis.com` -> telemetry, but sink changes are control
- `storage.googleapis.com` -> data

Why it matters:
Plane is context, not proof. It helps prioritize investigation.

Quick demo:
```powershell
python - <<'PY'
from src.gcp_plane_tagging import tag_plane
print(tag_plane("iam.googleapis.com", "CreateServiceAccountKey"))
print(tag_plane("logging.googleapis.com", "UpdateSink"))
print(tag_plane("storage.googleapis.com", "storage.objects.get"))
PY
```

Expected output:
```
control
control
data
```

---

## Step 4: Enrichment ("cheat codes")

File: `src/gcp_enrichment.py`

What it adds:
- `actor_kind`: human vs service_account vs google_service_agent
- `automation_tool`: normalized labels (iac_terraform, cli_gcloud, sdk_python, etc.)
- `automation_confidence`: high/medium/low/none
- `workload_identity`: true if workload identity pattern is detected
- `cross_project`: true when service account project does not match resource project

Why it matters:
The LLM does not need to guess whether an event is automation. Python labels it.

---

## Step 5: GCP prompt and batching

File: `src/llm_analyze.py`

What is different:
- GCP has its own system prompt and user prompt builder.
- The prompt uses a compact envelope (no full raw log).
- Evidence citations require `source_file`, `record_index`, and `event_id` (insertId).

---

## Step 6: Deterministic IOC extraction (Option B)

File: `src/llm_analyze.py`

In addition to the LLM, GCP runs extract stable IOCs automatically:
- public IPs -> `ip:...`
- user agents -> `ua:...`
- principals -> `principal:...`
- project IDs -> `project:...`
- high value resources -> `resource:...`

These are pivots for investigation, not proof of compromise.

---

## Hands-on exercise (beginner friendly)

Goal: Validate the GCP pipeline and see enrichment output.

1) Dry-run the synthetic sample:
```powershell
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run
```

2) Run the full mini-lab with debug logging:
```powershell
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --source gcp --debug
```

Expected behavior:
- You will see "Processing X GCP batches..."
- Debug logs show enrichment (ActorKind, Tool, Confidence)
- A report is written to `reports/`

---

## Key takeaways

- GCP ingestion supports JSON and JSONL with auto-detection.
- Normalization keeps evidence provenance and avoids storing raw logs.
- Plane tagging and enrichment provide deterministic context.
- The GCP prompt uses a compact envelope with insertId evidence.
- Deterministic IOCs make analyst pivots consistent.

---

## Interview talking points (simple version)

- "GCP support is an adapter: we normalize audit logs into the same envelope as Windows and AWS."
- "Plane tagging is conservative context, not proof of impact."
- "Enrichment labels automation deterministically so the model does not guess."
- "Evidence always includes source_file, record_index, and insertId."

---

## Quick reference

Files to know:
- `src/ingest_gcp.py` (loader + normalization)
- `src/gcp_plane_tagging.py` (plane tagging)
- `src/gcp_enrichment.py` (actor/automation enrichment)
- `src/config_gcp.py` (constants)
- `src/llm_analyze.py` (GCP prompt + IOC extraction)

Useful commands:
```powershell
# Dry-run a small sample
python -m src.main --input data/gcp_synthetic_minilab.jsonl --source gcp --dry-run

# Full mini-lab run with debug logging
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --source gcp --debug
```
