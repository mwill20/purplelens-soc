# PurpleLens Cloud Enhancement Plan
**Project Extension: Multi-Source Security Log Analysis**

---

## Document Purpose

This document outlines a **strategic, time-bounded approach** to extending PurpleLens with cloud log source capabilities and data pipeline patterns. It serves three purposes:

1. **Implementation Guide**: Step-by-step instructions if time permits
2. **Future Roadmap**: Enhancement plan for post-interview development
3. **Interview Artifact**: Demonstrates architectural thinking and planning discipline

**Status**: Planning Phase  
**Decision Point**: To be determined based on progress with core PurpleLens lessons  
**Estimated Effort**: 15-20 hours over 2-3 weeks  

---

## Executive Summary

### Problem Statement

Current PurpleLens implementation demonstrates AI-augmented security analysis with strong architectural principles, but operates on a single log source (Windows EVTX files) with local-only processing. Interviewer feedback identified two gaps:

1. **Cloud Infrastructure Experience**: No demonstrated use of cloud platforms (GCP, AWS)
2. **Data Pipeline Engineering**: Missing exposure to source/transform/sink patterns at scale

### Proposed Solution

Extend PurpleLens with:
- **Multi-source ingestion**: Add AWS CloudTrail logs alongside existing EVTX
- **Normalization layer**: Map diverse sources to common security event schema
- **Cloud deployment proof**: Minimal GCP Cloud Function to demonstrate platform capability
- **Preserved architecture**: Reuse existing analysis logic, proving source-agnostic design

### Success Criteria

**Technical:**
- ✅ Ingest and parse AWS CloudTrail logs from Kaggle dataset
- ✅ Normalize AWS and EVTX to unified schema
- ✅ Existing LLM analysis works on both sources without modification
- ✅ Deploy one Cloud Function to GCP (proof of capability)

**Interview:**
- ✅ Articulate Source → Parse → Normalize → Enrich → Store → Analyze pipeline
- ✅ Explain trust boundary and cross-source correlation
- ✅ Demonstrate hands-on cloud platform experience
- ✅ Show pragmatic engineering judgment (branching strategy, dataset selection)

### Strategic Decision: Branch + Parallel Module

**Approach**: Keep `master` branch pristine, build extensions on `cloud-extension` branch in isolated `src/cloud/` module.

**Rationale**: 
- Minimizes risk (original demo always works)
- Shows version control discipline
- Enables side-by-side comparison
- Allows graceful abandonment if time runs short

---

## Architecture Design

### Current State (Phase 1 Complete)

```
┌─────────────────────────────────────────────────────────┐
│                    LOCAL PIPELINE                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  SOURCE: Local EVTX files                                │
│     ↓                                                     │
│  INGEST: Python filesystem read                          │
│     ↓                                                     │
│  PARSE: evtx library → JSON                              │
│     ↓                                                     │
│  ─────── TRUST BOUNDARY ───────                          │
│     ↓                                                     │
│  ANALYZE: OpenAI LLM (gpt-4o-mini)                       │
│     ↓                                                     │
│  STORE: SQLite database                                  │
│     ↓                                                     │
│  REPORT: Text file generation                            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Single source (Windows Event Logs)
- Batch processing
- Local storage
- Manual execution

---

### Target State (Phase 2 - Cloud Enhanced)

```
┌──────────────────────────────────────────────────────────────────┐
│                  MULTI-SOURCE CLOUD PIPELINE                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  SOURCE LAYER (Multi-source)                                      │
│  ├─ Local EVTX files                                              │
│  ├─ AWS CloudTrail (Kaggle dataset)                               │
│  └─ [Future: GCP Audit Logs, Sysmon, etc.]                        │
│     ↓                                                              │
│  INGEST LAYER (Source-specific parsers)                           │
│  ├─ ingest.py (EVTX) ← EXISTING                                   │
│  └─ ingest_aws.py (CloudTrail) ← NEW                              │
│     ↓                                                              │
│  PARSE LAYER (Extract fields)                                     │
│  ├─ EVTX: EventID, TimeCreated, EventData                         │
│  └─ AWS: eventName, eventTime, userIdentity                       │
│     ↓                                                              │
│  ─────────────── TRUST BOUNDARY ───────────────                   │
│     ↓                                                              │
│  NORMALIZE LAYER (Common schema) ← NEW                            │
│  ├─ principalEmail → actor                                        │
│  ├─ eventName → action                                            │
│  ├─ EventID → event_id                                            │
│  └─ Output: Unified security event format                         │
│     ↓                                                              │
│  ENRICH LAYER (Add context)                                       │
│  ├─ MITRE ATT&CK mapping (security.py) ← EXISTING                 │
│  └─ [Future: GeoIP, threat intel]                                 │
│     ↓                                                              │
│  ANALYZE LAYER (AI augmentation)                                  │
│  └─ llm_analyze.py ← EXISTING, UNCHANGED                          │
│     ↓                                                              │
│  STORE LAYER                                                       │
│  ├─ storage.py (SQLite) ← EXISTING                                │
│  └─ [Future: storage_bq.py (BigQuery)]                            │
│     ↓                                                              │
│  REPORT LAYER                                                      │
│  └─ report.py ← EXISTING, UNCHANGED                               │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘

CLOUD DEPLOYMENT PROOF (Separate)
└─ GCP Cloud Function: Demonstrates ingestion API capability
```

**Key Changes:**
- **NEW**: Multi-source ingestion (EVTX + AWS CloudTrail)
- **NEW**: Normalization layer for cross-source compatibility
- **UNCHANGED**: Analysis, storage, and reporting logic
- **PROOF**: Minimal GCP deployment showing cloud capability

---

## Detailed Component Design

### Component 1: AWS CloudTrail Ingestion

**File**: `src/cloud/ingest_aws.py`

**Purpose**: Load and parse AWS CloudTrail logs from Kaggle flaws.cloud dataset

**Interface**:
```python
def load_aws_cloudtrail(directory: str) -> list[dict]:
    """
    Load AWS CloudTrail events from JSON files.
    
    Args:
        directory: Path to directory containing CloudTrail JSON files
        
    Returns:
        List of CloudTrail event dictionaries with provenance metadata
        
    Raises:
        FileNotFoundError: If directory doesn't exist or has no JSON files
        ValueError: If files exceed size limit
        json.JSONDecodeError: If JSON is malformed (logged and skipped)
    """
```

**Data Flow**:
```
Input:  data/cloud_logs/aws_cloudtrail/*.json
  ↓
Parse:  Extract "Records" array from each file
  ↓
Enrich: Add source_file, source_type provenance
  ↓
Output: List[dict] with CloudTrail events
```

**Implementation Details**:
- Reuses error handling patterns from `ingest.py`
- Adds `source_type: "aws_cloudtrail"` for tracking
- Preserves original CloudTrail structure in `raw_event` field
- Implements same 10MB file size limit as EVTX parser

**Testing**:
```python
# Verify ingestion
events = load_aws_cloudtrail("data/cloud_logs/aws_cloudtrail")
assert len(events) > 0
assert all(e["source_type"] == "aws_cloudtrail" for e in events)
assert all("source_file" in e for e in events)
```

---

### Component 2: Multi-Source Normalization

**File**: `src/cloud/normalize.py`

**Purpose**: Map diverse log sources to unified security event schema

**Schema Design**:
```python
class NormalizedSecurityEvent:
    """
    Common schema for all security log sources.
    Enables source-agnostic analysis and correlation.
    """
    timestamp: str          # ISO 8601 format
    source_type: str        # "windows_evtx", "aws_cloudtrail", etc.
    event_id: str           # Source-specific event identifier
    severity: str           # "low", "medium", "high", "critical"
    actor: str              # Who performed the action (user/principal)
    action: str             # What action was performed
    resource: str           # What was affected (file, bucket, instance)
    source_ip: str          # Originating IP address
    outcome: str            # "success", "failure", "denied"
    raw_event: dict         # Original event for provenance
    provenance: dict        # Tracking metadata (file, line, etc.)
```

**Mapping Logic**:

**AWS CloudTrail → Normalized:**
```python
def normalize_aws_event(aws_event: dict) -> dict:
    """Map AWS CloudTrail to common schema"""
    user_identity = aws_event.get("userIdentity", {})
    
    return {
        "timestamp": aws_event.get("eventTime"),
        "source_type": "aws_cloudtrail",
        "event_id": aws_event.get("eventName"),
        "severity": _assess_aws_severity(aws_event),  # Helper function
        "actor": user_identity.get("userName") or user_identity.get("principalId", "UNKNOWN"),
        "action": aws_event.get("eventName"),
        "resource": _extract_aws_resource(aws_event),  # Helper function
        "source_ip": aws_event.get("sourceIPAddress"),
        "outcome": "success" if aws_event.get("errorCode") is None else "failure",
        "raw_event": aws_event,
        "provenance": {
            "source_file": aws_event.get("source_file"),
            "source_type": "aws_cloudtrail"
        }
    }
```

**Windows EVTX → Normalized:**
```python
def normalize_evtx_event(evtx_event: dict) -> dict:
    """Map Windows EVTX to common schema"""
    event_data = evtx_event.get("Event", {})
    system = event_data.get("System", {})
    event_id = str(system.get("EventID"))
    
    return {
        "timestamp": system.get("TimeCreated"),
        "source_type": "windows_evtx",
        "event_id": event_id,
        "severity": _assess_evtx_severity(event_id),  # Helper function
        "actor": _extract_evtx_user(event_data),       # Event-specific logic
        "action": f"WindowsEvent_{event_id}",
        "resource": _extract_evtx_resource(event_data),
        "source_ip": _extract_evtx_ip(event_data) or "localhost",
        "outcome": "logged",
        "raw_event": evtx_event,
        "provenance": {
            "source_file": evtx_event.get("source_file"),
            "record_index": evtx_event.get("record_index"),
            "source_type": "windows_evtx"
        }
    }
```

**Why This Matters**:
- Enables queries like: "Show all failed actions by external IPs across ALL sources"
- LLM analysis receives consistent schema regardless of log origin
- Future sources (Sysmon, GCP, etc.) just need new normalize_X functions
- Preserves raw events for audit trail

---

### Component 3: Cloud Entry Point

**File**: `src/main_cloud.py`

**Purpose**: Orchestrate multi-source pipeline using composition

**Architecture Pattern**: Compose new cloud components WITH existing logic

```python
"""
Cloud-extended entry point for PurpleLens.
Demonstrates multi-source ingestion with source-agnostic analysis.

Key Design: Reuses existing analysis/report/storage modules.
Only the ingestion and normalization layers are new.
"""

from src.cloud.ingest_aws import load_aws_cloudtrail
from src.cloud.normalize import normalize_aws_event, normalize_evtx_event
from src.ingest import load_events  # Original EVTX loader
from src.llm_analyze import analyze_events  # UNCHANGED
from src.report import generate_report      # UNCHANGED
from src.storage import store_results       # UNCHANGED
import logging

LOGGER = logging.getLogger(__name__)

def main():
    """
    Multi-source security log analysis pipeline.
    
    Flow:
        1. Ingest from multiple sources (EVTX + AWS CloudTrail)
        2. Normalize to common schema
        3. Analyze with existing LLM logic
        4. Store and report using existing modules
    """
    print("=" * 60)
    print("PurpleLens - Cloud-Extended Multi-Source Analysis")
    print("=" * 60)
    print()
    
    # PHASE 1: Multi-Source Ingestion
    LOGGER.info("Phase 1: Ingesting from multiple sources...")
    
    # Load EVTX (existing source)
    evtx_events = load_events("data/evtx_parsed")
    print(f"  ✓ Loaded {len(evtx_events)} Windows EVTX events")
    
    # Load AWS CloudTrail (new source)
    aws_events = load_aws_cloudtrail("data/cloud_logs/aws_cloudtrail")
    print(f"  ✓ Loaded {len(aws_events)} AWS CloudTrail events")
    print()
    
    # PHASE 2: Normalization
    LOGGER.info("Phase 2: Normalizing to common schema...")
    
    evtx_normalized = [normalize_evtx_event(e) for e in evtx_events]
    aws_normalized = [normalize_aws_event(e) for e in aws_events]
    
    # Merge normalized events
    all_normalized = evtx_normalized + aws_normalized
    print(f"  ✓ Normalized {len(all_normalized)} total events")
    print(f"    - {len(evtx_normalized)} from Windows")
    print(f"    - {len(aws_normalized)} from AWS CloudTrail")
    print()
    
    # PHASE 3: Analysis (EXISTING LOGIC - UNCHANGED!)
    LOGGER.info("Phase 3: Analyzing with LLM...")
    
    analysis_results = analyze_events(all_normalized, model="gpt-4o-mini")
    print(f"  ✓ Generated {len(analysis_results)} security findings")
    print()
    
    # PHASE 4: Storage (EXISTING LOGIC - UNCHANGED!)
    LOGGER.info("Phase 4: Storing results...")
    
    store_results(analysis_results)
    print(f"  ✓ Results stored in database")
    print()
    
    # PHASE 5: Reporting (EXISTING LOGIC - UNCHANGED!)
    LOGGER.info("Phase 5: Generating report...")
    
    report_path = generate_report(analysis_results)
    print(f"  ✓ Report saved to: {report_path}")
    print()
    
    print("=" * 60)
    print("Analysis Complete")
    print("=" * 60)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

**Key Insight**: Only ~50 new lines of code to add a second log source. Most logic is reused.

---

### Component 4: GCP Cloud Function (Deployment Proof)

**File**: `cloud_function/main.py` (separate deployment artifact)

**Purpose**: Demonstrate cloud deployment capability without building full pipeline

**Implementation**:
```python
"""
Minimal GCP Cloud Function proving deployment capability.
This is NOT the main PurpleLens system - it's a proof of concept.
"""

def purplelens_audit_log_ingest(request):
    """
    Cloud Function demonstrating GCP Audit Log ingestion capability.
    
    In production, this would:
    - Receive Pub/Sub messages with log events
    - Parse and validate
    - Write to Cloud Storage or BigQuery
    
    For demo, it returns capability confirmation.
    """
    from google.cloud import logging_v2
    from datetime import datetime, timedelta
    
    # Example: Query last hour of audit logs
    client = logging_v2.Client()
    filter_str = (
        'protoPayload."@type"="type.googleapis.com/google.cloud.audit.AuditLog" '
        f'AND timestamp>="{(datetime.utcnow() - timedelta(hours=1)).isoformat()}Z"'
    )
    
    # Count available logs (don't process, just demonstrate access)
    log_count = sum(1 for _ in client.list_entries(filter_=filter_str, max_results=10))
    
    return {
        "status": "operational",
        "message": "PurpleLens Cloud Function deployed successfully",
        "project": "purplelens-demo",
        "capabilities": [
            "Cloud Logging API access",
            "Audit log query capability",
            "Multi-source ingestion architecture"
        ],
        "sample_logs_available": log_count,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Deployment**:
```powershell
# One-time setup
gcloud auth login
gcloud config set project purplelens-demo

# Deploy
gcloud functions deploy purplelens-audit-log-ingest `
    --runtime python311 `
    --trigger-http `
    --allow-unauthenticated `
    --region us-central1 `
    --entry-point purplelens_audit_log_ingest

# Test
Invoke-WebRequest -Uri "https://us-central1-purplelens-demo.cloudfunctions.net/purplelens-audit-log-ingest"
```

**Deliverables**:
1. Screenshot of GCP Console showing deployed function
2. Screenshot of successful HTTP response
3. One-paragraph reflection on deployment experience

**Time Investment**: 3-4 hours total

---

## Dataset Strategy

### Selected Dataset: Kaggle AWS CloudTrail (flaws.cloud)

**Source**: https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud

**Characteristics**:
- **Size**: ~500MB of CloudTrail events
- **Content**: Real attack patterns from flaws.cloud security CTF
- **Format**: Standard AWS CloudTrail JSON
- **Attack Patterns**: S3 misconfigurations, IAM abuse, privilege escalation
- **Community**: Well-known in security circles

**Why This Dataset**:

| Criterion | Rationale |
|-----------|-----------|
| **Authenticity** | Real CloudTrail events, not synthetic |
| **Relevance** | Contains actual security incidents |
| **Availability** | Immediate download, no cloud account needed |
| **Cost** | Free (vs $10-50/month for generating own) |
| **Time** | Saves 4-6 hours of cloud setup and log generation |
| **Interview Credibility** | "I analyzed the flaws.cloud dataset" is recognized |

### Dataset Structure

**CloudTrail Event Format**:
```json
{
  "Records": [
    {
      "eventVersion": "1.08",
      "userIdentity": {
        "type": "IAMUser",
        "principalId": "AIDAI...",
        "arn": "arn:aws:iam::123456789012:user/attacker",
        "accountId": "123456789012",
        "accessKeyId": "AKIAI...",
        "userName": "attacker"
      },
      "eventTime": "2024-01-15T10:23:45Z",
      "eventSource": "s3.amazonaws.com",
      "eventName": "GetBucketPolicy",
      "awsRegion": "us-east-1",
      "sourceIPAddress": "93.184.216.34",
      "userAgent": "aws-cli/1.16.102",
      "requestParameters": {
        "bucketName": "flaws.cloud"
      },
      "responseElements": null,
      "requestID": "ABC123...",
      "eventID": "def456...",
      "eventType": "AwsApiCall",
      "recipientAccountId": "123456789012"
    }
  ]
}
```

### Directory Structure

```
data/
├── evtx_parsed/                    # Existing EVTX data
│   ├── Credential_hashdump.jsonl
│   ├── Execution_wmic.jsonl
│   └── Lateral_wmic.jsonl
└── cloud_logs/                     # New cloud data
    ├── README.md                   # Dataset documentation
    └── aws_cloudtrail/             # Kaggle dataset
        ├── cloudtrail_001.json
        ├── cloudtrail_002.json
        └── ... (multiple files)
```

### Setup Instructions

```powershell
# 1. Create directory structure
New-Item -ItemType Directory -Path "data/cloud_logs/aws_cloudtrail" -Force

# 2. Download from Kaggle
# Visit: https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud
# Requires free Kaggle account
# Download ZIP file

# 3. Extract
Expand-Archive -Path "Downloads/aws-cloudtrails-dataset-from-flaws-cloud.zip" `
               -DestinationPath "data/cloud_logs/aws_cloudtrail"

# 4. Verify
Get-ChildItem "data/cloud_logs/aws_cloudtrail" -Filter *.json | Measure-Object
# Should show multiple JSON files

# 5. Add to .gitignore (files are large)
Add-Content .gitignore "`ndata/cloud_logs/*.json"
```

---

## Implementation Roadmap

### Phase 2.1: AWS Ingestion (Week 1, 6 hours)

**Objective**: Load and parse AWS CloudTrail logs

**Tasks**:
1. Create `src/cloud/` directory and `__init__.py`
2. Implement `src/cloud/ingest_aws.py`
3. Download Kaggle dataset to `data/cloud_logs/`
4. Write unit test for ingestion
5. Verify provenance metadata attached

**Acceptance Criteria**:
- [ ] Can load CloudTrail JSON files
- [ ] Returns list of event dictionaries
- [ ] Adds `source_file`, `source_type` provenance
- [ ] Handles malformed JSON gracefully
- [ ] Test passes with sample data

**Deliverable**: Working AWS log ingestion module

---

### Phase 2.2: Normalization Layer (Week 1-2, 6 hours)

**Objective**: Unified schema for cross-source analysis

**Tasks**:
1. Design `NormalizedSecurityEvent` schema
2. Implement `normalize_aws_event()`
3. Implement `normalize_evtx_event()`
4. Write mapping documentation
5. Create unit tests for both normalizers

**Acceptance Criteria**:
- [ ] Both AWS and EVTX map to same field names
- [ ] Timestamp formats standardized
- [ ] Original event preserved in `raw_event`
- [ ] Provenance metadata maintained
- [ ] Tests verify field mappings

**Deliverable**: Normalization module with test coverage

---

### Phase 2.3: Multi-Source Entry Point (Week 2, 4 hours)

**Objective**: Orchestrate pipeline with multiple sources

**Tasks**:
1. Create `src/main_cloud.py`
2. Import and compose existing modules
3. Add multi-source ingestion logic
4. Add normalization step
5. Verify existing analysis works unchanged

**Acceptance Criteria**:
- [ ] Loads both EVTX and AWS events
- [ ] Normalizes both to common schema
- [ ] Feeds normalized events to `analyze_events()`
- [ ] Generates report successfully
- [ ] Original `main.py` still works independently

**Deliverable**: Working multi-source pipeline

---

### Phase 2.4: GCP Deployment (Week 3, 4 hours)

**Objective**: Prove cloud deployment capability

**Tasks**:
1. Set up GCP free tier account
2. Install `gcloud` CLI
3. Write minimal Cloud Function
4. Deploy to GCP
5. Test and screenshot

**Acceptance Criteria**:
- [ ] GCP project created
- [ ] Cloud Function deployed successfully
- [ ] HTTP endpoint responds
- [ ] Screenshots captured
- [ ] Reflection documented

**Deliverable**: Deployed Cloud Function + documentation

---

### Phase 2.5: Documentation (Week 3, 2 hours)

**Objective**: Interview-ready explanations

**Tasks**:
1. Update README with cloud architecture
2. Create `docs/Cloud_Architecture.md`
3. Write normalization schema documentation
4. Add code comments throughout
5. Prepare architecture diagram

**Acceptance Criteria**:
- [ ] README explains both demos
- [ ] Architecture document complete
- [ ] Code well-commented
- [ ] Diagram shows data flow
- [ ] Interview talking points prepared

**Deliverable**: Comprehensive documentation package

---

## Project Structure

### File Organization (Cloud Extension Branch)

```
purplelens-soc/
├── src/
│   ├── ingest.py                  # Original (UNCHANGED)
│   ├── llm_analyze.py             # Original (UNCHANGED)
│   ├── security.py                # Original (UNCHANGED)
│   ├── storage.py                 # Original (UNCHANGED)
│   ├── report.py                  # Original (UNCHANGED)
│   ├── main.py                    # Original entry point (UNCHANGED)
│   ├── cloud/                     # NEW - Cloud extensions
│   │   ├── __init__.py
│   │   ├── ingest_aws.py          # AWS CloudTrail parser
│   │   ├── normalize.py           # Multi-source normalization
│   │   └── storage_bq.py          # BigQuery backend (FUTURE)
│   └── main_cloud.py              # NEW - Cloud entry point
├── data/
│   ├── evtx_parsed/               # Existing EVTX data
│   └── cloud_logs/                # NEW - Cloud datasets
│       ├── README.md
│       └── aws_cloudtrail/        # Kaggle dataset
├── docs/
│   ├── ARCHITECTURE.md            # Original (update with cloud)
│   ├── Cloud_Enhancement_Plan.md  # This document
│   └── Cloud_Architecture.md      # NEW - Cloud design details
├── tests/
│   └── test_cloud_ingestion.py   # NEW - Cloud tests
├── cloud_function/                # NEW - GCP deployment
│   ├── main.py                    # Cloud Function code
│   └── requirements.txt           # Cloud dependencies
└── requirements.txt               # Original (add google-cloud-logging)
```

---

## Git Workflow

### Branching Strategy

```powershell
# Create feature branch
git checkout -b cloud-extension

# Track remote
git push -u origin cloud-extension

# Develop on branch
# (all cloud work happens here)

# Switch back to demo original
git checkout master

# Return to cloud work
git checkout cloud-extension

# When ready, merge (optional)
git checkout master
git merge cloud-extension
```

### Commit Strategy

**Atomic Commits**:
```
feat(cloud): Add AWS CloudTrail ingestion module
feat(cloud): Implement multi-source normalization layer
feat(cloud): Create cloud-extended entry point
feat(cloud): Deploy GCP Cloud Function proof-of-concept
docs(cloud): Document cloud architecture and enhancement plan
```

### Branch Hygiene

- **master**: Always working demo, interview-ready
- **cloud-extension**: Experimental, can break
- **No direct commits to master** during cloud work
- Tag releases: `v1.0-local`, `v2.0-cloud`

---

## Testing Strategy

### Unit Tests for New Components

**File**: `tests/test_cloud_ingestion.py`

```python
import unittest
from src.cloud.ingest_aws import load_aws_cloudtrail
from src.cloud.normalize import normalize_aws_event, normalize_evtx_event

class TestCloudIngestion(unittest.TestCase):
    
    def test_load_aws_cloudtrail(self):
        """Verify AWS CloudTrail ingestion"""
        events = load_aws_cloudtrail("data/cloud_logs/aws_cloudtrail")
        
        self.assertGreater(len(events), 0)
        self.assertTrue(all(e["source_type"] == "aws_cloudtrail" for e in events))
        self.assertTrue(all("source_file" in e for e in events))
    
    def test_normalize_aws_event(self):
        """Verify AWS normalization to common schema"""
        sample_aws = {
            "eventTime": "2024-01-15T10:23:45Z",
            "eventName": "GetBucketPolicy",
            "userIdentity": {"userName": "attacker"},
            "sourceIPAddress": "93.184.216.34"
        }
        
        normalized = normalize_aws_event(sample_aws)
        
        self.assertEqual(normalized["actor"], "attacker")
        self.assertEqual(normalized["action"], "GetBucketPolicy")
        self.assertEqual(normalized["source_ip"], "93.184.216.34")
        self.assertIn("raw_event", normalized)
    
    def test_cross_source_schema_compatibility(self):
        """Verify AWS and EVTX normalize to same schema"""
        # Normalized events from both sources should have same keys
        aws_normalized = normalize_aws_event({...})
        evtx_normalized = normalize_evtx_event({...})
        
        self.assertEqual(set(aws_normalized.keys()), set(evtx_normalized.keys()))
```

### Integration Test

**File**: `tests/test_multi_source_pipeline.py`

```python
def test_end_to_end_multi_source():
    """Verify multi-source pipeline works end-to-end"""
    from src.main_cloud import main
    
    # Should not raise exceptions
    main()
    
    # Verify outputs exist
    assert Path("db/security_analysis.db").exists()
    assert len(list(Path("reports").glob("analysis_*.txt"))) > 0
```

---

## Time Investment & Effort Estimates

### Detailed Breakdown

| Phase | Component | Hours | Dependencies |
|-------|-----------|-------|--------------|
| **2.1** | Download Kaggle dataset | 0.5 | Kaggle account |
| **2.1** | Create cloud module structure | 0.5 | None |
| **2.1** | Implement `ingest_aws.py` | 2.0 | Dataset downloaded |
| **2.1** | Test AWS ingestion | 1.0 | Ingestion code complete |
| **2.1** | Document AWS parser | 0.5 | - |
| **2.2** | Design normalization schema | 1.0 | None |
| **2.2** | Implement `normalize.py` | 3.0 | Schema defined |
| **2.2** | Write unit tests | 1.5 | Normalize code complete |
| **2.2** | Document schema mappings | 0.5 | - |
| **2.3** | Create `main_cloud.py` | 1.5 | Normalization done |
| **2.3** | Integration testing | 1.0 | All components ready |
| **2.3** | Debug and refine | 1.5 | - |
| **2.4** | GCP account setup | 0.5 | Credit card for verification |
| **2.4** | Write Cloud Function | 1.0 | GCP account ready |
| **2.4** | Deploy to GCP | 1.0 | Function code written |
| **2.4** | Test and screenshot | 0.5 | Deployment successful |
| **2.4** | Document experience | 1.0 | - |
| **2.5** | Update README | 0.5 | All phases done |
| **2.5** | Write architecture doc | 1.0 | - |
| **2.5** | Add code comments | 0.5 | - |
| **2.5** | Prepare interview Q&A | 1.0 | - |
| **TOTAL** | | **20.0** | |

### Critical Path

**Minimum Viable Demo** (12 hours):
1. AWS ingestion (3 hrs)
2. Normalization (4 hrs)
3. Cloud entry point (3 hrs)
4. Basic documentation (2 hrs)

**Full Implementation** (20 hours):
- Minimum + GCP deployment + comprehensive docs

### Schedule Options

**Option A: 2-Week Sprint**
- Week 1: Phases 2.1-2.2 (10 hrs, ~1.5 hrs/day)
- Week 2: Phases 2.3-2.5 (10 hrs, ~1.5 hrs/day)

**Option B: 3-Week Moderate Pace**
- Week 1: Phase 2.1 (6 hrs, ~1 hr/day)
- Week 2: Phase 2.2-2.3 (8 hrs, ~1.5 hrs/day)
- Week 3: Phase 2.4-2.5 (6 hrs, ~1 hr/day)

**Option C: Minimum Viable (1 Week)**
- Skip GCP deployment
- Focus on AWS + normalization + docs
- 12 hours total

---

## Decision Framework

### Go/No-Go Decision Criteria

**Proceed with Implementation IF**:
- ✅ Core PurpleLens lessons 01, 03, 04 completed
- ✅ At least 2 weeks before interview
- ✅ Can commit 1.5 hours/day for 2 weeks
- ✅ Comfortable with current demo
- ✅ Want to demonstrate cloud/pipeline skills

**Defer to Post-Interview IF**:
- ⚠️ Interview is in < 2 weeks
- ⚠️ Still studying core lessons
- ⚠️ Current demo not solid
- ⚠️ Limited time availability
- ⚠️ Risk-averse about breaking working code

**Use as Interview Talking Point ONLY IF**:
- 📋 No time for implementation
- 📋 Want to show architectural thinking
- 📋 Discuss as "future enhancement"
- 📋 Demonstrate planning discipline

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Break existing demo | Low | High | Branch strategy, no changes to master |
| Run out of time | Medium | Medium | Phases are independent, can stop anytime |
| Dataset download issues | Low | Medium | Backup: Use synthetic data |
| GCP deployment fails | Medium | Low | Optional component, can skip |
| Interview before completion | Medium | Low | Partial work still valuable |
| Code doesn't integrate cleanly | Low | Medium | Composition pattern minimizes coupling |

### Success Scenarios

**Scenario 1: Full Implementation**
- All phases complete
- Both demos work (local + cloud)
- GCP deployment proven
- **Interview Impact**: ⭐⭐⭐⭐⭐

**Scenario 2: Core Cloud Features**
- AWS ingestion + normalization done
- Skip GCP deployment
- Documentation complete
- **Interview Impact**: ⭐⭐⭐⭐

**Scenario 3: Planning Only**
- This document exists
- No code written
- Discussed as "future work"
- **Interview Impact**: ⭐⭐⭐

---

## Interview Preparation

### Demo Script

**Part 1: Original Demo (3 minutes)**
```
[On master branch]
$ git checkout master
$ python src/main.py

"This is the original PurpleLens demo. It analyzes Windows EVTX files 
using LLM-augmented security analysis. The architecture enforces that 
AI operates post-trust-boundary on structured, validated data. Let me 
show you the output..."

[Show report, explain findings]
```

**Part 2: Cloud Extension Demo (5 minutes)**
```
[Switch to cloud branch]
$ git checkout cloud-extension
$ python src/main_cloud.py

"This is the cloud-extended version. Notice it loads both EVTX and AWS 
CloudTrail logs. Here's what's important: I built a normalization layer 
that maps different source formats to a common schema. AWS calls it 
'principalEmail', we normalize it to 'actor'. Windows EVTX has 'EventID', 
AWS has 'eventName', both become 'event_id' in our schema.

Once normalized, the SAME analysis code runs on both sources. I didn't 
rewrite llm_analyze.py—I reused it. This proves the architecture is 
source-agnostic, which is exactly how production SOCs handle dozens of 
log sources.

The cloud dataset is from flaws.cloud on Kaggle—real attack patterns 
from AWS misconfigurations. Let me show you a finding..."

[Show report with AWS events analyzed]
```

**Part 3: GCP Deployment (2 minutes)**
```
[Show GCP Console screenshot]

"To demonstrate hands-on cloud experience, I deployed this Cloud Function 
to GCP. It's minimal—just proves I can work with cloud platforms and 
understand managed services. In production, this would pull audit logs 
via Pub/Sub and feed them into the pipeline.

[Show function response]

The key insight: I could build a full GCP ingestion pipeline, but that 
would be over-engineering for an interview. Instead, I proved the concept 
and focused time on the normalization architecture, which is the harder 
problem."
```

### Key Talking Points

**Architecture**:
- "Source → Parse → Normalize → Enrich → Store → Analyze"
- "Trust boundary between untrusted raw logs and validated structured data"
- "Normalization enables source-agnostic analysis"
- "Existing code reused via composition, not rewritten"

**Engineering Decisions**:
- "Used Kaggle dataset instead of generating own logs—pragmatic choice"
- "Branch strategy kept original demo safe while experimenting"
- "Parallel module structure shows modular design thinking"
- "Minimal GCP deployment proves capability without over-engineering"

**Data Pipeline Patterns**:
- "Source diversity requires normalization layer"
- "Common schema enables cross-source correlation"
- "Provenance preserved through raw_event field"
- "Future sources just need new normalize_X functions"

**Cloud Experience**:
- "Deployed Cloud Function to GCP"
- "Understand Cloud Logging API and audit log structure"
- "Know when to use managed services vs custom code"
- "Practiced infrastructure-as-code with gcloud CLI"

### Interview Questions & Model Answers

**Q: "How would you scale this to handle millions of events?"**

**A**: "Three changes. First, replace file-based ingestion with streaming—Pub/Sub on GCP or Kinesis on AWS. Events flow in real-time instead of batch. Second, replace SQLite with BigQuery or Athena for distributed storage and SQL-scale queries. Third, deploy the analysis layer as containerized microservices on Cloud Run or ECS, so they auto-scale based on event volume. The normalization layer stays the same—it's the storage and compute layers that need to scale. The architecture already supports this because ingestion, analysis, and storage are decoupled."

---

**Q: "Why not just use a SIEM like Splunk or Elastic?"**

**A**: "SIEMs are excellent for log aggregation and rule-based detection. PurpleLens is a research project exploring LLM-augmented analysis with strong provenance guarantees. The value proposition is AI-generated explanations in plain English with MITRE ATT&CK context, not just alerts. That said, PurpleLens could feed INTO a SIEM as an enrichment source—our findings become additional context fields. In production, you'd want both: SIEM for breadth and real-time alerting, PurpleLens for depth and analyst assistance."

---

**Q: "What cloud security logs would you prioritize adding next?"**

**A**: "Three priorities. First, GCP Cloud Audit Logs—every API call, every identity action, critical for cloud infrastructure security. Second, Kubernetes audit logs if the org runs containers—pod creation, role bindings, API server activity. Third, Cloud Identity/SSO logs—authentication, MFA events, session management. These three cover control plane security. I'd defer data plane logs like VPC flow logs until we have the control plane instrumented because most cloud breaches involve identity and IAM, not network-level exploits. The normalization architecture already supports this—just add normalize_gcp() and normalize_k8s() functions."

---

**Q: "How do you ensure the LLM doesn't hallucinate security findings?"**

**A**: "Three mechanisms. First, the trust boundary—AI only operates on validated, structured data after parsing and normalization. No hallucinated events can enter the system. Second, temperature controls—we use low temperature (0.1-0.3) for factual analysis, not creative storytelling. Third, constrained prompting—we ask for specific MITRE ATT&CK technique IDs, not open-ended threat narratives. The prompt includes: 'Base your analysis ONLY on the provided events. Do not invent scenarios.' Post-processing validates that cited technique IDs exist in MITRE. Finally, we preserve raw events in every output so analysts can verify claims. If the LLM says 'saw credential dumping', the analyst can check the original EVTX event."

---

**Q: "Walk me through your git branching strategy and why you chose it."**

**A**: "I used a feature branch called 'cloud-extension' while keeping master pristine. This was a risk management decision—I had a working demo that I didn't want to break 3 days before an interview. The branch let me experiment freely. If cloud integration failed, I could abandon the branch and demo the original. If it succeeded, I could merge. This also shows version control discipline: master is always deployable, feature branches are where experiments happen. In a team setting, this would be a pull request workflow with code review before merging. The key is: never commit broken code to master."

---

## Future Enhancements (Post-Interview)

### Phase 3: Production Hardening

If implemented post-interview, consider:

**Streaming Pipeline**:
- Pub/Sub for event ingestion
- Cloud Functions triggered by Pub/Sub messages
- Real-time processing (< 1 second latency)

**Advanced Storage**:
- BigQuery for structured queries at scale
- Cloud Storage for archival (Parquet format)
- Partitioned tables by timestamp

**Observability**:
- Cloud Monitoring dashboards
- Alerting on pipeline failures
- Cost tracking and optimization

**Security**:
- Service account least-privilege IAM
- Secret Manager for API keys
- VPC Service Controls for data isolation

### Phase 4: Additional Sources

**Priority 1**:
- GCP Cloud Audit Logs
- Sysmon (enhanced Windows telemetry)
- Azure Activity Logs

**Priority 2**:
- Kubernetes audit logs
- Application logs (OWASP Top 10 patterns)
- Network flow logs (VPC Flow, NSG)

**Priority 3**:
- Container security events
- Cloud Identity/SSO logs
- Database audit logs

### Phase 5: Advanced Analysis

**LLM Improvements**:
- Multi-model ensemble (GPT-4 + Claude + local models)
- Fine-tuned models on security data
- Chain-of-thought reasoning for complex attacks

**Detection Engineering**:
- Automated MITRE ATT&CK technique tagging
- Threat hunt query generation
- IOC extraction and correlation

**Visualization**:
- Attack timeline reconstruction
- Entity relationship graphs
- Geospatial IP mapping

---

## Appendix A: Dataset Details

### Kaggle Dataset Metadata

**Full Name**: AWS CloudTrails Dataset from flaws.cloud  
**URL**: https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud  
**Size**: ~500 MB  
**Format**: JSON (standard CloudTrail format)  
**Events**: ~50,000+ CloudTrail events  
**Time Range**: 2017-2018 (from original flaws.cloud CTF)  

**Sample Event Types**:
- `GetBucketPolicy` - S3 bucket permission checks
- `PutBucketPolicy` - S3 bucket policy modifications
- `AssumeRole` - IAM role assumption
- `GetCallerIdentity` - Identity verification
- `ListBuckets` - S3 enumeration
- `GetObject` - S3 object access

**Attack Patterns Included**:
- Public S3 bucket misconfiguration
- IAM privilege escalation
- Unauthorized API access
- Credential exposure
- Lateral movement via role assumption

### Alternative Datasets (If Kaggle Unavailable)

**Option 1**: Synthetic Generation
- Use script provided in this document
- Control attack patterns
- Immediate availability

**Option 2**: AWS Security Analytics Bootstrap
- GitHub: https://github.com/awslabs/aws-security-analytics-bootstrap
- Official AWS sample datasets
- Requires AWS account to generate

**Option 3**: Splunk Boss of the SOC
- GitHub: https://github.com/splunk/botsv3
- Multi-source security datasets
- Includes AWS CloudTrail among others

---

## Appendix B: Code Templates

### Template: normalize_X_event()

```python
def normalize_X_event(x_event: dict) -> dict:
    """
    Normalize [SOURCE NAME] events to common security schema.
    
    Args:
        x_event: Raw event dictionary from [SOURCE]
        
    Returns:
        Normalized event dictionary with standard fields
        
    Raises:
        KeyError: If required fields missing
        ValueError: If data validation fails
    """
    # Extract source-specific fields
    timestamp = x_event.get("[TIMESTAMP_FIELD]")
    actor = x_event.get("[USER_FIELD]", "UNKNOWN")
    action = x_event.get("[ACTION_FIELD]")
    
    # Validate required fields
    if not timestamp or not action:
        raise ValueError(f"Missing required fields in {x_event}")
    
    # Map to common schema
    return {
        "timestamp": _standardize_timestamp(timestamp),
        "source_type": "[SOURCE_TYPE_CONSTANT]",
        "event_id": action,
        "severity": _assess_severity(x_event),
        "actor": actor,
        "action": action,
        "resource": _extract_resource(x_event),
        "source_ip": x_event.get("[IP_FIELD]", "UNKNOWN"),
        "outcome": _determine_outcome(x_event),
        "raw_event": x_event,
        "provenance": {
            "source_file": x_event.get("source_file"),
            "source_type": "[SOURCE_TYPE_CONSTANT]"
        }
    }

def _assess_severity(event: dict) -> str:
    """Determine severity based on source-specific logic"""
    # Implement source-specific severity logic
    pass

def _extract_resource(event: dict) -> str:
    """Extract affected resource from source-specific fields"""
    # Implement source-specific resource extraction
    pass

def _determine_outcome(event: dict) -> str:
    """Determine success/failure from source-specific fields"""
    # Implement source-specific outcome logic
    pass
```

---

## Appendix C: Checklist

### Pre-Implementation

- [ ] Core lessons 01, 03, 04 completed
- [ ] Original demo working and understood
- [ ] At least 2 weeks until interview
- [ ] Can commit 1.5 hrs/day for 2 weeks
- [ ] Git installed and configured
- [ ] Python environment set up
- [ ] Kaggle account created

### Phase 2.1: AWS Ingestion

- [ ] Kaggle dataset downloaded (500MB)
- [ ] Dataset extracted to `data/cloud_logs/aws_cloudtrail/`
- [ ] Feature branch created: `cloud-extension`
- [ ] `src/cloud/` directory created
- [ ] `src/cloud/ingest_aws.py` implemented
- [ ] Unit test written and passing
- [ ] Provenance metadata verified
- [ ] Error handling tested

### Phase 2.2: Normalization

- [ ] `NormalizedSecurityEvent` schema defined
- [ ] `src/cloud/normalize.py` created
- [ ] `normalize_aws_event()` implemented
- [ ] `normalize_evtx_event()` implemented
- [ ] Unit tests for both normalizers
- [ ] Schema compatibility verified
- [ ] Documentation written

### Phase 2.3: Cloud Entry Point

- [ ] `src/main_cloud.py` created
- [ ] Multi-source ingestion implemented
- [ ] Normalization integrated
- [ ] Existing modules composed (not modified!)
- [ ] Integration test passing
- [ ] Original `main.py` still works
- [ ] Both demos verified side-by-side

### Phase 2.4: GCP Deployment (Optional)

- [ ] GCP free tier account created
- [ ] `gcloud` CLI installed
- [ ] Cloud Function code written
- [ ] Function deployed to GCP
- [ ] HTTP endpoint tested
- [ ] Screenshots captured (console + response)
- [ ] Deployment documented

### Phase 2.5: Documentation

- [ ] README updated with cloud architecture
- [ ] `docs/Cloud_Architecture.md` created
- [ ] Code comments added throughout
- [ ] Normalization schema documented
- [ ] Interview talking points prepared
- [ ] Demo script rehearsed

### Pre-Interview

- [ ] Master branch clean and working
- [ ] Cloud extension branch working (if implemented)
- [ ] Can switch between branches smoothly
- [ ] Screenshots organized
- [ ] Architecture diagram ready
- [ ] Practice demo completed 3+ times
- [ ] Interview Q&A rehearsed

---

## Appendix D: Emergency Rollback Plan

If cloud extension breaks and interview is imminent:

```powershell
# 1. Immediately switch to master
git checkout master

# 2. Verify original demo works
python src/main.py

# 3. Stash or delete cloud branch (optional)
git branch -D cloud-extension  # Delete local branch
git push origin --delete cloud-extension  # Delete remote

# 4. Interview narrative shift
# "I explored cloud extensions on a feature branch but decided to focus
#  on perfecting the core demo. I can discuss the architecture I designed
#  for multi-source ingestion, but the working demo you see is the 
#  battle-tested local version."

# 5. Show this planning document
# "Here's the enhancement plan I created. I made a pragmatic decision
#  to not implement it before the interview to avoid risk."
```

**This shows**:
- Risk management
- Version control discipline
- Prioritization skills
- Honest communication

---

## Appendix E: Quick Reference

### Commands Cheat Sheet

```powershell
# Create feature branch
git checkout -b cloud-extension

# Switch to original demo
git checkout master

# Switch to cloud demo
git checkout cloud-extension

# Run original demo
python src/main.py

# Run cloud demo
python src/main_cloud.py

# Deploy GCP function
gcloud functions deploy purplelens-audit-log-ingest --runtime python311 --trigger-http

# Download Kaggle dataset
# (Manual: Visit kaggle.com, download ZIP, extract)

# Verify dataset
Get-ChildItem "data/cloud_logs/aws_cloudtrail" -Filter *.json | Measure-Object

# Run tests
python -m pytest tests/test_cloud_ingestion.py

# Check git status
git status

# View branches
git branch -a
```

### File Paths Reference

```
Main Scripts:
  - Original: src/main.py
  - Cloud:    src/main_cloud.py

Core Modules (UNCHANGED):
  - src/ingest.py
  - src/llm_analyze.py
  - src/security.py
  - src/storage.py
  - src/report.py

New Cloud Modules:
  - src/cloud/ingest_aws.py
  - src/cloud/normalize.py
  - src/cloud/storage_bq.py (future)

Data:
  - EVTX:  data/evtx_parsed/
  - Cloud: data/cloud_logs/aws_cloudtrail/

Documentation:
  - This plan: docs/Cloud_Enhancement_Plan.md
  - Architecture: docs/Cloud_Architecture.md
  - Original: docs/ARCHITECTURE.md
```

### Time Estimates

```
Minimum Viable:  12 hours
Full Implementation:  20 hours
With GCP Deployment:  24 hours
Planning Only:  2 hours (read this doc)
```

---

## Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-22 | Initial planning document created | GitHub Copilot |

---

**END OF DOCUMENT**

This plan can be executed, deferred, or referenced as a design artifact. The choice depends on interview timeline and progress with core PurpleLens lessons.

**Key Principle**: Better to have a perfect working demo of the original than a broken cloud extension. This document ensures cloud thinking is captured regardless of implementation status.
