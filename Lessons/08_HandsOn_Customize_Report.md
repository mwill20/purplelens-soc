# Lesson 08 - Hands On: Customize the Report

This lab walks through a small report customization that uses existing fields
without changing the schema.

## Goal
Add a short "Run Quality" section that reports status and confidence near the
top of the report.

## Steps
1. Open `src/report.py` and locate the function that builds the report lines.
2. Find the section where the executive summary is added.
3. Insert a new block that includes:
   - `analysis_output.status`
   - `analysis_output.confidence`
4. Keep formatting consistent with the rest of the report.

Example snippet to add (exact placement may differ):

```text
Run Quality
-----------
Status: success
Confidence: 0.58
```

## Why this works
- `status` and `confidence` are already part of the validated schema.
- No changes are needed to ingestion, LLM analysis, or validation.

## Stretch ideas
- Add a "Top IOCs" section that lists the first 3 indicators.
- Add a "Source Summary" section that counts events per input file.
