# PurpleLens SOC - Enhancement 1 NorthStar (AWS CloudTrail Branch)

Branch name: `enhancement/aws-cloudtrail`
Owner roles: Architect -> Overseer (reviewer, enhancer, troubleshooter, approver, tester) -> Primary Engineer (execution)
---

## 1) Why this enhancement exists (interview-aligned)

This branch exists to demonstrate that PurpleLens is a log-agnostic SOC analysis harness:

- It can ingest and normalize a different artifact type (AWS CloudTrail).
- It can use an LLM only for structured extraction (no actions, no false authority).
- It produces a deterministic, evidence-cited SOC report and persists to SQLite for auditability.

Directly support and enhancement of PurpleLens project:
- ingest + analyze + (light) correlate security artifacts with GenAI context,
- produce a clear final report,
- demonstrate code quality + security acumen + prompting strategy.

---

## 2) Non-negotiable architecture invariants (do not change)

These remain identical to the Windows EVTX branch:

1) LLM is extraction-only  
   - Output must be JSON-only and schema-validated (Pydantic).
2) Evidence is mandatory  
   - Each key claim references `source_file` + `record_index` (or equivalent provenance).
3) Python writes the report  
   - Deterministic formatting; LLM does not write narrative.
4) Policy guardrails run after schema validation  
   - Block "I blocked", "I remediated", or any claims of completed actions.
5) SQLite persistence  
   - Store run metadata + structured findings + final report text.

---

## 2.5) Technical specifications (required for implementation)

### Auto-detect strategy
```python
# Detection order:
# 1. File extension (.evtx, .json, .jsonl)
# 2. Content sniffing (first 512 bytes)
# 3. Schema validation (CloudTrail has "Records" array or "eventVersion" field)
# 4. Fail with clear error if ambiguous

# Acceptance:
# - Mixed directory (EVTX + JSON) without --source flag must error
# - Detection decision logged explicitly
# - --source flag always overrides auto-detection
```

### LLM configuration
```python
LLM_CONFIG = {
    "model": "gpt-4-turbo",  # or specify actual model
    "max_tokens": 4096,
    "temperature": 0.0,  # deterministic extraction
    "context_window": 128000,  # but batch conservatively for compatibility
}
```

### Correlation parameters
```python
CORRELATION_CONFIG = {
    "time_window_seconds": 300,  # 5 minutes
    "max_cluster_size": 50,      # prevent runaway grouping
    "cluster_by": ["actor", "resource", "src_ip"],  # separate strategies
}

# Cluster ID generation:
# cluster_id = f"{strategy}_{hash(sorted_event_ids)[:8]}"

# Acceptance test:
# - Same actor, 2 events 4 min apart → same cluster
# - Same actor, 2 events 6 min apart → different clusters
# - 51 events same actor → multiple clusters (size cap)
```

### Prompt batching budget
```python
PROMPT_CONFIG = {
    "max_events_per_batch": 25,  # tune based on model
    "max_prompt_tokens": 6000,   # leave room for response
}

# Batching strategy:
# - Group correlated events into batches
# - Each batch gets separate LLM call
# - Merge structured outputs after validation
# - Track batch_id in evidence for replay
```

### Error handling policy
```python
ERROR_HANDLING = {
    "malformed_json": "log warning, skip record, continue",
    "missing_required_field": "log warning, skip record, continue",
    "llm_response_invalid_json": "fail run with clear error",
    "llm_response_schema_violation": "fail run with clear error",
    "llm_response_guardrail_violation": "fail run with clear error",
}

# Logging:
# - Structured logs (JSON) with levels
# - Separate error.log for interview review
# - Include failure_count in run metadata (SQLite)
```

### Security and redaction
```python
REDACT_FIELDS = [
    "responseElements.credentials",  # temp creds in AssumeRole
    "requestParameters.password",
    "userAgent",  # may contain internal tool names
]

# Storage:
# - raw_hash stored, NOT full raw record (except in-memory during run)
# - Evidence persists only minimal replay fields
# - No secrets in SQLite database
```

---

## 3) Scope (tight for demo purposes)

In scope:
- CloudTrail dataset ingestion (Kaggle Flaws CloudTrail set)
- Normalization into the PurpleLens event envelope
- Minimal correlation primitives (same actor / same resource / same time-window)
- Same single-run CLI experience: `python -m src.main --input ...`
- Small demo dataset (e.g., 50-200 events) to keep LLM prompts stable

Out of scope (explicit):
- Real-time streaming / tailing
- Full AWS service coverage / full CloudTrail schema modeling
- Auto-remediation, determinations, or "we blocked X"
- Complex graph correlation across accounts/orgs
- Multi-tenant/enterprise RBAC or DB migrations (SQLite stays)

---

## 4) Core design: Adapter, not rewrite

Only the ingestion adapter changes.  
Everything downstream uses the same pipeline and contracts.

### Normalized event envelope (conceptual)
Each CloudTrail record becomes:

- `source_file`: path to file
- `record_index`: line/index in file
- `event_time`: parsed timestamp
- `provider`: "aws"
- `plane`: "control" / "data" / "telemetry" / "unknown" (heuristic mapping)
- `actor`: `userIdentity.arn` or `principalId`
- `actor_type`: `AssumedRole` / `IAMUser` / `AWSService` / etc
- `action`: `eventSource` + `eventName`
- `resource`: best-effort resource identifier(s) from `resources[]` / requestParameters
- `src_ip`: `sourceIPAddress`
- `user_agent`: `userAgent`
- `outcome`: `errorCode`/`errorMessage` or "success" if absent
- `raw`: original record kept in memory for prompt; persist `raw_hash` (SHA-256) plus minimal replay fields (fixed set: `source_file`, `record_index`, `event_time`, `actor`, `action`, `resource`) inside evidence JSON (stored in persisted evidence objects)

The goal is SOC reasoning portability, not perfect AWS modeling.

---

## 5) Phased execution plan (engineer executes one phase at a time)

### Phase 0 - Branch scaffold + guardrail continuity (low risk)
Goal: Create the branch skeleton without changing the core pipeline.

Engineer tasks:
- Create branch `enhancement/aws-cloudtrail`
- Add `src/ingest_aws.py` (new adapter)
- Add a minimal fixture directory (e.g., `data/aws_cloudtrail_sample/`)
- Update CLI to accept `--source aws|windows` (optional, default = auto-detect; `--source` overrides)
- Ensure existing Windows flow still works

Overseer acceptance checks:
- Windows EVTX workflow passes unchanged
- All tests still pass
- No new "LLM writes narrative" path introduced

---

### Phase 1 - CloudTrail parsing + normalization (core work)
Goal: Convert CloudTrail JSON/JSONL records into the normalized event envelope.

Engineer tasks:
- Parse dataset format (Kaggle may be JSON files, JSON arrays, or JSONL)
- Implement robust parsing:
  - skip malformed lines with clear errors
  - record provenance (`source_file`, `record_index`)
- Create `normalize_cloudtrail_record(record) -> NormalizedEvent`
- Keep normalized events in memory for prompt context (no new DB tables)
- Ensure analysis-run persistence remains unchanged (run metadata + structured outputs + report stored)

**Normalization field handling:**
```python
# CloudTrail records have inconsistent field presence

REQUIRED_FIELDS = ["eventTime", "eventSource", "eventName"]

OPTIONAL_WITH_DEFAULTS = {
    "actor": lambda rec: extract_actor(rec) or "SYSTEM",
    "actor_type": lambda rec: rec.get("userIdentity", {}).get("type", "Unknown"),
    "resource": lambda rec: extract_resources(rec) or ["NONE"],
    "plane": lambda rec: infer_plane(rec) or "unknown",
}

# Validation:
# - Skip records missing REQUIRED_FIELDS (log warning with source_file + index)
# - Populate OPTIONAL_WITH_DEFAULTS deterministically

# Resource extraction (Phase 1: simple; Phase 2: enhanced):
# CloudTrail resources appear in 3 places:
# 1. resources[] array (ARNs) - USE THIS IN PHASE 1
# 2. requestParameters (nested, service-specific) - PHASE 2 HEURISTICS
# 3. responseElements (often empty or redacted) - IGNORE

def extract_resources(rec: dict) -> list:
    """Phase 1: resources array only"""
    resources = rec.get("resources", [])
    return [r.get("ARN", "UNKNOWN") for r in resources] if resources else []

def extract_actor(rec: dict) -> str:
    """Fallback chain for actor extraction"""
    ui = rec.get("userIdentity") or {}
    return ui.get("arn") or ui.get("principalId") or ui.get("accountId") or None
```

Example snippet (complete):
```python
def normalize_cloudtrail_record(rec: dict, source_file: str, idx: int) -> dict:
    # Validate required fields
    for field in REQUIRED_FIELDS:
        if not rec.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    ui = rec.get("userIdentity") or {}
    return {
        "provider": "aws",
        "source_file": source_file,
        "record_index": idx,
        "event_time": rec.get("eventTime"),
        "actor": extract_actor(rec) or "SYSTEM",
        "actor_type": ui.get("type", "Unknown"),
        "action": f"{rec.get('eventSource')}:{rec.get('eventName')}",
        "src_ip": rec.get("sourceIPAddress", "UNKNOWN"),
        "user_agent": rec.get("userAgent", "UNKNOWN"),
        "outcome": "failure" if rec.get("errorCode") else "success",
        "raw": rec,
        "plane": infer_plane(rec) or "unknown",
        "resource": extract_resources(rec) or ["NONE"],
    }
```

Overseer acceptance checks:
- Ingests N records deterministically (same count every run)
- Every normalized event has provenance fields populated
- Malformed record handling is explicit and logged

---

### Phase 2 - Plane tagging + minimal correlation hooks (small but valuable)
Goal: Demonstrate cloud security intuition: planes + "connect the dots" basics.

Engineer tasks:
- Add plane tagging heuristics (deterministic):
```python
CONTROL_PLANE_ACTIONS = {
    "iam.amazonaws.com": "*",  # all IAM actions
    "sts.amazonaws.com": "*",  # all STS actions
    "organizations.amazonaws.com": "*",
    "cloudtrail.amazonaws.com": ["StopLogging", "DeleteTrail", "UpdateTrail"],
}

DATA_PLANE_INDICATORS = {
    "eventName_suffix": ["Object", "Item", "Record"],  # GetObject, PutItem
}

TELEMETRY_SERVICES = [
    "guardduty.amazonaws.com",
    "cloudwatch.amazonaws.com",
    "config.amazonaws.com",
]

def infer_plane(rec: dict) -> str:
    event_source = rec.get("eventSource", "")
    event_name = rec.get("eventName", "")
    
    if event_source in TELEMETRY_SERVICES:
        return "telemetry"
    if event_source in CONTROL_PLANE_ACTIONS:
        return "control"
    if any(event_name.endswith(suffix) for suffix in DATA_PLANE_INDICATORS["eventName_suffix"]):
        return "data"
    
    return "unknown"
```

- Add minimal correlation in preprocessing (before LLM prompt):
  - cluster by actor within time window (300 seconds)
  - cluster by resource identifiers
  - add derived fields: `cluster_id`, `cluster_size`
  - use correlation config from section 2.5

Overseer acceptance checks:
- Heuristics are deterministic and unit-tested
- Correlation does not change or invent facts; it only groups events

---

### Phase 3 - Prompt framing tuned for CloudTrail + schema validation (LLM contract unchanged)
Goal: Ensure the LLM sees the right context without letting it take control.

Engineer tasks:
- Define Pydantic schemas (provider-agnostic base):
```python
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class EvidenceItem(BaseModel):
    source_file: str
    record_index: int
    event_time: str
    actor: str
    action: str
    resource: str
    raw_hash: str  # SHA-256 of raw record
    batch_id: Optional[str] = None  # for multi-batch runs

class Finding(BaseModel):
    finding_id: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    evidence: List[EvidenceItem] = Field(..., min_items=1)  # MUST have evidence
    
class AWSFinding(Finding):
    """AWS-specific extensions (optional)"""
    account_id: Optional[str] = None  # extracted from ARN
    region: Optional[str] = None
```

- Update the extraction prompt template to include:
  - explicit instruction hierarchy
  - event provenance labels
  - "JSON only" response requirement
  - use prompt batching config from section 2.5
- Provide event batches with stable formatting using normalized fields:
  - `Event[12] source=... idx=... actor=... action=... resource=...`
  - Include the raw record only as an attached JSON block for evidence
- Validate output via Pydantic; fail closed if invalid

Overseer acceptance checks:
- Schema validation blocks malformed output
- Policy guardrails block false action claims
- Report generation still deterministic

---

### Phase 4 - Demo dataset + reproducibility notes (assignment-aligned)
Goal: Nail the "how and why dataset was chosen" requirement.

Engineer tasks:
- Curate a small, stable subset of the Kaggle dataset:
  - documented selection criteria (e.g., "IAM + STS + logging-related actions")
  - keep it small to avoid prompt overflow (target: 50-100 events)
- Add README section with **critical limitations disclosure**:

```markdown
## Dataset

### Source
- URL: https://www.kaggle.com/datasets/nobukim/aws-cloudtrails-dataset-from-flaws-cloud
- Origin: flaws.cloud (Scott Piper's AWS security training CTF)
- License: [Kaggle dataset license]

### **CRITICAL: This is synthetic data from a security challenge**

**Strengths:**
- Contains realistic IAM/STS/S3 patterns
- Known attack scenarios (credential exposure, privilege escalation)
- Well-structured CloudTrail format

**Weaknesses:**
- Limited service coverage (no EC2, Lambda, RDS, etc.)
- No cross-account activity
- No AWS service events (only user actions)
- Timing patterns are artificial
- Single-account perspective only

**This tool demonstrates the harness architecture, not production-grade AWS coverage.**

### Correlation Disclaimer

"Correlation" in this tool means:
- **Grouping by proximity** (same actor/resource within time window)
- **NOT proof of causation**
- **NOT attribution or determination**

Clustered events suggest relationships for analyst review; they do not constitute findings.
```

- Do not commit the full dataset; commit only a small derived sample if the Kaggle license permits

Overseer acceptance checks:
- Demo run completes reliably
- README is accurate and does not overclaim capabilities

---

### Phase 5 - Minimal test coverage (interview confidence)
Goal: Prevent regressions and prove adapter correctness.

Engineer tasks:
- Unit tests:
  - parsing a record (valid CloudTrail JSON)
  - normalization fields present and populated correctly
  - plane tagging heuristics (all cases: control/data/telemetry/unknown)
  - resource extraction fallback chain
  - actor extraction fallback chain
  - correlation clustering (time windows, cluster size caps)

- Negative test cases (critical):
  - Empty CloudTrail file (should error gracefully)
  - Malformed JSON (invalid escape sequences)
  - CloudTrail record with null userIdentity
  - Record missing required fields (eventTime, eventSource, eventName)
  - LLM returns "I blocked this attack" (guardrail violation - should fail)
  - LLM returns malformed JSON (schema validation - should fail)
  - LLM returns valid JSON with missing evidence (schema validation - should fail)
  - Mixed directory (EVTX + JSON) without --source flag (should error)

- Performance test:
  - 200 events completes in <60 seconds (reasonable for demo)

- Regression test:
  - Windows EVTX flow still passes after all phases (unchanged behavior)

- End-to-end test with mocked LLM:
  - verifies DB writes and report output
  - validates batch_id tracking for multi-batch scenarios
  - confirms error.log created and populated on parsing failures

Overseer acceptance checks:
- All tests pass locally with a single command (`pytest` or equivalent)
- Windows tests still pass (zero regression)
- Negative tests actually fail appropriately (not false passes)
- Coverage report shows >80% for new AWS adapter code

---

## 6) Interview narrative anchors (what you say out loud)

- "PurpleLens is a harness: ingestion -> constrained extraction -> deterministic report."
- "AWS support is an adapter: I normalized CloudTrail into the same evidence-first event envelope."
- "The LLM never acts; it extracts structured findings; Python writes the report and stores the audit trail."

---

## 7) Risks and mitigations (architect-level)

- Dataset format variability: handle JSON arrays vs JSONL; log and skip malformed records.
- Prompt size blowups: small curated subset; batch events; cap max events per run.
- Over-claim risk in docs: explicitly state "grouping != proof; no automated remediation."

---

## 8) Definition of Done (branch-level)

- `--source aws` (or auto-detect) runs end-to-end
- Schema validation + policy guardrails still enforce constraints
- SQLite contains run metadata + findings + report
- Tests cover normalization + one full mocked flow
- README documents dataset source and limitations without overclaiming
