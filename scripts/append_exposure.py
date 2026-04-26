#!/usr/bin/env python3
"""
Usage:
  python scripts/append_exposure.py

Purpose:
  Appends a synthetic exposure event to the GCP mini-lab dataset.

Limitations:
  - Modifies the dataset in place.
  - Intended for local demo data only.
  - Re-running appends unless prior synthetic IDs are filtered.
"""

import json
from pathlib import Path

file_path = Path("data/gcp_log_pack/minilab_ground_truth_complete.json")
if not file_path.exists():
    raise SystemExit(f"Missing file: {file_path}")

with file_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Remove previous synthetic attempts if present
filtered = [
    r
    for r in data
    if r.get("insertId") not in ("synthetic-exposure-final-001", "aj84ks92ld01")
]

# New authentic-looking event (as provided)
real_looking_log = {
    "protoPayload": {
        "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
        "status": {},
        "authenticationInfo": {"principalEmail": "mwill.itmission@gmail.com"},
        "requestMetadata": {
            "callerIp": "35.23.1.104",
            "callerSuppliedUserAgent": "GoogleCloudSDK/455.0.0 (Windows NT 10.0; x64) gcloud/455.0.0",
        },
        "serviceName": "storage.googleapis.com",
        "methodName": "storage.setIamPolicy",
        "resourceName": "projects/_/buckets/threatprism-marketing-assets-v2",
        "serviceData": {
            "@type": "type.googleapis.com/google.iam.v1.PolicyDelta",
            "bindingDeltas": [
                {
                    "action": "ADD",
                    "role": "roles/storage.objectViewer",
                    "member": "allUsers",
                }
            ],
        },
    },
    "insertId": "aj84ks92ld01",
    "resource": {
        "type": "gcs_bucket",
        "labels": {
            "bucket_name": "threatprism-marketing-assets-v2",
            "location": "us-central1",
            "project_id": "threatprism-lab-core",
        },
    },
    "timestamp": "2026-01-04T12:30:00Z",
    "severity": "NOTICE",
    "logName": "projects/threatprism-lab-core/logs/cloudaudit.googleapis.com%2Factivity",
}

# Append and write back as UTF-8 (no BOM)
final = filtered + [real_looking_log]
with file_path.open("w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f"Success. Added storage.setIamPolicy event. Final Event Count: {len(final)}")
