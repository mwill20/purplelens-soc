# GCP Mini-Lab Blueprint (Phase 0)

**Status:** APPROVED  
**Date:** January 3, 2026  
**Branch:** `enhancement/gcp-mini-lab`  
**Spec Reference:** `docs/ThreatPrism_NorthStar_Enhancement_2_GCP_MiniLab.md`

---

## 1. Mini-Lab Purpose
The purpose of this mini-lab is to demonstrate **cloud security engineering intuition** by generating a small, controlled set of high-signal GCP audit events. It does not aim for GCP mastery or enterprise-scale coverage. The focus is on capturing specific "identity + plane + blast radius" patterns to prove the architecture can handle cloud-native reasoning (control vs. telemetry planes).

---

## 2. Project & Identity Model

### Project Scope
- **Primary Project:** `threatprism-lab-core` (Conceptual)
- **Scope:** Single project to minimize complexity.

### Identity Model
1. **Human Principal (Control Plane Intent)**
   - **Identity:** `admin-human@example.com`
   - **Role:** Simulates an administrator performing sensitive manual actions (e.g., breaking glass, changing IAM).

2. **Automation Service Account (Machine Intent)**
   - **Identity:** `terraform-runner@threatprism-lab-core.iam.gserviceaccount.com`
   - **Role:** Simulates CI/CD or IaC pipelines.
   - **Signal:** High velocity, consistent user agent (`Terraform/1.5.0`, `Cloud SDK`).

*Safety Rule: No personal Gmail accounts and no real organization assets are used.*

---

## 3. Event Checklist (Target Signals)
We will generate 6–10 specific event types to demonstrate plane awareness.

### A) Control Plane (Identity & Access)
*The "Who can do what" layer.*
1. `CreateServiceAccountKey` (The "Anchor" event - high risk persistence)
2. `SetIamPolicy` (Blast radius expansion)
3. `cloudkms.googleapis.com/DestroyCryptoKeyVersion` (Destructive event / Data loss risk)
4. `cloudkms.googleapis.com/CreateCryptoKey` (Resource creation)

### B) Telemetry / Visibility Plane (The "Watchtower")
*Attacks on the monitoring system itself.*
1. `logging.sinks.create` (Exfiltration path creation)
2. `logging.sinks.update` (Disabling visibility)
3. `logging.sinks.delete` (Blinding the SOC)

### C) Data Access Logs (Workload Identity)
*Modern cloud authentication patterns.*
1. `iamcredentials.googleapis.com/GenerateAccessToken` (Workload Identity / Keyless auth vs key-based auth differentiation)

**Total Event Count:** 8 events (within 6-10 requirement)

**Rationale for Event 5:** `GenerateAccessToken` demonstrates:
- Workload Identity Federation (preferred auth pattern)
- Service account impersonation detection
- Differentiates keyless (GKE, Cloud Run) vs key-based auth (risky)
- Tests Data Access log type (not just Admin Activity)
- Higher interview signal than low-noise data plane reads

---

## 4. Export Method (Conceptual)
Logs will be obtained via the standard GCP Logging tools to ensure format compliance.

**Strategy:**
1. **Source:** `gcloud logging read` or Cloud Logging API.
2. **Format:** JSON or JSONL (Newline Delimited JSON).
3. **Variability Handling:** The ingestion pipeline must handle:
   - Standard JSONL (Cloud Logging default).
   - JSON Arrays (Export to Storage).
   - Pub/Sub wrappers (`{"message": {"data": ...}}`).

*Note: No credentials or active API connections are required for the analysis tool itself; it operates on static file exports.*

---

## 5. Evidence & Provenance Guarantees
To maintain analyst trust, the system adheres to strict evidence rules:

1. **Primary Anchor:** `insertId` (GCP's unique log ID) is required for all citations.
2. **Location:** `source_file` and `record_index` (line number) must be preserved.
3. **Persistence:**
   - **Allowed:** SHA-256 Hash of raw log, extracted metadata (timestamp, actor, action).
   - **Forbidden:** Storing the full raw JSON blob in SQLite (Data Minimization).
4. **Replay:** `insertId` allows an analyst to find the exact log in GCP later.

---

## 6. Safety Boundaries
This lab operates under strict containment:
- **No Production Assets:** All log data is from a disposable lab environment.
- **No Write Access:** The analysis tool never connects to GCP APIs; it reads static files.
- **No Personal PII:** Identities are generic lab accounts.
- **No Remediation:** The tool analyzes and reports; it does not block or revert actions.

---

## 7. Strengths & Limitations

### Strengths
- **Ground Truth:** We know exactly what happened, allowing for precise unit testing.
- **High Signal:** Filters out the massive noise of default GCP auditing.
- **Deterministic:** Input A always results in Report B.

### Limitations
- **Scale:** Not representative of an enterprise with millions of logs/hour.
- **Scope:** Only covers ~10 event types out of thousands of GCP methods.
- **Context:** Does not see the "state" of the cloud (e.g., current firewall rules), only the "events" (changes to rules).
