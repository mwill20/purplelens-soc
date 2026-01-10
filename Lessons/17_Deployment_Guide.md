# Lesson 17 - Deployment Guide

This lesson explains how to deploy the project as a demo-grade cloud service
while keeping costs low and iteration speed high. It uses GCP Cloud Run Jobs as
the concrete example and generalizes the concepts to other platforms.

## Objectives
- Understand the core deployment decisions for a batch LLM pipeline
- Learn a practical GCP deployment pattern
- Identify what changes for AWS or other providers
- Run a real Cloud Run Job using GCS inputs and outputs

## Deployment decisions (general)
1. Packaging
   - Container image with pinned dependencies
2. Compute model
   - Batch job (Cloud Run Jobs, AWS Batch, or Lambda with async)
3. Storage
   - Object storage for inputs and reports
   - SQLite for demo-scale persistence
4. Secrets
   - Secret Manager or Parameter Store
5. Observability
   - Central logs and job status

## Why batch jobs work well
LLM analysis is asynchronous, variable in time, and may be expensive. A batch
job:
- Avoids HTTP timeouts
- Keeps compute off when idle
- Makes costs predictable

## GCP demo pattern (this project)
Use Cloud Run Jobs + GCS + Secret Manager:

```
GCS (inputs) -> Cloud Run Job -> GCS (reports, db)
                 |
                 +-> Secret Manager (LLM key)
```

Key steps:
1. Build a container with the provided `Dockerfile` (entrypoint is
   `scripts/gcp_job_wrapper.py`).
2. Store the LLM key in Secret Manager.
3. Create a Cloud Run Job with the service account permissions.
4. Use the wrapper arguments (`--input-gcs`, `--output-gcs`) to move data.

Refer to `docs/DEPLOYMENT_GCP_DEMO.md` for the full command sequence.

## Command checklist (copy and adapt)
This is the minimal sequence you should be able to run after completing the
lesson. Replace placeholders with your project values.

Build and push:
```
gcloud artifacts repositories create purplelens \
  --repository-format=docker --location=us-central1

gcloud builds submit --tag \
  us-central1-docker.pkg.dev/<project>/purplelens/purplelens:latest .
```

Create the job:
```
gcloud run jobs create purplelens-job \
  --image us-central1-docker.pkg.dev/<project>/purplelens/purplelens:latest \
  --region us-central1 \
  --service-account purplelens-sa@<project>.iam.gserviceaccount.com \
  --set-env-vars PROVIDER=gemini,MODEL=gemini-flash-latest \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

Execute with stable outputs:
```
gcloud run jobs execute purplelens-job --region us-central1 \
  --args="--input-gcs=gs://<bucket>/inputs/sample.jsonl,--output-gcs=gs://<bucket>/outputs,--run-tag=demo-001"
```

## Outcome
By the end of this lesson you should be able to:
- Build and push a container image
- Create a Cloud Run Job with the right permissions
- Execute the job with `--input-gcs` and `--output-gcs`
- Find reports and the SQLite DB in GCS under `runs/<run-tag>/`

## How this maps to AWS (quick notes)
- Compute: AWS Batch or Lambda (async)
- Storage: S3
- Secrets: Systems Manager Parameter Store or Secrets Manager
- Logs: CloudWatch

## Exercise
Draft a deployment checklist for your demo:
- Container registry
- Secrets storage
- Job execution model
- Input and output bucket paths
- Cost guardrails
