# GCP Mini-Lab Log Pack

**Status:** Phase 1-3 Validation Artifact  
**Canonical Dataset:** `minilab_ground_truth_complete.json` (consolidated master, ~30 high-signal events)

## Current Contents
The canonical dataset contains a curated set of high-signal GCP Audit Log events covering Persistence, Defense Evasion, Lateral Movement (cross-project), Impact (KMS), and Exfiltration/Exposure signals. Use this pack to validate ingestion, plane tagging, enrichment, and deterministic IOC extraction without requiring active GCP credentials.

## Usage
```bash
python -m src.main --input data/gcp_log_pack/minilab_ground_truth_complete.json --debug
```
