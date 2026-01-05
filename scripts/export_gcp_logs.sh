#!/usr/bin/env bash
# Usage:
#   ./scripts/export_gcp_logs.sh -p purplelens-lab-core -o data/gcp_log_pack/minilab_ground_truth_complete.json
#
# Purpose:
#   Export targeted GCP audit logs using gcloud into a JSON file compatible with PurpleLens.
#
# Limitations:
#   - Requires gcloud CLI installed and authenticated.
#   - Uses a targeted filter; does not export all audit logs.
#   - Writes output in JSON array format (not JSONL).

set -euo pipefail

while getopts ":p:o:f:" opt; do
  case ${opt} in
    p ) PROJECT_ID="$OPTARG" ;;
    o ) OUTPUT_PATH="$OPTARG" ;;
    f ) FRESHNESS="$OPTARG" ;;
    \? ) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    : ) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done

: "${PROJECT_ID:?Missing -p PROJECT_ID}"
: "${OUTPUT_PATH:?Missing -o OUTPUT_PATH}"
FRESHNESS="${FRESHNESS:-4h}"

FILTER='protoPayload.methodName=("CreateServiceAccountKey" OR "DeleteServiceAccountKey" OR "CreateLogMetric" OR "DeleteLogMetric" OR "CreateSink" OR "UpdateSink" OR "CreateCryptoKey" OR "DestroyCryptoKeyVersion" OR "GenerateAccessToken" OR "storage.objects.get" OR "SetIamPolicy")'

echo "Exporting logs from project ${PROJECT_ID} to ${OUTPUT_PATH}"
gcloud logging read "${FILTER}" \
  --project "${PROJECT_ID}" \
  --format=json \
  --freshness="${FRESHNESS}" \
  > "${OUTPUT_PATH}"

echo "Export complete: ${OUTPUT_PATH}"
