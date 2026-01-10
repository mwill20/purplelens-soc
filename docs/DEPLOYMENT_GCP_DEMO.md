# GCP Deployment Guide (Demo)

This guide deploys the CLI pipeline as a Cloud Run Job for low-cost, batch
processing. Inputs and outputs live in GCS and secrets are stored in Secret
Manager. The goal is a realistic demo architecture that scales to zero.

## Overview
- Compute: Cloud Run Jobs
- Storage: GCS (inputs, reports, SQLite)
- Secrets: Secret Manager
- Logs: Cloud Logging

## Architecture

```
GCS (input) -> Cloud Run Job -> GCS (reports, db)
                 |
                 +-> Secret Manager (LLM key)
```

## Prerequisites
- GCP project and billing enabled
- gcloud installed and authenticated
- A container registry (Artifact Registry is recommended)

## Step 1: Create GCS buckets
Create one bucket with prefixes or two separate buckets:
- `gs://<bucket>/inputs/`
- `gs://<bucket>/outputs/`

## Step 2: Store secrets
Store one of these keys in Secret Manager:
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

## Step 3: Create a service account
Grant permissions:
- `roles/storage.objectAdmin` on the bucket
- `roles/secretmanager.secretAccessor` on the secret

## Step 4: Containerize the CLI
Use the provided `Dockerfile`, which sets the entrypoint to the Cloud Run Jobs
wrapper (`scripts/gcp_job_wrapper.py`). The wrapper downloads input from GCS,
runs the CLI, and uploads reports and the SQLite DB back to GCS.
The wrapper relies on `google-cloud-storage`, which is included in
`requirements.txt`.

```Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/

ENTRYPOINT ["python", "scripts/gcp_job_wrapper.py"]
```

## Step 5: Build and push image
Example (Artifact Registry):

```
gcloud artifacts repositories create purplelens \
  --repository-format=docker --location=us-central1

gcloud builds submit --tag \
  us-central1-docker.pkg.dev/<project>/purplelens/purplelens:latest .
```

## Step 6: Create the Cloud Run Job
Use env vars for provider and model, and mount secrets for API keys. The job
entrypoint expects arguments like `--input-gcs` and `--output-gcs`:

```
gcloud run jobs create purplelens-job \
  --image us-central1-docker.pkg.dev/<project>/purplelens/purplelens:latest \
  --region us-central1 \
  --service-account purplelens-sa@<project>.iam.gserviceaccount.com \
  --set-env-vars PROVIDER=gemini,MODEL=gemini-flash-latest \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

## Step 7: Provide inputs and capture outputs
The wrapper in `scripts/gcp_job_wrapper.py` supports:
- `--input-gcs`: file or prefix in GCS
- `--output-gcs`: output prefix in GCS
- `--source`, `--provider`, `--model`, `--db`
- `--run-tag` (optional, defaults to a UTC timestamp)
- `--upload-logs` (optional)

## Step 8: Run the job
Start a run and pass the input and output URIs:

```
gcloud run jobs execute purplelens-job --region us-central1 \
  --args="--input-gcs=gs://<bucket>/inputs/sample.jsonl,--output-gcs=gs://<bucket>/outputs,--source=auto,--upload-logs"
```

Outputs are written under:
- `gs://<bucket>/outputs/runs/<run-tag>/reports/`
- `gs://<bucket>/outputs/runs/<run-tag>/db/`
- `gs://<bucket>/outputs/runs/<run-tag>/logs/` (if enabled)

Use `--run-tag=demo-001` if you want a stable folder name.

## Optional: Schedule runs
Use Cloud Scheduler to trigger runs on a fixed schedule for demos.

## Troubleshooting
- Authentication errors: confirm the service account has secret access.
- Missing outputs: verify the wrapper uploads the report and DB to GCS.
- Slow runs: reduce batch size or use a smaller input file.

## Cost notes
Cloud Run Jobs and GCS stay near free tier for demo-scale usage. Scale-to-zero
means no idle cost.
