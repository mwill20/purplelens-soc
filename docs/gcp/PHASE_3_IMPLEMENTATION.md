# Phase 3 Implementation: GCP Enrichment (Automation + Identity)

**Status:** COMPLETE  
**Date:** January 3, 2026  
**Components:** `src/gcp_enrichment.py`, `src/ingest_gcp.py`, `src/main.py`

## 1. Goal
Phase 3 adds **deterministic “cheat codes” enrichment** for GCP Audit Logs to help the LLM reason about:
- **Who** performed the action (human vs service account)
- **How** it was performed (IaC/CLI/SDK/CI signals)
- **Confidence** in automation attribution
- **Cross-project** access heuristics

This enrichment is computed in Python (no external API calls) and attached to each normalized GCP event.

---

## 2. Enrichment Signals (Deterministic)
### Strong tells
- **Service account identity:** `*.gserviceaccount.com` → `actor_kind=service_account`
- **Workload identity:** `principalSubject` contains `workloadIdentityPools` → `workload_identity=True`

### Supporting tell
- **Private IP:** RFC1918 (`10.*`, `192.168.*`, `172.16-31.*`) → increases likelihood of workload/runtime origin

### Weak signals (User-Agent)
User-agent patterns are mapped to normalized tool labels (examples):
- `Terraform/...` → `iac_terraform`
- `google-cloud-sdk/...`, `gcloud/...`, `cloud-sdk` → `cli_gcloud`
- CI/CD/workflow patterns (Cloud Build, GitHub Actions, Jenkins, etc.) → `cicd_*` / `workflow_*`

---

## 3. Confidence Model
`compute_automation_confidence(...)` returns one of:
- `high`: service account OR workload identity
- `medium`: IaC/CI/CD/SDK signals without strong identity tell
- `low`: gcloud alone OR private IP without other automation tool
- `none`: no automation signals

This is intentionally conservative: automation signals inform analysis but do not prove malicious intent.

---

## 4. Integration Points
### 4.1 Ingest-time enrichment
In `src/ingest_gcp.py`, `normalize_gcp_audit(...)` computes and attaches:
- `actor_kind`
- `automation_tool`
- `automation_confidence`
- `workload_identity`
- `cross_project`

These are stored inside the per-event `raw_event` envelope.

### 4.2 Debug visibility (one line per event)
A single enrichment log line is emitted **only when DEBUG logging is enabled**:

```
[DEBUG] [src.ingest_gcp] GCP Enrichment [<source_file>:<record_index>]: ActorKind=..., Tool=..., Confidence=..., CrossProject=...
```

### 4.3 CLI support: `--debug`
`src/main.py` adds `--debug`, which sets logging level to `DEBUG` (overrides `--verbose`/default levels).

---

## 5. Validation (Reproducible)
### Dry-run with enrichment debug output
```powershell
python -m src.main --input data/gcp_log_pack/minilab_synthetic.jsonl --dry-run --debug
```
Expected:
- Source detection logs show `gcp`
- Exactly 3 enrichment debug lines (one per event)
- `Validation successful. Loaded 3 events...`

### Regression tests
```powershell
python -m pytest tests/ -q
```
Expected:
- `76 passed`

---

## 6. Known Limitations
- `cross_project` heuristic is currently designed primarily for service accounts (not a full principal-to-project resolver).
- No dedicated GCP unit tests are added in this phase; verification is via end-to-end dry-run logging and regression suite.
