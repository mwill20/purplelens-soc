================================================================================
DATASET MANIFEST: GCP Security Ground Truth (Phase 1)
================================================================================
Filename:   minilab_ground_truth_complete.json
Date:       January 4, 2026
Author:     Bespin AI Security Analyst Assistant Team
Format:     GCP Cloud Audit Log (JSON)
Event Count: ~30 Records

--------------------------------------------------------------------------------
1. DATASET DESCRIPTION
--------------------------------------------------------------------------------
This file contains a curated set of high-fidelity GCP Audit Logs generated during
a controlled "Purple Team" simulation. It captures a complete attack lifecycle,
designed to test SIEM/SOAR logic for correlation, severity scoring, and
threat actor attribution.

It is "Ground Truth" data: We know exactly what happened because we executed it.

--------------------------------------------------------------------------------
2. ATTACK SCENARIO (The "Answer Key")
--------------------------------------------------------------------------------
The dataset contains the following specific attack signals:

[A] IDENTITY & PERSISTENCE
    - Event: CreateServiceAccountKey (Method: google.iam.admin.v1...)
    - Attribution: Automation/Terraform User Agent
    - Intent: Establishing a backdoor credential.

[B] DEFENSE EVASION
    - Event: DeleteLogMetric
    - Event: UpdateSink (with Exclusion Filter)
    - Intent: Blinding the Security Operations Center (SOC).

[C] LATERAL MOVEMENT
    - Event: SetIamPolicy (Cross-Project)
    - Context: Compromised identity in 'lab-core' modifying 'production-database'.
    - Intent: Privilege Escalation across project boundaries.

[D] IMPACT & EXFILTRATION
    - Event: DestroyCryptoKeyVersion (KMS)
    - Event: SetIamPolicy (Storage) -> Made bucket "allUsers" (Public)
    - Intent: Data Destruction (Ransomware) and Data Leakage.

--------------------------------------------------------------------------------
2A. SIGNAL CHECKLIST (Present vs. Missing in this file)
--------------------------------------------------------------------------------
Checked items are confirmed present in minilab_ground_truth_complete.json.

[x] google.iam.admin.v1.CreateServiceAccountKey (persistence)
[ ] google.iam.admin.v1.DeleteServiceAccountKey (cleanup / evasion)

[x] cloudresourcemanager.googleapis.com/SetIamPolicy (project IAM)
[x] Cross-project project_id reference (includes 'purplelens-production-database')

[ ] google.logging.v2.MetricsServiceV2.CreateLogMetric
[ ] google.logging.v2.MetricsServiceV2.DeleteLogMetric
[ ] google.logging.v2.ConfigServiceV2.CreateSink
[ ] google.logging.v2.ConfigServiceV2.UpdateSink (exclusion filter)

[x] cloudkms.googleapis.com/CreateCryptoKey
[x] cloudkms.googleapis.com/DestroyCryptoKeyVersion

[x] iamcredentials.googleapis.com/GenerateAccessToken

[ ] storage.objects.get (DATA_READ)
[ ] storage.setIamPolicy (bucket public exposure)

--------------------------------------------------------------------------------
3. USAGE INSTRUCTIONS
--------------------------------------------------------------------------------
This file is the primary input for the Bespin/PurpleLens detection engine.

Command to Reproduce Analysis:
> python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --debug

--------------------------------------------------------------------------------
4. GENERATION METHOD
--------------------------------------------------------------------------------
Logs were harvested using the GCP Cloud SDK (`gcloud`) with a precise filter
to isolate signal from noise:
Filter: protoPayload.methodName=("CreateServiceAccountKey" OR "SetIamPolicy" ...)
Window: 4 Hours post-simulation.

================================================================================
