# PurpleLens SOC — Enhancement 1 NorthStar (AWS CloudTrail Branch)

**Branch name:** `enhancement/aws-cloudtrail`  
**Owner roles:** Architect (you) → Overseer (review) → Primary Engineer (execute 1 phase at a time)  
**Timebox:** Designed for a **≤ 1-week** effort with **~40 hours max** total engineering time.

---

## 1) Why this enhancement exists (interview-aligned)

This branch exists to demonstrate that PurpleLens is a **log-agnostic SOC analysis harness**:

- It can **ingest and normalize** a different artifact type (AWS CloudTrail).
- It can use an LLM **only for structured extraction** (no “actions”, no false authority).
- It produces a **deterministic, evidence-cited SOC report**, and persists to SQLite for auditability.

This directly supports the assignment’s intent:
- ingest + analyze + (light) correlate security artifacts with GenAI context,
- produce a clear final report,
- demonstrate code quality + security acumen + prompting strategy.

---

## 2) Non‑negotiable architecture invariants (do not change)

These remain identical to the Windows EVTX branch:

1. **LLM is extraction-only**  
   - Output must be JSON-only, schema-validated (Pydantic).
2. **Evidence is mandatory**  
   - Each key claim references `source_file` + `record_index` (or equivalent provenance).
3. **Python writes the report**  
   - Deterministic formatting; LLM does not write narrative.
4. **Policy guardrails run after schema validation**  
   - Block “I blocked…”, “I remediated…”, or any claims of completed actions.
5. **SQLite persistence**  
   - Store run metadata + structured findings + final report text.

---

## 3) Scope (tight and interview-safe)

### In scope
- CloudTrail dataset ingestion (Kaggle Flaws CloudTrail set)
- Normalization into PurpleLens “event envelope”
- Minimal correlation primitives (same actor / same resource / same time-window)
- Same single-run CLI experience: `python -m src.main --input ...`
- Small demo dataset (e.g., 50–200 events) to keep LLM prompt stable

### Out of scope (explicitly)
- Real-time streaming / tailing
- Full AWS service coverage / full CloudTrail schema modeling
- Auto-remediation, determinations, or “we blocked X”
- Complex graph correlation across accounts/orgs
- Multi-tenant/enterprise RBAC or DB migrations (SQLite stays)

---

## 4) Core design: “Adapter, not rewrite”

**Only the ingestion adapter changes.**  
Everything downstream uses the same pipeline and contracts.

### Normalized event envelope (conceptual)
Each CloudTrail record becomes:

- `source_file`: path to file
- `record_index`: line/index in file
- `event_time`: parsed timestamp
- `provider`: `"aws"`
- `plane`: `"control"` (default) / `"telemetry"` / `"data"` (heuristic mapping)
- `actor`: `userIdentity.arn` or `principalId`
- `actor_type`: `AssumedRole` / `IAMUser` / `AWSService` / etc
- `action`: `eventSource` + `eventName`
- `resource`: best-effort resource identifier(s) from `resources[]` / requestParameters
- `src_ip`: `sourceIPAddress`
- `user_agent`: `userAgent`
- `outcome`: `errorCode`/`errorMessage` or “success” if absent
- `raw`: original record (stored or hashed)

> The goal is *SOC reasoning portability*, not perfect AWS modeling.

---

## 5) Phased execution plan (engineer executes ONE phase at a time)

### Phase 0 — Branch scaffold + guardrail continuity (low risk)
**Goal:** Create the branch skeleton without changing the core pipeline.

**Engineer tasks**
- Create branch `enhancement/aws-cloudtrail`
- Add `src/ingest_aws.py` (new adapter)
- Add a minimal fixture directory (e.g., `data/aws_cloudtrail_sample/`)
- Update CLI to accept `--source aws|windows` (or detect input shape)
- Ensure existing Windows flow still works

**Overseer acceptance checks**
- Windows EVTX workflow passes unchanged
- All tests still pass
- No new “LLM writes narrative” path introduced

---

### Phase 1 — CloudTrail parsing + normalization (core work)
**Goal:** Convert CloudTrail JSON/JSONL records into the normalized event envelope.

**Engineer tasks**
- Parse dataset format (Kaggle may be JSON files, JSON arrays, or JSONL)
- Implement robust parsing:
  - skip malformed lines with clear errors
  - record provenance (`source_file`, `record_index`)
- Create `normalize_cloudtrail_record(record) -> NormalizedEvent`
- Persist normalized events (same DB table/schema used by Windows, if already exists)

**Example snippet (illustrative, not full file)**
```python
def normalize_cloudtrail_record(rec: dict, source_file: str, idx: int) -> dict:
    ui = rec.get("userIdentity") or {}
    return {
        "provider": "aws",
        "source_file": source_file,
        "record_index": idx,
        "event_time": rec.get("eventTime"),
        "actor": ui.get("arn") or ui.get("principalId"),
        "actor_type": ui.get("type"),
        "action": f'{rec.get("eventSource")}:{rec.get("eventName")}',
        "src_ip": rec.get("sourceIPAddress"),
        "user_agent": rec.get("userAgent"),
        "outcome": "failure" if rec.get("errorCode") else "success",
        "raw": rec,
    }
```

**Overseer acceptance checks**
- Ingests N records deterministically (same count every run)
- Every normalized event has provenance fields populated
- Malformed record handling is explicit and logged

---

### Phase 2 — Plane tagging + minimal correlation hooks (small but valuable)
**Goal:** Demonstrate cloud security intuition: planes + “connect the dots” basics.

**Engineer tasks**
- Add simple heuristics:
  - IAM / STS / Organizations / CloudTrail → `control`
  - S3 object-level / DynamoDB item-level (if present) → `data`
  - GuardDuty findings / CloudWatch logs events → `telemetry`
- Add minimal correlation in preprocessing (before LLM prompt):
  - cluster by actor within time window
  - cluster by resource identifiers
  - add derived fields: `cluster_id`, `cluster_size`

**Overseer acceptance checks**
- Heuristics are deterministic and unit-tested
- Correlation does not change or “invent” facts; it only groups events

---

### Phase 3 — Prompt framing tuned for CloudTrail + schema validation (LLM contract unchanged)
**Goal:** Ensure the LLM sees the right context without letting it “take control.”

**Engineer tasks**
- Update the extraction prompt template to include:
  - explicit instruction hierarchy
  - event provenance labels
  - “JSON only” response requirement
- Provide event batches with stable formatting:
  - `Event[12] source=... idx=... actor=... action=... resource=...`
- Validate output via Pydantic; fail closed if invalid

**Overseer acceptance checks**
- Schema validation blocks malformed output
- Policy guardrails block false action claims
- Report generation still deterministic

---

### Phase 4 — Demo dataset + reproducibility notes (assignment-aligned)
**Goal:** Nail the “how and why dataset was chosen” requirement.

**Engineer tasks**
- Curate a small, stable subset of the Kaggle dataset:
  - documented selection criteria (e.g., “IAM + STS + logging-related actions”)
  - keep it small to avoid prompt overflow
- Add README section:
  - dataset source
  - strengths/weaknesses (coverage gaps, synthetic bias if any)
  - what “correlation” means in this tool (grouping, not proof)

**Overseer acceptance checks**
- Demo run completes reliably
- README is accurate and does not overclaim capabilities

---

### Phase 5 — Minimal test coverage (interview confidence)
**Goal:** Prevent regressions and prove adapter correctness.

**Engineer tasks**
- Unit tests:
  - parsing a record
  - normalization fields present
  - plane tagging heuristics
- End-to-end test with mocked LLM:
  - verifies DB writes and report output

**Overseer acceptance checks**
- Tests pass locally with a single command
- Windows tests still pass

---

## 6) Interview narrative anchors (what you say out loud)

- “PurpleLens is a harness: **ingestion → constrained extraction → deterministic report**.”
- “AWS support is an adapter: I normalized CloudTrail into the same evidence-first event envelope.”
- “The LLM never ‘acts’; it extracts structured findings; Python writes the report and stores the audit trail.”

---

## 7) Risks & mitigations (architect-level)

- **Dataset format variability:** handle JSON arrays vs JSONL; log + skip malformed records.
- **Prompt size blowups:** small curated subset; batch events; cap max events per run.
- **Over-claim risk in docs:** explicitly state “grouping ≠ proof; no automated remediation.”

---

## 8) Definition of Done (branch-level)
- `--source aws` (or auto-detect) runs end-to-end
- Schema validation + policy guardrails still enforce constraints
- SQLite contains run metadata + findings + report
- Tests cover normalization + one full mocked flow
- README documents dataset source and limitations without overclaiming
