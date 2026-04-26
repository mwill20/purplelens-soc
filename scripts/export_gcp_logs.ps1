# Usage:
#   .\scripts\export_gcp_logs.ps1 -ProjectId "threatprism-lab-core" -OutputPath "data\gcp_log_pack\minilab_ground_truth_complete.json"
#
# Purpose:
#   Export targeted GCP audit logs using gcloud into a JSON file compatible with ThreatPrism.
#
# Limitations:
#   - Requires gcloud CLI installed and authenticated.
#   - Uses a targeted filter; does not export all audit logs.
#   - Writes output in JSON array format (not JSONL).

param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectId,

    [Parameter(Mandatory = $true)]
    [string] $OutputPath,

    [string] $Freshness = "4h"
)

$filter = @'
protoPayload.methodName=(
  "CreateServiceAccountKey" OR
  "DeleteServiceAccountKey" OR
  "CreateLogMetric" OR
  "DeleteLogMetric" OR
  "CreateSink" OR
  "UpdateSink" OR
  "CreateCryptoKey" OR
  "DestroyCryptoKeyVersion" OR
  "GenerateAccessToken" OR
  "storage.objects.get" OR
  "SetIamPolicy"
)
'@

Write-Host "Exporting logs from project $ProjectId to $OutputPath"
gcloud logging read $filter `
  --project $ProjectId `
  --format=json `
  --freshness=$Freshness `
  > $OutputPath

Write-Host "Export complete: $OutputPath"
