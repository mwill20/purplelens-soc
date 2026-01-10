# Lesson 03 - Phase 1: Ingest Deep Dive

The ingest phase is responsible for reading source logs, normalizing fields,
and producing the event envelope used by all downstream stages.

## Objectives
- Understand supported source formats
- Learn how normalization works
- Know what to change when adding a new source

## Supported sources and formats
### Windows
- Expected format: JSONL (one JSON record per line)
- Module: `src/ingest.py`
- Output: envelope with `source_file`, `record_index`, optional `event_id`,
  and `raw_event`

### AWS CloudTrail
- Expected formats: JSONL or CloudTrail JSON files
- Module: `src/ingest_aws.py`
- Enrichment: `src/aws_plane_tagging.py` and `src/aws_correlate.py`

### GCP Cloud Logging
- Expected formats: JSONL, JSON arrays, or Pub/Sub wrapper payloads
- Module: `src/ingest_gcp.py`
- Enrichment: `src/gcp_plane_tagging.py` and `src/gcp_enrichment.py`

## The normalized event envelope

```json
{
  "source_file": "Logs/aws_sample.json",
  "record_index": 3,
  "event_id": "f8b7f7c2-3b54-4fbb-acde-2e6e9a4a7e71",
  "raw_event": {
    "eventName": "AssumeRole",
    "eventSource": "sts.amazonaws.com",
    "userIdentity": { "type": "AssumedRole" }
  }
}
```

Downstream stages never read the source file directly. They only consume this
envelope, so any new source must emit the same shape.

## Source detection
- Use `--source auto` to detect source by file extension and JSON markers.
- You can override with `--source windows|aws|gcp`.
- Mixed-source inputs are rejected to keep analysis clean.

## Common pitfalls
- JSON arrays must be loaded as a list of events, not a single event.
- Pub/Sub wrapper payloads must be unwrapped to reach the log entry.
- For AWS and GCP, ensure event IDs are preserved when present.

## Exercises
1. Add a new field to the envelope (for example `ingest_timestamp`) and trace
   how it would flow into reporting or storage.
2. Update auto-detection to recognize a new log format and log a clear error
   when inputs are mixed.
