# PurpleLens SOC — Enhancement 2 NorthStar (GCP Mini-Lab Log Generation + Ingest)

**Branch name:** `enhancement/gcp-mini-lab`  
**Owner roles:** Architect (you) → Overseer (review) → Primary Engineer (execute 1 phase at a time)  
**Timebox:** Designed for a **≤ 1-week** effort with **~40 hours max** total engineering time.

---

## 1) Correct goal statement (per your feedback)

**Goal:** Demonstrate **cloud security engineering intuition** by showing you understand:
- **planes** (control / data / telemetry),
- **identity + automation** (service accounts, CI/CD, Terraform),
- **blast radius reasoning** (scope depends on roles/permissions, not labels),
- **visibility pipeline risk** (logging sink changes, audit log trails),
- and how to build an **AI-assisted SOC workflow** that is evidence-first and audit-friendly.

This is not a “become a GCP product expert” exercise. Products change; the architecture patterns don’t.

---

## 2) Non‑negotiable architecture invariants (do not change)

Same invariants as the core PurpleLens tool:

1. **LLM is extraction-only** (JSON-only, schema-validated)
2. **Evidence required** (source_file + record_index referenced)
3. **Python writes the report** (deterministic)
4. **Policy guardrails** block false action claims
5. **SQLite persistence** for auditability and replay

---

## 3) Scope (tight and safe)

### In scope
- A tiny GCP “mini-lab” that generates a **small set** of high-signal audit events
- Export logs to **JSONL** in a PurpleLens-ingestable format
- Ingest those logs through a new adapter (or extend existing ingest to accept GCP JSONL)
- Demonstrate control-plane and telemetry-plane reasoning via report sections

### Out of scope (explicitly)
- Full GCP security engineering hardening
- Full IaC module library or enterprise policy-as-code
- Real-time streaming ingestion
- Automated remediation / determinations
- Building a production-grade multi-project SIEM pipeline

---

## 4) What “mini-lab” must generate (the event set)

Keep this to **6–10 event types max**, all high signal:

### A) Control plane (IAM + admin mutations)
- `CreateServiceAccountKey` (your anchor event)
- `SetIamPolicy` (binding changes)
- `CreateServiceAccount` (optional)
- `DeleteServiceAccountKey` (rotation / cleanup)

### B) Visibility pipeline mutations (telemetry plane risk)
- `logging.sinks.create` / `logging.sinks.update` / `logging.sinks.delete`
- (Optional) changes to log exclusions or retention if easy

### C) Automation identity footprints
- service account as actor
- cross-project/service-account actions (pivot-capable identity)
- gcloud / Terraform user-agent signals (execution method, not “human proof”)

> The point is to generate logs that let you narrate: “identity + plane + blast radius + visibility risk + evidence.”

---

## 4.5) Technical specifications (implementation-ready details)

### Source Detection Strategy
**Requirement:** Extend existing `detect_source()` in `main.py` to recognize GCP audit logs without breaking Windows/AWS detection.

**Detection Order:**
```python
# Step 1: Extension check (both .json and .jsonl supported)
# Step 2: Content sniffing (first 512 bytes)
#   - GCP markers: "protoPayload", "logName", "insertId"
#   - Handle wrappers: Pub/Sub may wrap in {"message": {"data": ...}}
#   - Bucket exports may have array wrapper or newline-delimited
#   - Differentiate from AWS: "Records", "eventVersion"
#   - Differentiate from Windows: "Event", "System"
# Step 3: Schema validation
#   - GCP: has protoPayload.serviceName + protoPayload.methodName
#   - AWS: has eventSource + eventName
#   - Windows: has Event.System.EventID

# JSON vs JSONL handling:
# - .json files: try parsing as array first, then single object
# - .jsonl files: newline-delimited (one record per line)
# - Auto-detect by attempting JSON array parse; if fails, treat as JSONL

# Acceptance:
# - Mixed directory (GCP + AWS + Windows) without --source flag must error
# - Detection decision logged explicitly
# - --source gcp|aws|windows always overrides auto-detection
# - Handles both JSON array exports and JSONL streaming formats
```

**Test cases:**
- Pure GCP directory (JSONL) → auto-detect "gcp"
- Pure GCP directory (JSON array) → auto-detect "gcp"
- Pure GCP with Pub/Sub wrapper → auto-detect "gcp"
- Pure AWS directory → auto-detect "aws" (no regression)
- Pure Windows directory → auto-detect "windows" (no regression)
- GCP + AWS mixed → error with clear message
- `--source gcp` override → force GCP even if ambiguous

---

### Plane Tagging Heuristics
**Requirement:** Conservative, deterministic classification with `unknown` fallback.

**Implementation:** `src/gcp_plane_tagging.py`

```python
"""Conservative GCP plane tagging for Phase 2."""

def tag_plane(service: str, method: str) -> str:
    """Tag GCP audit events into control/data/telemetry planes (conservative)."""
    service = (service or "").lower().strip()
    method = (method or "").strip()

    # Control plane (identity + admin + logging control + crypto key management)
    CONTROL_PLANE_SERVICES = {
        "iam.googleapis.com": "*",  # All IAM methods
        "cloudresourcemanager.googleapis.com": "*",  # Project/org admin
        "serviceusage.googleapis.com": "*",  # API enablement
        "cloudkms.googleapis.com": "*",  # KMS key rotation/deletion = blast radius event
    }
    
    # Logging sink operations are control plane (visibility risk)
    if service == "logging.googleapis.com":
        if method in {"CreateSink", "UpdateSink", "DeleteSink", 
                      "CreateExclusion", "UpdateExclusion", "DeleteExclusion"}:
            return "control"
        return "telemetry"  # Other logging operations
    
    # Check control plane services
    if service in CONTROL_PLANE_SERVICES:
        return "control"
    
    # Telemetry plane (monitoring, audit writes)
    TELEMETRY_SERVICES = {
        "monitoring.googleapis.com": "*",
        "cloudtrace.googleapis.com": "*",
    }
    
    if service in TELEMETRY_SERVICES:
        return "telemetry"
    
    # Data plane (object/data access) - minimal for this phase
    if service == "storage.googleapis.com":
        if method in {"storage.objects.get", "storage.objects.create", 
                      "storage.objects.delete", "storage.buckets.list"}:
            return "data"
    
    return "unknown"  # Conservative default
```

**Acceptance criteria:**
- 100% deterministic (no randomness, no external calls)
- Unit tests cover all services in lookup tables
- Default to "unknown" not "control"

---

### Schema Validation Requirements
**Current schema:** Existing `Evidence`, `Finding`, `AnalysisOutput` models in `schemas.py`

**GCP field mapping:**
```python
# Evidence.event_id maps to GCP's insertId (unique log entry ID)
#   - insertId is the GCP-native "source of truth" for log uniqueness
#   - MUST be included in evidence citations for auditability
#   - Format in report: "Evidence: insertId abc123... (file.jsonl:42)"
# Evidence.source_file = path to JSONL file
# Evidence.record_index = line number (0-indexed)
# Evidence.excerpt = relevant snippet from protoPayload or resource
```

**Report Evidence Format (GCP-specific):**
```python
# Example finding evidence output:
# "Evidence: insertId e4f7g8h9... from gcp_audit.jsonl line 42"
# "  Principal: user@example.com"
# "  Action: cloudkms.googleapis.com/RotateCryptoKeyVersion"
# "  Resource: projects/example/locations/us/keyRings/prod/cryptoKeys/data-encryption"

# This format makes insertId prominent for GCP practitioners
```

**Required fields validation:**
```python
REQUIRED_GCP_FIELDS = [
    "timestamp",
    "protoPayload.serviceName",
    "protoPayload.methodName",
]

# Optional with defaults:
OPTIONAL_WITH_DEFAULTS = {
    "insertId": lambda rec: rec.get("insertId", "UNKNOWN"),
    "severity": lambda rec: rec.get("severity", "DEFAULT"),
    "principalEmail": lambda rec: rec.get("protoPayload", {}).get(
        "authenticationInfo", {}).get("principalEmail", "SYSTEM"),
}
```

**Action:** No Pydantic model changes required; existing schema sufficient.

---

### LLM Prompt Strategy
**Requirement:** GCP-specific system prompt emphasizing cloud security context.

**Implementation:** `src/llm_analyze.py` → `_build_gcp_user_prompt()`

```python
def _build_gcp_user_prompt(events: List[Dict[str, Any]]) -> str:
    """Build GCP-specific analysis prompt."""
    prompt_parts = [
        "You are analyzing GCP Cloud Audit Logs for security relevance.",
        "",
        "Focus on:",
        "- Identity patterns (service accounts vs human principals)",
        "- Plane classification (control/data/telemetry)",
        "- Visibility pipeline mutations (logging sinks, exclusions)",
        "- Cross-project actions (potential lateral movement)",
        "- Automation signals (Terraform, gcloud, CI/CD user agents)",
        "",
        "Extract structured findings with evidence. Do NOT claim remediation or certainty.",
        "",
        f"Events to analyze ({len(events)} total):",
        "",
    ]
    
    for idx, event in enumerate(events, 1):
        raw = event.get("raw_event", {})
        prompt_parts.append(f"--- Event {idx} ---")
        prompt_parts.append(json.dumps(raw, indent=2))
    
    return "\n".join(prompt_parts)
```

**Acceptance criteria:**
- Prompt mentions GCP-specific terminology
- Emphasizes evidence-backed extraction
- No Windows/AWS terminology mixed in

---

### Batch Configuration
**Requirement:** Define batching parameters for GCP audit logs.

**Implementation:** `src/config_gcp.py`

```python
"""GCP-specific configuration constants."""

GCP_BATCH_CONFIG = {
    "max_events_per_batch": 25,  # Conservative (GCP logs can be verbose)
    "max_prompt_tokens": 6000,   # Leave room for response
}

GCP_CORRELATION_CONFIG = {
    "enabled": False,  # Phase 1: no correlation; Phase 2B: optional
    "time_window_seconds": 300,  # 5 minutes if enabled
    "max_cluster_size": 50,
    "cluster_strategies": ["actor_only"],  # Simple strategy
}
```

**Acceptance criteria:**
- Config module created and imported
- Batching enforced in `analyze_events()` for GCP source

---

### Error Handling Policy
**Requirement:** Explicit handling for malformed GCP audit logs.

```python
ERROR_HANDLING = {
    "malformed_json": "log warning, skip record, continue",
    "missing_required_field": "log warning with source_file + record_index, skip record",
    "invalid_timestamp": "log warning, use fallback timestamp, continue",
    "llm_response_invalid_json": "fail run with clear error",
    "llm_response_schema_violation": "fail run with clear error",
    "llm_response_guardrail_violation": "fail run with clear error",
}

# Logging format:
# WARNING: Skipping record 42 in gcp_audit.jsonl: Missing required field 'protoPayload.serviceName'
```

**Acceptance criteria:**
- Malformed records logged with provenance
- Run continues unless critical error
- Error counts included in analysis metadata

---

### Data Minimization Strategy
**Requirement:** Never persist full raw GCP audit logs to SQLite.

**Implementation:**
```python
import hashlib
import json

def compute_raw_hash(raw_event: dict) -> str:
    """Generate SHA-256 hash of raw GCP audit log."""
    canonical = json.dumps(raw_event, sort_keys=True)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

# Storage:
# - Store hash only: raw_hash field in evidence JSON
# - Store minimal replay fields: insertId, timestamp, serviceName, methodName
# - Full raw kept in memory during analysis only
# - Never write raw audit log to SQLite
```

**Acceptance criteria:**
- Database schema inspection shows no raw JSON columns
- Evidence JSON contains hash + minimal fields only

---

### Test Acceptance Criteria (Concrete Targets)

**Phase 1 Tests (Normalization):**
- ✅ Load GCP JSONL with provenance (1 test)
- ✅ Required fields validation (3 tests: valid, missing service, missing method)
- ✅ Optional field defaults (2 tests)
- ✅ Actor extraction fallback chain (3 tests)
- ✅ Timestamp parsing (2 tests: ISO format, fallback)
- ✅ Malformed JSON handling (1 test)
- **Subtotal:** 12 tests minimum

**Phase 2 Tests (Plane Tagging):**
- ✅ Control plane services (IAM, resource manager, KMS, logging sinks) (5 tests)
- ✅ Telemetry plane services (monitoring, trace, logging writes) (2 tests)
- ✅ Data plane (storage objects) (2 tests)
- ✅ Unknown fallback (2 tests)
- **Subtotal:** 11 tests minimum

**Phase 3 Tests (Enrichment):**
- ✅ Actor kind (service account vs human email) (3 tests)
- ✅ User agent tagging (terraform, gcloud, Cloud SDK, google-cloud-sdk, cloudbuild) (5 tests)
- ✅ Cross-project detection (2 tests)
- **Subtotal:** 10 tests minimum

**Phase 5 Tests (Integration):**
- ✅ Source detection (GCP JSONL auto-detect, GCP JSON array auto-detect, --source override) (3 tests)
- ✅ Mocked LLM full-flow (load → analyze → report → persist) (1 test)
- ✅ insertId evidence validation (appears in report) (1 test)
- ✅ Regression check (Windows/AWS tests still pass) (verification)
- **Subtotal:** 5 tests minimum

**Total Target:** ≥38 new GCP tests + 76 existing tests = 114 total

---

## 5) Phased execution plan (engineer executes ONE phase at a time)

### Phase 0 — Mini-lab blueprint (no code, just design artifacts)
**Goal:** Create a lab plan that is small, reproducible, and defensible.

**Engineer tasks**
- Produce `docs/GCP_MINILAB_PLAN.md` containing:
  - target project naming convention (e.g., `purplelens-lab-*`)
  - identities to use (1 human, 1 CI service account)
  - event checklist (6–10 event types)
  - safety notes (avoid real org assets)
- Define “export method” for logs to JSONL (conceptual)

**Overseer acceptance checks**
- [ ] `docs/GCP_MINILAB_PLAN.md` created and committed
- [ ] Event checklist defined (6-10 types, matches section 4 spec)
- [ ] Safety notes documented (no real org assets)
- [ ] Export method conceptually defined (gcloud logging read → JSONL)
- [ ] Source detection strategy documented (extends existing detect_source)
- [ ] Plane tagging heuristics table created
- [ ] No overclaiming (explicitly states demo/lab scope)

**Exit Criteria:**
- ✅ All checklist items complete
- ✅ Plan reviewed and approved by Overseer
- ✅ No ambiguity in event types or export strategy

---

### Phase 1 — Log export format + ingestion adapter (core pipeline piece)
**Goal:** Decide the JSONL shape and ensure PurpleLens can ingest it.

**Engineer tasks**
- Define a canonical JSONL record that preserves:
  - `protoPayload.serviceName`
  - `protoPayload.methodName`
  - `resource.type` + labels
  - `authenticationInfo.principalEmail`
  - `callerIp` + `callerSuppliedUserAgent`
  - timestamps
  - provenance fields: `source_file`, `record_index`
- Implement `src/ingest_gcp.py` (new adapter) that:
  - reads JSONL
  - normalizes into the same event envelope used elsewhere
  - persists normalized events

**Example snippet (illustrative)**
```python
def normalize_gcp_audit(rec: dict, source_file: str, idx: int) -> dict:
    pp = rec.get("protoPayload") or {}
    auth = pp.get("authenticationInfo") or {}
    md = pp.get("requestMetadata") or {}
    
    # Extract insertId (GCP-native unique identifier - critical for evidence)
    insert_id = rec.get("insertId", "UNKNOWN")
    
    # Use plane tagging function for accurate classification
    from src.gcp_plane_tagging import tag_plane
    plane = tag_plane(pp.get("serviceName"), pp.get("methodName"))
    
    return {
        "provider": "gcp",
        "source_file": source_file,
        "record_index": idx,
        "insert_id": insert_id,  # GCP-native unique ID (maps to Evidence.event_id)
        "event_time": rec.get("timestamp"),
        "plane": plane,
        "actor": auth.get("principalEmail"),
        "action": f'{pp.get("serviceName")}:{pp.get("methodName")}',
        "resource": pp.get("resourceName") or rec.get("resource", {}),
        "src_ip": md.get("callerIp"),
        "user_agent": md.get("callerSuppliedUserAgent"),
        "severity": rec.get("severity"),
        "raw": rec,  # Keep in memory for LLM context; hash for storage
    }
```

**Overseer acceptance checks**
- [ ] `src/ingest_gcp.py` created with required functions
- [ ] `src/config_gcp.py` created with batch/correlation config
- [ ] `src/gcp_plane_tagging.py` created with deterministic heuristics (includes KMS)
- [ ] `main.py` source detection extended (handles JSON/JSONL gracefully)
- [ ] JSON vs JSONL handling implemented (array vs newline-delimited)
- [ ] Pub/Sub/bucket wrapper detection handled gracefully
- [ ] Normalization deterministic (same input → same output)
- [ ] Required fields validation enforced (timestamp, serviceName, methodName)
- [ ] insertId extraction validated (UNKNOWN fallback if missing)
- [ ] Malformed record handling tested
- [ ] Provenance attached (source_file, record_index, insertId)
- [ ] Data minimization implemented (SHA-256 hash storage)
- [ ] 12+ normalization tests passing

**Exit Criteria:**
- ✅ Load N GCP records deterministically (JSON and JSONL formats)
- ✅ All provenance fields populated (including insertId)
- ✅ Plane tagging returns control/data/telemetry/unknown (KMS = control)
- ✅ Windows EVTX tests still pass (no regression)
- ✅ AWS CloudTrail tests still pass (no regression)

**Exit Criteria:**
- ✅ Load N GCP records deterministically
- ✅ All provenance fields populated
- ✅ Plane tagging returns control/data/telemetry/unknown
- ✅ Windows EVTX tests still pass (no regression)
- ✅ AWS CloudTrail tests still pass (no regression)

---

### Phase 2 — Plane-aware report sections (intuition on display)
**Goal:** Make the report explicitly reflect plane reasoning.

**Engineer tasks**
- Add deterministic section headings in the report (based on normalized `plane`):
  - Control Plane Findings
  - Telemetry/Visibility Pipeline Findings
  - Data Plane Observations (optional, if present)
- Ensure findings link to evidence indices (line numbers)

**Overseer acceptance checks**
- [ ] `src/report.py` updated with plane-aware section logic
- [ ] Section headers deterministic ("Control Plane Findings", "Telemetry/Visibility Findings")
- [ ] No LLM involvement in section generation
- [ ] Evidence citations intact (source_file + record_index in all findings)
- [ ] LLM prompt function `_build_gcp_user_prompt()` created
- [ ] GCP-specific terminology in prompt (no AWS/Windows mixing)
- [ ] 10+ plane tagging tests passing

**Exit Criteria:**
- ✅ Report displays plane sections when GCP events present
- ✅ Sections are empty if no findings for that plane
- ✅ All findings have evidence with line numbers
- ✅ Report generation remains 100% deterministic

---

### Phase 3 — “IaC/automation identity” enrichment (small, high value)
**Goal:** Make automation identity reasoning visible without deep GCP specifics.

**Engineer tasks**
- Add deterministic tags (best-effort) from userAgent strings:
  - `terraform`, `gcloud`, `cloudbuild`, `github-actions`, `Cloud SDK`, `google-cloud-sdk`, etc.
  - Note: Some older CI/CD scripts may use generic Cloud SDK agents without custom strings
- Add a derived field `actor_kind = human|service_account` by email pattern
- Add a derived "pivot indicator" when actor project != resource project (best-effort)

**User Agent Tagging Table:**
```python
AUTOMATION_SIGNALS = {
    "terraform": "iac",
    "gcloud": "cli",
    "Cloud SDK": "cli",
    "google-cloud-sdk": "cli",
    "cloudbuild": "ci_cd",
    "github-actions": "ci_cd",
    "jenkins": "ci_cd",
    "circleci": "ci_cd",
}
# Match case-insensitive substring in callerSuppliedUserAgent
```

**Overseer acceptance checks**
- [ ] Actor kind derivation implemented (email pattern matching)
- [ ] User agent tagging table defined (terraform, gcloud, cloudbuild, etc.)
- [ ] Cross-project detection logic implemented (actor project != resource project)
- [ ] No external API calls (100% deterministic)
- [ ] No claims of "proof" (only "indicators" or "signals")
- [ ] 9+ enrichment tests passing
- [ ] Documentation disclaims automation detection limitations

**Exit Criteria:**
- ✅ `actor_kind` field populated deterministically
- ✅ `automation_signal` field populated from user agent
- ✅ Cross-project indicator flagged when detected
- ✅ All enrichment logic unit tested
- ✅ No false certainty claims in documentation

---

### Phase 4 — Mini-lab “log pack” (the demo artifact)
**Goal:** Create a small, stable set of generated logs you can demo repeatedly.

**Engineer tasks**
- Create a **static** JSONL “log pack” in-repo (or downloadable artifact) with:
  - 1–2 examples per high-signal event type
  - consistent filenames and ordering
- Document how logs were produced (manual vs scripted) + strengths/weaknesses:
  - Strength: controlled ground truth, high signal
  - Weakness: not representative of full enterprise noise

**Overseer acceptance checks**
- [ ] Static log pack created in `data/gcp_minilab_sample/` directory
- [ ] 6-10 event types represented (1-2 examples each)
- [ ] Consistent filenames and ordering (deterministic)
- [ ] README or dataset doc created explaining:
  - How logs were generated (manual gcloud commands vs script)
  - Dataset strengths (controlled ground truth, high signal)
  - Dataset weaknesses (not representative of enterprise noise, limited service coverage)
  - Explicit scope disclaimer (demo/lab only, not production coverage)
- [ ] Log pack committed to git (small file size <100KB)

**Exit Criteria:**
- ✅ Log pack loads successfully via `--input data/gcp_minilab_sample/`
- ✅ Log pack is version-controlled (no drift between runs)
- ✅ Documentation explicitly states limitations
- ✅ No overclaiming of production readiness

---

### Phase 5 — Minimal tests (confidence under panel pressure)
**Goal:** Avoid surprises.

**Engineer tasks**
- Unit tests for:
  - normalization fields present
  - plane classification for known method/service combos
  - deterministic enrichment tags
- Mocked LLM full-flow test ensures report + DB writes

**Overseer acceptance checks**
- [ ] 38+ new GCP tests created and passing
- [ ] Test coverage:
  - Normalization (12 tests)
  - Plane tagging (11 tests - includes KMS)
  - Enrichment (10 tests - includes Cloud SDK)
  - Source detection (3 tests - includes JSON/JSONL)
  - Integration (5 tests - includes insertId validation)
- [ ] Regression verification: 76 existing tests still pass
- [ ] Total test count: ≥114 tests passing
- [ ] One-command execution: `python -m pytest tests/`
- [ ] Test execution time: <2 minutes for full suite
- [ ] No test failures, no skipped tests (unless explicitly documented)

**Exit Criteria:**
- ✅ All new tests passing
- ✅ Zero regression (Windows + AWS tests unchanged)
- ✅ Test coverage documented in test file headers
- ✅ Mocked LLM flow generates report + persists to SQLite
- ✅ insertId appears in evidence citations in generated reports

---

## 5.5) Phase 0+ Expansion Catalog (Roadmap to 50+ Events)

The Phase 0 mini-lab validates the harness with **8 high-signal events**. For production-grade coverage, the following expansion roadmap targets **50+ events** across all GCP security tiers.

### Tier 1: Core IAM Admin Activity (Next 10-15 Events)
**Service:** `iam.googleapis.com`  
**Log Type:** Admin Activity

**Critical Methods:**
- `DeleteServiceAccount` (Persistence removal)
- `CreateServiceAccount` (Identity creation)
- `DeleteServiceAccountKey` (Credential rotation/revocation)
- `UndeleteServiceAccount` (Restoration after deletion)
- `DisableServiceAccount` (Access suspension)
- `EnableServiceAccount` (Access restoration)

**Why They Matter:**
- Control who can do what (highest blast radius)
- Common in persistence and privilege escalation TTPs
- Expected in enterprise IAM hygiene workflows

---

### Tier 2: Logging & Telemetry Expansion (Defense Evasion)
**Service:** `logging.googleapis.com`  
**Log Type:** Admin Activity

**Critical Methods:**
- `UpdateExclusion` (Subtle visibility reduction without full sink deletion)
- `CreateExclusion` (Filter-based log suppression)
- `DeleteExclusion` (Restore previously excluded logs)
- `UpdateLogMetric` (Metric tampering)
- `DeleteLogMetric` (Remove security alerting metrics)

**Why They Matter:**
- Attackers reduce detection without outright deletion (lower noise)
- Critical for SIEM ingestion pipeline integrity
- Often precedes real attacks

---

### Tier 3: Pub/Sub Telemetry Routing (Pipeline Breakage)
**Service:** `pubsub.googleapis.com`  
**Log Type:** Admin Activity

**Critical Methods:**
- `CreateSubscription` (Add new log consumer)
- `DeleteSubscription` (Break SIEM ingestion)
- `UpdateSubscription` (Modify ACK deadline, filters)
- `DetachSubscription` (Disconnect from topic without deletion)
- `CreateTopic` (Create exfiltration pipeline)
- `DeleteTopic` (Remove logging destination)

**Why They Matter:**
- Logs generated but never consumed = silent detection failure
- Common misconfiguration during SIEM onboarding
- Difficult to detect without subscription health monitoring

---

### Tier 4: Workload Identity & GKE-Originated Events (Modern Auth)
**Services:** `iamcredentials.googleapis.com`, `container.googleapis.com`  
**Log Type:** Data Access + Admin Activity

**Key Patterns:**
- `GenerateAccessToken` with `principalSubject` containing:
  - `workloadIdentityPools/...`
  - `ns/<namespace>/sa/<k8s-service-account>`
- `GenerateIdToken` (OIDC token minting for service mesh)
- GKE cluster operations (`CreateCluster`, `UpdateCluster`, `DeleteCluster`)
- Node pool modifications (`CreateNodePool`, `SetNodePoolAutoscaling`)

**Why They Matter:**
- Differentiates keyless auth (preferred) vs key-based auth (risky)
- Common in GKE, Cloud Run, Dataflow workloads
- Misconfiguration leads to over-privileged workloads
- Expected knowledge for senior cloud security roles

---

### Tier 5: Cross-Project & Cross-Boundary Events (Blast Radius)
**Pattern Recognition Across Services**

**Scenarios to Simulate:**
1. **Cross-Project IAM Changes**
   - Service account in `Project A` modifying IAM policy in `Project B`
   - Org-level vs project-level scope differentiation

2. **Central CI/CD Patterns**
   - Service account in `cicd-project` deploying to `prod-project`
   - Terraform service account creating keys for other service accounts

3. **MSP / Multi-Tenant Patterns**
   - Service account with org-wide `roles/logging.admin`
   - Cross-folder resource access

**Why They Matter:**
- Enterprise reality (not single-project sandboxes)
- Lateral movement risk assessment
- Demonstrates senior-level reasoning

---

### Tier 6: Automation & IaC Provenance (Attribution Context)
**Pattern Recognition in Existing Logs**

**Key Indicators:**
- `callerSuppliedUserAgent` containing:
  - `Terraform/X.Y.Z`
  - `google-cloud-sdk/X.Y.Z`
  - `gcloud/X.Y.Z`
  - `Deployment Manager`
- `principalEmail` is service account (not human)
- Consistent request patterns (batch operations)

**Why They Matter:**
- Automation mistakes scale instantly
- Attribution: author (who wrote IaC) vs executor (which SA ran it)
- Differentiates intentional changes from human error
- Interviewers expect immediate recognition of IaC patterns

---

### Tier 7: KMS & Crypto Operations (Data Protection Layer)
**Service:** `cloudkms.googleapis.com`  
**Log Type:** Admin Activity + Data Access

**Critical Methods (Beyond Phase 0):**
- `EncryptCryptoKeyVersion` (Data encryption events)
- `DecryptCryptoKeyVersion` (Data decryption - high volume in prod)
- `UpdateCryptoKey` (Rotation policy changes)
- `UpdateCryptoKeyVersion` (State changes: enabled → disabled)
- `SetIamPolicy` on KMS resources (Crypto key access changes)

**Why They Matter:**
- Crypto blast radius events (DestroyCryptoKeyVersion = data loss)
- Compliance requirements (FIPS, encryption at rest)
- Differentiates envelope encryption vs direct encryption

---

### Tier 8: Audit Log Types (Coverage Completeness)
**Ensure Simulation of All Three Types:**

1. **Admin Activity Logs** (Default, always on)
   - IAM changes, resource creation/deletion, config changes
   - No cost, always available

2. **Data Access Logs** (Must be explicitly enabled)
   - Token generation (`GenerateAccessToken`)
   - Data reads/writes (`storage.objects.get`, `bigquery.tables.getData`)
   - High volume, cost implications

3. **System Events** (GCP-internal operations)
   - Automatic quota adjustments
   - GKE node auto-scaling
   - Rarely attacker-driven, provides context

**Why They Matter:**
- Interviewers expect you to know which log type requires enablement
- Cost vs coverage trade-offs (Data Access logs can be expensive)
- Different retention and analysis strategies per type

---

### Critical Fields to Include in All Simulated Logs
**Ensure Every Event Contains:**

**Mandatory (Section 4.5.2 Schema):**
- `insertId` (primary anchor)
- `timestamp` (RFC 3339)
- `severity` (DEFAULT, NOTICE, WARNING, ERROR)
- `logName` (e.g., `projects/X/logs/cloudaudit.googleapis.com%2Factivity`)
- `resource.type` (e.g., `service_account`, `gce_instance`, `k8s_cluster`)
- `resource.labels.project_id`

**Authentication Context:**
- `protoPayload.authenticationInfo.principalEmail`
- `protoPayload.authenticationInfo.principalSubject` (for workload identity)
- `protoPayload.authenticationInfo.serviceAccountKeyName` (if key-based)

**Authorization Context:**
- `protoPayload.authorizationInfo[].permission`
- `protoPayload.authorizationInfo[].granted` (true/false)
- `protoPayload.authorizationInfo[].resourceAttributes`

**Request Context:**
- `protoPayload.serviceName` (e.g., `iam.googleapis.com`)
- `protoPayload.methodName` (e.g., `SetIamPolicy`)
- `protoPayload.resourceName` (e.g., `projects/X/serviceAccounts/Y`)
- `protoPayload.request` (method-specific payload)
- `protoPayload.requestMetadata.callerIp`
- `protoPayload.requestMetadata.callerSuppliedUserAgent`

**Response Context (if applicable):**
- `protoPayload.response` (created resource details)
- `protoPayload.status.code` (0 = success, non-zero = error)
- `protoPayload.status.message` (error description)

---

### High-Value Scenarios for Expansion (Concrete Examples)
**When generating the remaining 42+ events, prioritize these patterns:**

1. **Terraform Service Account Updating Logging Sink Filter**
   - `callerSuppliedUserAgent: Terraform/1.5.0`
   - `methodName: logging.sinks.update`
   - `request.filter` excludes `cloudaudit.googleapis.com/activity`

2. **CI/CD Service Account Creating JSON Key for Another Service Account**
   - `principalEmail: cicd-runner@...iam.gserviceaccount.com`
   - `methodName: CreateServiceAccountKey`
   - `request.privateKeyType: TYPE_GOOGLE_CREDENTIALS_FILE`
   - Cross-project: creates key for SA in different project

3. **GKE Workload Generating Access Token via Workload Identity**
   - `principalSubject: principalSet://iam.googleapis.com/projects/.../locations/global/workloadIdentityPools/.../ns/default/sa/app-backend`
   - `methodName: GenerateAccessToken`
   - `callerIp: 10.x.x.x` (internal GKE IP)
   - `callerSuppliedUserAgent: google-cloud-go/v0.110.0`

4. **Pub/Sub Subscription Deletion Breaking SIEM Ingestion**
   - `methodName: pubsub.subscriptions.delete`
   - `resourceName: projects/siem-prod/subscriptions/stackdriver-to-splunk`
   - Impact: Logs generated but never consumed

5. **Cross-Project IAM Policy Change**
   - `principalEmail: terraform-runner@cicd-project.iam.gserviceaccount.com`
   - `methodName: SetIamPolicy`
   - `resourceName: projects/production-data/...`
   - Demonstrates lateral movement risk

6. **Benign but Scary Admin Activity Event**
   - `methodName: DestroyCryptoKeyVersion`
   - `principalEmail: backup-rotation@...iam.gserviceaccount.com`
   - `callerSuppliedUserAgent: google-cloud-sdk/412.0.0`
   - Context: Automated key rotation (expected behavior)

---

### Expansion Phasing Strategy
**How to Scale from 8 → 50+ Events:**

**Phase 0 (Current):** 8 events → Prove harness works  
**Phase 0.5:** +10 events (Tier 1 IAM) → 18 total  
**Phase 0.75:** +10 events (Tier 2 Logging + Tier 3 Pub/Sub) → 28 total  
**Phase 1 Completion:** +12 events (Tier 4 Workload Identity) → 40 total  
**Phase 2 Completion:** +10 events (Tiers 5-8 coverage) → 50 total  
**Beyond:** Continue to 100+ for enterprise realism

**Test Target Scaling:**
- Phase 0: 38 new tests (12 normalization + 11 plane tagging + 10 enrichment + 5 integration)
- Phase 0.5: +15 tests (additional plane tagging + edge cases)
- Phase 1: +20 tests (workload identity patterns, cross-project)
- Phase 2: +15 tests (full audit log type coverage)
- **Total at 50 events:** ~88 new GCP tests

---

## 6) Interview narrative anchors (what you say out loud)

- “I’m demonstrating **cloud security intuition**, not memorizing product trivia.”
- “This lab produces controlled examples of **identity and visibility pipeline mutations**.”
- “PurpleLens treats logs as untrusted input, forces evidence-backed extraction, and emits deterministic reporting with an audit trail.”

---

## 7) Risks & mitigations (architect-level)

- **Over-scope risk:** cap event types to 6–10; keep lab single-project.
- **Doc overclaim risk:** explicitly state it’s a demo log pack, not enterprise coverage.
- **Prompt injection via logs (defense-in-depth):** keep log delimiting + instruction hierarchy; treat logs as data.

---

## 8) Definition of Done (branch-level)

**Functional Requirements:**
- ✅ `--source gcp` (or auto-detect) runs end-to-end on mini-lab log pack
- ✅ Report clearly reflects plane separation (control / telemetry / data / unknown)
- ✅ SQLite persists run metadata + structured findings + report
- ✅ Data minimization enforced (SHA-256 hash only, no raw logs in DB)

**Testing Requirements:**
- ✅ ≥114 total tests passing (38 new GCP + 76 existing)
- ✅ Zero regressions to Windows/AWS functionality
- ✅ Test execution: one-command (`python -m pytest tests/`)
- ✅ Mocked LLM integration test validates full pipeline
- ✅ insertId appears in evidence citations

**Documentation Requirements:**
- ✅ `docs/GCP_MINILAB_PLAN.md` explains lab setup and event types
- ✅ Dataset documentation includes strengths/weaknesses disclosure
- ✅ README.md updated with GCP usage examples
- ✅ Architecture docs updated with GCP adapter diagram

**Code Quality Requirements:**
- ✅ All new modules follow existing project structure
- ✅ Type hints present on all public functions
- ✅ Docstrings present on all modules and public functions
- ✅ No hardcoded secrets or credentials in code
- ✅ Configuration centralized in `config_gcp.py`

**Approval Gates:**
- ✅ Each phase approved by Overseer before proceeding
- ✅ All acceptance criteria verified
- ✅ Pull request from `enhancement/gcp-mini-lab` → `master`
- ✅ Squash merge for clean history

---

## 9) Pre-Implementation Checklist

**Before Phase 0 starts, verify:**
- [ ] All 8 technical specification sections reviewed (section 4.5)
- [ ] Acceptance criteria understood for all phases
- [ ] Test count targets acknowledged (34 new tests minimum)
- [ ] Regression prevention strategy confirmed (76 existing tests must pass)
- [ ] Data minimization strategy understood (hash storage only)
- [ ] Source detection strategy reviewed (no Windows/AWS breakage)
- [ ] Plane tagging heuristics table internalized
- [ ] LLM prompt strategy approved

**Overseer sign-off required before proceeding to Phase 0.**
