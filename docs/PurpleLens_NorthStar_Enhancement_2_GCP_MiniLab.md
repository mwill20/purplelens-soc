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
- Plan is clear, minimal, and does not claim production hardening
- Event checklist matches the “high signal” set above

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
    return {
        "provider": "gcp",
        "source_file": source_file,
        "record_index": idx,
        "event_time": rec.get("timestamp"),
        "plane": "control" if pp.get("serviceName", "").endswith("iam.googleapis.com") else "telemetry",
        "actor": auth.get("principalEmail"),
        "action": f'{pp.get("serviceName")}:{pp.get("methodName")}',
        "resource": pp.get("resourceName") or rec.get("resource", {}),
        "src_ip": md.get("callerIp"),
        "user_agent": md.get("callerSuppliedUserAgent"),
        "severity": rec.get("severity"),
        "raw": rec,
    }
```

**Overseer acceptance checks**
- Ingests N records deterministically with provenance
- No downstream pipeline changes required

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
- Report sections are deterministic (not LLM narrative)
- Findings remain evidence-backed

---

### Phase 3 — “IaC/automation identity” enrichment (small, high value)
**Goal:** Make automation identity reasoning visible without deep GCP specifics.

**Engineer tasks**
- Add deterministic tags (best-effort) from userAgent strings:
  - `terraform`, `gcloud`, `cloudbuild`, `github-actions`, etc.
- Add a derived field `actor_kind = human|service_account` by email pattern
- Add a derived “pivot indicator” when actor project != resource project (best-effort)

**Overseer acceptance checks**
- Enrichment is deterministic and unit-tested
- No claims of “human vs automation” based on tool alone

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
- Log pack is small and stable (no drift)
- Documentation avoids overclaiming coverage

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
- One-command test run passes locally

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
- `--source gcp` (or auto-detect) runs end-to-end on the mini-lab log pack
- Report clearly reflects plane separation (control / telemetry; data optional)
- SQLite persists run metadata + structured findings + report
- Tests cover normalization + one mocked end-to-end run
- Documentation explains how logs were generated + dataset strengths/weaknesses
