# Scripts

Small utilities that support dataset preparation, validation, and demos.

## Contents
- `prep_evtx.ps1`: Convert Windows EVTX files to JSONL input for PurpleLens.
- `aws_csv_to_jsonl.py`: Convert CloudTrail CSV (Kaggle Flaws dataset format) to JSONL.
- `check_demo_db.py`: Print a short summary of the latest analysis run in `db/analysis.db`.
- `verify_gcp_enrichment.py`: Print deterministic GCP enrichment signals for the mini-lab dataset.
- `append_exposure.py`: Append a synthetic exposure event to the GCP mini-lab dataset (modifies data in place).
- `export_gcp_logs.ps1`: Export targeted GCP audit logs using gcloud to JSON (Windows/PowerShell).
- `export_gcp_logs.sh`: Export targeted GCP audit logs using gcloud to JSON (Linux/macOS).
- `gcp_job_wrapper.py`: Cloud Run Jobs wrapper that downloads GCS input, runs the CLI, and uploads outputs.

## Notes
- Scripts assume repository-relative paths and should be run from the repo root.
- `append_exposure.py` is a data mutation utility; use it only for local demos.
