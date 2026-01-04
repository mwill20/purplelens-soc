# GCP Security Mini-Lab: Audit Log Generation Procedure

Date: January 2026  
Artifact: `minilab_ground_truth_complete.json`

## Objective
Generate a high-fidelity dataset of GCP audit logs capturing the full lifecycle of a cloud attack: Persistence, Defense Evasion, Destruction, and Exfiltration.

## 1. Environment & Scope
The simulation was executed in a contained GCP Lab environment (`purplelens-lab-core`) to ensure zero risk to production assets.

- **Project ID**: `purplelens-lab-core`
- **Primary Actor**: `mwill.itmission@gmail.com` (Simulating Compromised Admin)
- **Secondary Actor**: `terraform-runner` (Service Account)
- **Target**: `victim-app` (Service Account) & Cloud Storage Data

## 2. Attack Simulation Execution
The following procedures were executed via Cloud Shell to generate specific **Control Plane** and **Data Plane** signals.

### Phase 1: Persistence (The Backdoor)
**Objective**: Establish persistent access to a service account to bypass future authentication checks.

- **Target Selection**: Identified the `victim-app` service account.
- **Key Creation**: Generated a JSON Service Account Key (the “Backdoor”).
  - **Signal**: `google.iam.admin.v1.CreateServiceAccountKey`
- **Cleanup**: Immediately deleted the key to hide tracks.
  - **Signal**: `google.iam.admin.v1.DeleteServiceAccountKey`

### Phase 2: Defense Evasion (Blinding the SOC)
**Objective**: Disable or tamper with security telemetry to prevent alerting.

- **Metric Manipulation**: Created and immediately deleted a Log Metric (`temporary-alert`) to test alert suppression.
  - **Signal**: `google.logging.v2.MetricsServiceV2.DeleteLogMetric`
- **Sink Tampering**:
  - Created a valid logging sink (`production-audit-sink`).
  - **Attack**: Updated the sink with an Exclusion Filter (`AND NOT protoPayload.methodName...`) to selectively silence specific audit events.
  - **Signal**: `google.logging.v2.ConfigServiceV2.UpdateSink` (with malicious filter arguments)

### Phase 3: Blast Radius & Destruction (KMS)
**Objective**: Demonstrate ability to destroy high-value cryptographic material (Ransomware/Destruction simulation).

- **Key Setup**: Created a Cloud KMS Key Ring and CryptoKey.
- **Destruction**: Destroyed the Key Version, rendering any data encrypted by it permanently inaccessible.
  - **Signal**: `cloudkms.googleapis.com/DestroyCryptoKeyVersion`

### Phase 4: Data Exfiltration (The Theft)
**Objective**: Access and expose sensitive data.

- **Preparation (Logging)**: Enabled `DATA_READ` audit logging for Cloud Storage (required to capture file access).
- **Theft**: Accessed a sensitive object (`secret.txt`) in a restricted bucket.
  - **Signal**: `storage.objects.get` (Data Access)
- **Exposure**: Modified bucket permissions to grant `allUsers` (Public Internet) access.
  - **Signal**: `storage.setIamPolicy` (High Severity Configuration Change)

## 3. Log Collection Strategy
Once the attack simulation was complete, logs were harvested directly from the Cloud Logging API. We utilized a precise filter to extract only the relevant signal events, filtering out the background noise of the lab environment.

### Extraction Command
```bash
gcloud logging read 'protoPayload.methodName=("CreateServiceAccountKey" OR "DeleteServiceAccountKey" OR "CreateLogMetric" OR "DeleteLogMetric" OR "CreateSink" OR "UpdateSink" OR "CreateCryptoKey" OR "DestroyCryptoKeyVersion" OR "GenerateAccessToken" OR "storage.objects.get" OR "SetIamPolicy")' \
  --format=json \
  --freshness=4h > minilab_ground_truth_complete.json
```

### Dataset Validation
- **Total Events**: ~30 high-signal records
- **Time Window**: 4 hours
- **Format**: Standard GCP Audit Log JSON

## 4. Summary of Signals Captured

| Category | Attack Technique | Log Method | Severity |
|---|---|---|---|
| Identity | Persistence | `CreateServiceAccountKey` | High |
| Identity | Defense Evasion | `DeleteServiceAccountKey` | Medium |
| Telemetry | Impair Defenses | `DeleteLogMetric` | Medium |
| Telemetry | Impair Defenses | `UpdateSink` (Exclusion) | High |
| Impact | Data Destruction | `DestroyCryptoKeyVersion` | Critical |
| Exfiltration | Data Theft | `storage.objects.get` | Medium |
| Exfiltration | Public Exposure | `storage.setIamPolicy` | Critical |
