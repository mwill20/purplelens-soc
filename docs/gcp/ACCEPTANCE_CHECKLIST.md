# GCP Mini-Lab (Enhancement 2) — Architect Acceptance Checklist

Date: January 2026  
Branch intent: `enhancement/gcp-mini-lab`  
Spec anchors:
- [docs/gcp/ENHANCEMENT_2_NorthStar.md](docs/gcp/ENHANCEMENT_2_NorthStar.md)
- [docs/gcp/MINILAB_PLAN.md](docs/gcp/MINILAB_PLAN.md)

## 1) Goal (What “done” means)
Deliver a **small, high-signal** GCP Audit Log dataset and a working PurpleLens pipeline path that:
- Ingests real GCP Cloud Audit Log JSON (no live GCP connectivity)
- Produces a report with evidence-backed findings that cite **source_file + record_index + insertId**
- Demonstrates cloud security reasoning using **identity + plane (control/data/telemetry) + blast radius**

## 2) Non-Goals (Explicit)
- Enterprise-grade GCP security coverage
- Full SIEM replacement / detection catalog
- Auto-remediation or “we fixed it” narratives
- Mixed-source ingestion in a single run (Windows/AWS/GCP are analyzed separately)

## 3) Required Inputs / Artifacts
- Dataset
- Primary dataset file exists: [data/gcp_log_pack/minilab_ground_truth_complete.json](data/gcp_log_pack/minilab_ground_truth_complete.json)
- Dataset manifest (“certificate of authenticity”) exists: [data/gcp_log_pack/README.txt](data/gcp_log_pack/README.txt)
- Generation procedure exists: [docs/GCP_LAB_PROCEDURE.md](docs/GCP_LAB_PROCEDURE.md)

### README discoverability
- README contains a short link to the procedure doc: [README.md](README.md)

## 4) Dataset Signal Coverage (Pass/Fail)
Dataset must contain at least one event for each item below (validated by methodName/serviceName fields; insertId must be present).

### A. Identity & Persistence
- [ ] `google.iam.admin.v1.CreateServiceAccountKey`
- [ ] `google.iam.admin.v1.DeleteServiceAccountKey`

### B. Defense Evasion / Telemetry Impairment
- [ ] `google.logging.v2.MetricsServiceV2.CreateLogMetric`
- [ ] `google.logging.v2.MetricsServiceV2.DeleteLogMetric`
- [ ] `google.logging.v2.ConfigServiceV2.CreateSink`
- [ ] `google.logging.v2.ConfigServiceV2.UpdateSink` (must include evidence of an exclusion filter argument)

### C. Lateral Movement / Cross-Project
- [ ] `cloudresourcemanager.googleapis.com/SetIamPolicy` referencing a *different* project than the lab core (e.g., `purplelens-production-database`)

### D. Impact / Destruction
- [ ] `cloudkms.googleapis.com/CreateCryptoKey` (or equivalent KMS create operation)
- [ ] `cloudkms.googleapis.com/DestroyCryptoKeyVersion`

### E. Exfiltration / Public Exposure
- [ ] `storage.objects.get` (DATA_READ audit event; ensure data access audit logging enabled)
- [ ] `storage.setIamPolicy` (bucket policy change consistent with public exposure)

## 5) Pipeline Functional Criteria (Pass/Fail)
### A. Run command
- [ ] Single command runs without errors:
  - `python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --debug`

### B. Output
- [ ] Report is generated to `reports/analysis_<uuid>.txt` with `status=success`
- [ ] Report includes findings across all phases (Persistence, Defense Evasion, Destruction, Exfil/Public Exposure, Cross-Project)

### C. Evidence integrity
- [ ] Every finding includes evidence objects with:
  - `source_file` (path)
  - `record_index` (0-based)
  - `event_id` = GCP `insertId`

### D. Plane tagging sanity
- [ ] IAM / KMS / logging sink-metric changes are classified as **control** or **telemetry** (per design)
- [ ] Storage object read is classified as **data**

### E. Automation attribution sanity
- [ ] Terraform/gcloud automation signals are visible in normalized fields (user agent or enrichment) for at least one event

## 6) Regression / Safety Criteria (Pass/Fail)
- [ ] Windows EVTX runs still succeed (baseline preserved)
- [ ] AWS CloudTrail runs still succeed
- [ ] Source detection does not mis-classify GCP as AWS/Windows and vice versa
- [ ] Tool does not claim it executed actions/remediation; output remains policy-compliant

## 7) Delivery Checklist (What to hand off)
- [ ] Updated dataset with full signal coverage (Section 4 all checked)
- [ ] Updated dataset manifest checklist reflects reality
- [ ] Updated procedure doc if the export filter/method list changes
- [ ] A “known-good” report file path from a successful run (for demo/reference)

## 8) Quick Verification (recommended)
A minimal validation can be done by searching the dataset for required method names (exact commands left to implementer preference). The authoritative record is the checklist in:
- [data/gcp_log_pack/README.txt](data/gcp_log_pack/README.txt)
