# Lesson 03B - API Fundamentals (Optional)

The project is CLI-first today, but the pipeline is designed to be wrapped by
an API or job system. This lesson explains a clean API shape for long-running
analysis without changing the core pipeline.

## Objectives
- Understand why async job APIs fit LLM workloads
- Learn a minimal job-based API contract
- Keep the same output schema used by the CLI

## Why async
LLM analysis is variable in latency and can exceed typical HTTP timeouts. A
job-based API avoids blocking requests and makes retries easier.

## Minimal API contract

### Create job
```
POST /analyze
Content-Type: multipart/form-data

file=@windows_sample.jsonl
source=auto
provider=gemini
model=gemini-flash-latest
```

Response:
```json
{
  "run_id": "9f1d1f7c-6d1b-4a18-8c67-acde00112233",
  "status": "queued"
}
```

### Check job
```
GET /jobs/{run_id}
```

Response (in progress):
```json
{
  "run_id": "9f1d1f7c-6d1b-4a18-8c67-acde00112233",
  "status": "running"
}
```

Response (complete):
```json
{
  "run_id": "9f1d1f7c-6d1b-4a18-8c67-acde00112233",
  "status": "success",
  "analysis": {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": [],
    "confidence": 0.42
  },
  "report_url": "https://storage.example/reports/analysis_20250101_120000.txt"
}
```

## Keeping the schema stable
- Use the same `AnalysisOutput` schema as the CLI.
- Treat report generation as a separate step so APIs can return quickly.
- Store artifacts in object storage for easy download and demoability.

## Exercises
1. Sketch a job worker that runs `python src/main.py` on a file saved to disk.
2. Decide how you would map `run_id` to storage paths and logs.
