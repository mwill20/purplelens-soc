# Lesson 06 - Phases 4 and 5: Report and Storage

After validation, the pipeline produces a deterministic report and writes the
results to SQLite for later review.

## Objectives
- Understand report structure and output paths
- Learn the SQLite schema
- See how status is derived for a run

## Report generation
Report output is deterministic and text-based for easy sharing:
- File path: `reports/analysis_<UTC timestamp>.txt`
- Module: `src/report.py`

The report includes:
- Executive Summary
- Findings (with evidence references)
- Hypotheses
- Indicators of Compromise
- Recommended Next Steps
- Errors (if analysis or validation failed)

## Storage
SQLite database: `db/analysis.db` (`src/storage.py`)

Tables:
- `analysis_runs`
  - run_id
  - timestamp
  - input_files (JSON)
  - status (success, partial, failed)
  - model_used
- `findings`
  - run_id
  - title
  - summary
  - severity
  - evidence (JSON)
- `hypotheses`
  - run_id
  - description
  - confidence
- `indicators_of_compromise`
  - run_id
  - indicator
- `reports`
  - run_id
  - report_text
  - generated_at

## Status derivation
Run status is derived from analysis results:
- `success`: structured output present with findings or hypotheses
- `partial`: partial output with missing or failed elements
- `failed`: no usable output

## Exercises
1. Add a new report section that highlights the top 3 IOCs.
2. Add a new SQLite table for performance metrics (duration, batch count).
