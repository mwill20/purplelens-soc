# Lesson 13: AWS CloudTrail Enhancements (Branch: enhancement/aws-cloudtrail)

This lesson explains the AWS-specific upgrades added on this branch. It is the AWS equivalent of:
- Lesson 03: Phase 1 Ingest (Windows JSONL)
- Lesson 04: Phase 2 LLM Analysis (Windows prompts)

You do NOT need to be a developer. The goal is to understand what the system does and why.

---

## Learning goals

By the end of this lesson, you will be able to:
- Explain why AWS CloudTrail data needs preprocessing (CSV to JSONL).
- Describe the AWS ingestion adapter and the normalized event envelope.
- Explain plane tagging (control/data/telemetry) in plain English.
- Explain correlation (grouping) and why it is not proof of causality.
- Explain how AWS events are batched for LLM analysis.
- Run a basic AWS dry-run from the command line.

---

## Big picture: AWS vs Windows paths

Windows path (existing lessons):
1. EVTX files -> JSONL (PowerShell script)
2. `src/ingest.py` loads JSONL, attaches provenance
3. `src/llm_analyze.py` uses Windows prompt

AWS path (this branch):
1. Kaggle CSV -> JSONL (new Python script)
2. `src/ingest_aws.py` normalizes CloudTrail into a consistent envelope
3. `src/aws_plane_tagging.py` adds a plane label
4. `src/aws_correlate.py` groups events by time/actor/resource
5. `src/aws_batching.py` builds batches for LLM
6. `src/llm_analyze.py` uses AWS prompt + batch merge

---

## Step 1: CSV to JSONL conversion

File: `scripts/aws_csv_to_jsonl.py`

Why this exists:
- The Kaggle dataset is a big CSV, not JSONL.
- The pipeline expects one JSON object per line (JSONL).

What the converter does:
- Reads the CSV row by row.
- Builds nested fields like `userIdentity.*`.
- Skips rows missing required fields:
  - `eventTime`, `eventSource`, `eventName`

Command:
```powershell
python scripts/aws_csv_to_jsonl.py data/dec12_18features.csv data/aws_cloudtrail.jsonl
```

---

## Step 2: AWS ingestion and normalized envelope

File: `src/ingest_aws.py`

Goal: Convert CloudTrail data into the same event structure used everywhere else:
```python
{
  "source_file": "...",
  "record_index": 0,
  "event_id": "...",
  "raw_event": {
    "source": "aws_cloudtrail",
    "event_time": "...",
    "service": "...",
    "action": "...",
    "actor": "...",
    "actor_type": "...",
    "src_ip": "...",
    "user_agent": "...",
    "aws_region": "...",
    "account_id": "...",
    "resources": ["..."],
    "error": "...",
    "raw_hash": "...",
    "request_id": "...",
    "event_type": "...",
    "read_only": true,
    "management_event": true,
    "plane": "control"
  }
}
```

Key safety rules:
- No raw CloudTrail is stored in the database.
- Only a SHA256 hash (`raw_hash`) and normalized fields are kept.
- Missing/empty fields are handled safely (no crashes).

Comparison to Lesson 03:
- Windows ingest attaches `source_file`, `record_index`, and `event_id`.
- AWS ingest does the same, plus a normalized envelope for CloudTrail-specific fields.

---

## Step 3: Plane tagging (control, data, telemetry)

File: `src/aws_plane_tagging.py`

This adds context about the type of AWS activity:
- control: IAM, STS, KMS, CloudTrail config changes
- data: object access (S3, DynamoDB data operations)
- telemetry: logs/monitoring (CloudWatch, Logs, Events)
- unknown: safe default for everything else

Why this matters:
Plane is context, not proof. It helps you interpret events, but it does NOT claim impact.

---

## Step 4: Correlation (grouping, not causality)

Files:
- `src/aws_correlate.py`
- `src/config_aws.py`

What it does:
- Groups events that are close in time and share actor/resource/IP.
- Uses a 5 minute window and caps clusters at 50 events.
- Adds `cluster_id`, `cluster_strategy`, and `cluster_size` to each event.

Important rule:
Correlation is a proximity hint. It does not prove causality.

---

## Step 5: AWS batching and LLM prompts

Files:
- `src/aws_batching.py`
- `src/config_llm_budget.py`
- `src/llm_analyze.py`

What changed from Lesson 04:
- AWS batches are smaller (25 events) to keep prompts stable.
- Batches are built in cluster-then-time order.
- AWS prompt uses a compact envelope (no raw CloudTrail).
- Results are merged deterministically with deduplication.

---

## Hands-on exercise (beginner friendly)

Goal: Convert a tiny CSV, then dry-run AWS ingest.

1) Create a small CSV:
```powershell
@"
eventID,eventTime,eventSource,eventName,userIdentitytype,userIdentityarn,sourceIPAddress,awsRegion
1,2020-01-01T00:00:00Z,iam.amazonaws.com,CreateUser,IAMUser,arn:aws:iam::123456789012:user/alice,1.2.3.4,us-east-1
"@ | Out-File -FilePath "data/aws_sample.csv" -Encoding UTF8
```

2) Convert to JSONL:
```powershell
python scripts/aws_csv_to_jsonl.py data/aws_sample.csv data/aws_sample.jsonl
```

3) Dry-run the AWS path:
```powershell
python -m src.main --input data/aws_sample.jsonl --source aws --dry-run
```

Expected output:
```
Validation successful. Loaded 1 events from data/aws_sample.jsonl.
```

---

## Plane tagging demo

Goal: See how the plane label is chosen.

1) Start a Python shell:
```powershell
python
```

2) Paste this:
```python
from src.aws_plane_tagging import tag_plane

print(tag_plane("iam.amazonaws.com", "CreateUser"))        # control
print(tag_plane("s3.amazonaws.com", "GetObject"))          # data
print(tag_plane("cloudwatch.amazonaws.com", "PutMetricData"))  # telemetry
print(tag_plane("ec2.amazonaws.com", "DescribeInstances")) # unknown
```

Expected output:
```
control
data
telemetry
unknown
```

Why this matters:
- It gives context (control vs data vs telemetry).
- It does not claim impact or causality.

---

## Correlation visualization

Goal: See how events are grouped into clusters.

1) Start a Python shell:
```powershell
python
```

2) Paste this:
```python
from src.aws_correlate import correlate_events
from src.config_aws import CORRELATION_CONFIG

events = [
    {
        "source_file": "test.jsonl",
        "record_index": 0,
        "event_id": "1",
        "raw_event": {
            "source": "aws_cloudtrail",
            "event_time": "2020-01-01T12:00:00Z",
            "actor": "alice",
            "src_ip": "1.1.1.1",
            "resources": ["res1"],
        },
    },
    {
        "source_file": "test.jsonl",
        "record_index": 1,
        "event_id": "2",
        "raw_event": {
            "source": "aws_cloudtrail",
            "event_time": "2020-01-01T12:03:00Z",
            "actor": "alice",
            "src_ip": "1.1.1.1",
            "resources": ["res2"],
        },
    },
    {
        "source_file": "test.jsonl",
        "record_index": 2,
        "event_id": "3",
        "raw_event": {
            "source": "aws_cloudtrail",
            "event_time": "2020-01-01T12:10:00Z",
            "actor": "alice",
            "src_ip": "1.1.1.1",
            "resources": ["res3"],
        },
    },
]

result = correlate_events(events, CORRELATION_CONFIG)
for event in result:
    raw = event["raw_event"]
    print(event["record_index"], raw["cluster_id"], raw["cluster_strategy"], raw["cluster_size"])
```

Expected behavior:
- The first two events (12:00 and 12:03) should share a cluster.
- The third event (12:10) should be a different cluster (outside 5 minutes).

---

## Key takeaways

- AWS data is not JSONL by default, so we convert it first.
- The AWS adapter normalizes events and protects sensitive fields.
- Plane tagging and correlation add context but never claim causality.
- AWS batching uses smaller batches and a CloudTrail-specific prompt.
- The core pipeline stays the same; only the adapter and prompt change.

---

## Interview talking points (simple version)

- "AWS support is an adapter. I normalized CloudTrail into the same event envelope as Windows."
- "Plane tagging is conservative context only, not proof of impact."
- "Correlation groups events by proximity; it does not claim causality."
- "The LLM still only extracts structured data; Python writes the report."

---

## Quick reference

Files to know:
- `scripts/aws_csv_to_jsonl.py` (CSV -> JSONL)
- `src/ingest_aws.py` (AWS ingestion + normalization)
- `src/aws_plane_tagging.py` (plane tagging)
- `src/aws_correlate.py` (correlation)
- `src/aws_batching.py` (batch building)
- `src/config_llm_budget.py` (batch limits)
- `src/llm_analyze.py` (AWS prompt + merge)

Next lessons to compare:
- `Lessons/03_Phase1_Ingest_Deep_Dive.md`
- `Lessons/04_Phase2_LLM_Analysis_Deep_Dive.md`
