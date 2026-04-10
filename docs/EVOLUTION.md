# PurpleLens: From POC to Production
## The Invention Story — Interview Reference Document

> **Author's note:** This document reconstructs the production evolution of PurpleLens from the open-source POC (`purplelens-soc`) through three deployment stages to a live enterprise platform. It is written for interview preparation and accurate technical storytelling. The production codebase is proprietary IP of 11:11 Systems/Ntirety and is not represented here. This document is grounded in the POC source code, the inventor's direct recall of architectural decisions, and engineering inference from the POC's own structure.

---

## The Invention Context

PurpleLens originated inside a multi-tenant MSSP SOC managing security operations for 60+ enterprise clients simultaneously. The environment was a high-volume, multi-cloud operation — AWS CloudTrail, GCP Audit Logs, and Windows EVTX telemetry all flowing into a centralized SIEM and SOAR platform running on Azure.

The problem was not a lack of detection coverage. The problem was **analyst cognitive load at MSSP scale**.

A Tier 1 analyst beginning work on a SOAR ticket had to:
1. Open the alert and read raw event data
2. Pivot to the SIEM to pull surrounding and historical context
3. Formulate a hypothesis about what the activity meant
4. Decide whether to escalate or close
5. Document their reasoning

At 60+ clients, this process was repeated hundreds of times per shift. Alert fatigue and inconsistency were structural problems, not individual ones. The question was: **can an AI do the T1 groundwork so the analyst can focus on judgment, not retrieval?**

The answer was PurpleLens.

---

## The POC: What The Code Actually Does

The open-source POC (`src/`) is a **CLI batch pipeline** with a clean, straight-line architecture:

```
ingest → normalize → sanitize → enrich → llm_analyze → validate_output → report → persist
```

### What was already solved in the POC

**Prompt injection firewall** (`security.py`)
Every event field is walked recursively by `prompt_firewall_event()` before touching the LLM. Six injection rules with two action types — `redact` (sanitize and continue) or `quarantine` (drop the event entirely). This was a conscious design decision: telemetry is treated as adversarial input, not trusted data.

**Dual-layer output validation** (`security.py`, `main.py`)
- `validate_output()`: regex guardrails on raw LLM response text. Blocks false authority claims (`"I have blocked..."`, `"This is definitely malicious"`). Enforces the principle that the LLM guides — it does not act.
- `validate_semantic_output()`: checks that every `Evidence` object's `source_file:record_index` exists in the loaded event set. The LLM cannot hallucinate a citation that doesn't trace back to a real event.
- Optional `run_semantic_judge()`: a second LLM pass validates the first.

**Schema-enforced output contract** (`schemas.py`)
The `AnalysisOutput` Pydantic model is the LLM's binding contract. `Finding.evidence` requires `min_length=1` — no finding without proof. `Hypothesis.confidence` is bounded `0.0–1.0`. `status` is a strict literal. Fail-closed on schema mismatch.

**Multi-source auto-detection** (`main.py`)
CloudTrail schema markers, GCP `protoPayload`/`insertId`, EVTX file extension. Mixed-directory detection exits cleanly rather than guessing.

**AWS event correlation** (`aws_correlate.py`)
Proximity-based clustering with strategies (`actor_src_ip`, `actor_resource`, `actor_only`), time-window gating, deterministic SHA1-based cluster IDs. Events related by actor + timeframe + resource are grouped before the LLM sees them — reducing token cost and improving coherence.

**Full observability infrastructure** (`src/ops/`)
`OpsContext` wraps every pipeline stage with structured JSON logging, per-stage timing, LLM token/cost tracking (`llm_tokens_in`, `llm_tokens_out`, `llm_cost_usd`), and prompt injection counters. This was not built for the POC — it was built anticipating production monitoring requirements.

### What the POC did NOT have (yet)
- No API layer. CLI-triggered only.
- No tenant concept. Single run, single log directory.
- No async execution. Synchronous, blocking pipeline.
- No SIEM/SOAR integration. File-based input only.
- No measurement infrastructure for analyst alignment.

These were the gaps that the three production deployment stages addressed.

---

## Three-Stage Production Evolution

### Stage 1: Batch QA Over Auto-Closed SOAR Events
**Problem:** The SOAR platform automated closure of thousands of events per shift using playbooks and known-benign pattern matching. But automation has blind spots. A misconfigured playbook, a novel TTP that looks like a benign pattern, or a threshold edge case could auto-close something that should have been investigated.

**Solution:** PurpleLens was deployed as a **scheduled batch job** (Azure Scheduler / cron) that ran against all SOAR auto-closed events from the prior period.

**How it worked:**
1. Scheduled trigger fires (e.g., every 4 hours)
2. Job queries SOAR API for all auto-closed events in the window
3. Event IDs passed to SIEM API — raw telemetry fetched per event
4. PurpleLens pipeline runs across the batch
5. Any event where LLM output returned high-concern findings despite auto-close status → alert fired to T3
6. Results persisted to PostgreSQL per-run

**What this stage proved:**
- The pipeline was stable enough to run unattended
- The prompt injection firewall and output validation held under production log diversity
- The LLM's schema-enforced output could be reliably parsed downstream
- T3 could use the shift-level aggregate to calibrate SOAR playbooks

**Architecture additions over POC:**
- Azure Scheduler as trigger (replacing CLI invocation)
- SOAR API integration for event ID export
- SIEM API integration for raw telemetry fetch (replacing file-based input)
- PostgreSQL replacing SQLite (run metadata, findings, per-event status)
- Basic alerting on high-confidence findings in auto-closed events

---

### Stage 2: End-of-Shift QA Over Analyst Determinations
**Problem:** Analyst determinations at T1 level are inconsistent. A rushed analyst nearing end of shift marks a borderline event benign without full investigation. At MSSP scale — multiple analysts, multiple clients, back-to-back shifts — the error rate compounds.

**Solution:** A second scheduled batch job ran at **end of each analyst shift**, processing all events marked benign by analysts during that shift.

**How it worked:**
1. Shift-end trigger fires (configurable per shift schedule)
2. Job queries SOAR for all analyst-closed (marked benign) events from that shift, by analyst ID
3. Telemetry fetched from SIEM per event
4. PurpleLens pipeline runs
5. Findings surfaced in a **shift report** delivered to: the shift manager, T3 lead, and detection engineering team
6. Events where LLM confidence score indicated high concern despite benign closure → flagged for T3 review

**What the shift report contained:**
- Summary of analyst activity (volume, closure rates by analyst)
- Events PurpleLens flagged as high-concern despite benign determination
- Hypothesis and IoC summary per flagged event
- Recommended next steps per flagged finding
- Confidence scores for every determination

**What this stage added:**
- **Analyst QA layer** — passive, non-confrontational. No analyst was alerted in real-time. The report went to management and engineering.
- **Rule refinement fuel** — detection engineering used the shift reports to identify SOAR playbook gaps and tune detection rules.
- **Manager visibility** — for the first time, shift managers had a structured daily intelligence brief on what happened, not just ticket counts.
- **Analyst accountability signal** — over time, patterns emerged in which analysts consistently agreed with PurpleLens guidance vs. which had high disagreement rates.

**Architecture additions over Stage 1:**
- Per-analyst event scoping in SOAR query
- Shift report generation (structured markdown/text, persisted to PostgreSQL and delivered via email or SOAR notification)
- Analyst ID tracking in PostgreSQL schema
- Detection engineering read access to PostgreSQL shift report table

---

### Stage 3: Real-Time Per-Event Analysis on Analyst Claim
**Problem:** Stages 1 and 2 were retrospective. By the time the batch ran, the analyst had already made a determination — possibly wrong. The real value of PurpleLens was giving analysts the AI's analysis **before** they made the call, not after.

**Solution:** PurpleLens was integrated directly into the SOAR analyst workflow as a **real-time, per-event, on-demand analysis** triggered at the moment an analyst claimed a ticket.

**The Analyst Experience:**
1. Analyst opens a SOAR ticket and clicks "Claim"
2. The claim action fires a SOAR webhook
3. Webhook payload (event ID, tenant ID, analyst ID) hits the PurpleLens FastAPI endpoint
4. Pipeline runs: SIEM API fetches the triggering event + surrounding context (same time window, same source entity) + historical events for that entity
5. PurpleLens analysis completes
6. Report written to PostgreSQL (tenant-scoped)
7. SOAR pulls the report and renders it in the **PurpleLens box** — a text panel inside the ticket UI
8. Analyst reads the PurpleLens report before beginning their investigation

**What the PurpleLens box showed:**
```
┌─ PurpleLens Analysis ─────────────────────────────────────────┐
│ Confidence: 0.82 — Likely Benign                              │
│                                                               │
│ HYPOTHESIS                                                    │
│ Scheduled task execution matching known backup agent pattern. │
│ Source IP aligns with internal automation infrastructure.     │
│                                                               │
│ INDICATORS OF COMPROMISE                                      │
│ • None identified in this event                               │
│ • No lateral movement signals in 72h window for this entity  │
│                                                               │
│ NEXT STEPS (How to Investigate)                               │
│ 1. Confirm source IP against known automation inventory       │
│ 2. Check parent process chain for anomalies                   │
│ 3. Validate against baseline for this host                    │
│                                                               │
│ TRACKING                                                      │
│ Related events: 3 in 72h window, all benign pattern          │
│ Last PurpleLens analysis for this entity: 7 days ago, benign │
└───────────────────────────────────────────────────────────────┘
```

**The LLM's role was explicit and bounded:**
- It hypothesized. It did not conclude.
- It recommended next steps. It did not take action.
- It presented a confidence score. The analyst made the determination.
- It surfaced IoCs. The analyst confirmed or refuted them.

This was the security architecture principle from the POC made operational: `PROHIBITED_PATTERNS` in `security.py` enforced that the LLM never claimed to have taken action or made a definitive determination. In production, this was both a technical guardrail and an institutional policy.

**Tenant isolation implementation:**
- Each enterprise client (tenant) had a scoped PostgreSQL schema or row-level security by `tenant_id`
- SIEM API credentials per tenant stored in Azure Key Vault, fetched at request time via managed identity
- PurpleLens pipeline context was tenant-scoped: event fetch, enrichment, and report storage all namespaced by `tenant_id`
- SOAR webhook payload included `tenant_id` — validated against an allowlist before processing
- Rolled out to one client first. Validated alignment metrics over 30 days. Expanded incrementally.

---

## The Alignment Metric

The production governance signal was **analyst concordance rate** — not analyst override rate.

The LLM never made a determination. It expressed a hypothesis with a confidence score:
- `"Likely Benign (0.82)"`
- `"Possible Lateral Movement — Investigate (0.71)"`
- `"High Concern — Escalate Recommended (0.88)"`

The metric tracked: **did the analyst's final determination align with the LLM's guidance?**

Example: LLM says `"Likely Benign (0.82)"` → analyst marks event benign → **concordance**.
Example: LLM says `"High Concern (0.88)"` → analyst marks event benign → **discordance** → flagged for T3 review.

This metric served three functions:
1. **Model quality signal:** Sustained discordance on a specific event type indicated the model's understanding of that pattern had degraded. Triggered retraining/prompt revision.
2. **Analyst performance signal:** An analyst with consistently high discordance rates against high-confidence LLM guidance was flagged for coaching (handled through management, not automated).
3. **Trust calibration:** As concordance rates were tracked over time, the team developed a confidence threshold above which the LLM's guidance was considered highly reliable. This informed future automation decisions.

---

## Production Architecture (Reconstructed)

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRIGGER LAYER                               │
│  Stage 1: Azure Scheduler (every N hours, batch)                │
│  Stage 2: Azure Scheduler (shift-end trigger, batch)            │
│  Stage 3: SOAR Webhook (analyst ticket claim, real-time)        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    API LAYER (FastAPI)                          │
│  POST /api/v1/analyze/batch      (Stages 1 & 2)                 │
│  POST /api/v1/analyze/event      (Stage 3 — per-event)          │
│  Tenant ID validation → Azure Key Vault credential fetch        │
│  Request logging → PostgreSQL audit table                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  ENRICHMENT LAYER (SIEM API)                    │
│  Fetch triggering event raw telemetry                           │
│  Fetch surrounding events (configurable time window)            │
│  Fetch entity history (same actor/IP/host, 72h default)         │
│  Normalize to PurpleLens event schema                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                 PURPLELENS PIPELINE (from POC)                  │
│  prompt_firewall_event() → sanitize all telemetry fields        │
│  correlate_events() → cluster related events by actor/time      │
│  analyze_events() → LLM analysis with schema-enforced output    │
│  validate_output() → policy guardrails on LLM response          │
│  validate_semantic_output() → evidence traceability check       │
│  generate_report() → structured analyst-facing output           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   DATA LAYER (Azure)                            │
│  PostgreSQL (Azure Database) — tenant-scoped by tenant_id       │
│  Row-level security per tenant on findings, reports, runs       │
│  Azure Key Vault — per-tenant SIEM/SOAR API credentials         │
│  Azure Blob Storage — raw event artifacts per tenant            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  DELIVERY LAYER                                 │
│  Stage 1 & 2: SOAR notification + PostgreSQL report table       │
│  Stage 2: Shift report (structured text → email/SOAR channel)   │
│  Stage 3: SOAR webhook callback → PurpleLens box in ticket UI   │
│  Analyst UI: text panel in SOAR ticket (no separate dashboard)  │
└─────────────────────────────────────────────────────────────────┘
```

**Infrastructure:**
- Cloud: Microsoft Azure
- Compute: Azure App Service (FastAPI) or Azure Container Apps
- Database: Azure Database for PostgreSQL (Flexible Server)
- Secrets: Azure Key Vault with managed identity
- Storage: Azure Blob Storage (tenant-scoped containers)
- Scheduling: Azure Scheduler / Logic Apps (Stages 1 & 2)
- LLM: Azure OpenAI Service (GPT-4) — Azure-hosted for data residency compliance

---

## The Security Architecture Principle That Held Through All Three Stages

From the POC docstring in `security.py`:
> *"LLM output is untrusted input. We enforce behavior, not hope for compliance."*

This principle never changed from POC to production. It became an institutional policy:
- The LLM hypothesizes. The analyst determines.
- The LLM surfaces evidence. The analyst confirms.
- The LLM recommends next steps. The analyst investigates.
- The LLM never takes action. The analyst owns the outcome.

This was not just a safety design — it was the adoption strategy. Analysts trusted PurpleLens because it never competed with their judgment. It gave them a running start.

---

## Interview Narrative Summary

**The Problem:**
At an MSSP managing 60+ enterprise clients, T1 analysts were spending 3-4 hours per shift on manual event investigation groundwork — pulling context from SIEMs, formulating hypotheses, deciding where to start. Alert fatigue and inconsistent determinations were structural problems.

**The Invention:**
I designed and built PurpleLens — an AI-driven SOC analysis pipeline that treated the LLM as an untrusted component: input sanitized before it touches the model, output validated before an analyst sees it, and human determination always final. The POC is open-source at github.com/mwill20/purplelens-soc.

**The Evolution:**
We deployed in three stages. Stage 1 validated the pipeline against SOAR auto-closed events — proving the system was stable and the guardrails held under production log diversity. Stage 2 added end-of-shift QA over analyst determinations — giving management and detection engineering a structured shift intelligence brief for the first time. Stage 3 was the full integration: real-time per-event analysis delivered inside the SOAR ticket the moment an analyst claimed it, giving every analyst a T1-level running start before they began investigation.

**The Outcome:**
At MSSP scale — 60+ enterprise clients on Azure, multi-cloud telemetry, PostgreSQL with tenant-scoped isolation — PurpleLens reduced analyst investigation start time and provided the detection engineering team with a continuous signal for rule refinement. The governance metric was analyst concordance rate: how often analysts agreed with the LLM's hypothesis and confidence score. That metric drove both model calibration and analyst coaching decisions.

**The Principle That Never Changed:**
From the first line of code to the last production deployment: LLM output is untrusted input. We enforce behavior, not hope for compliance.
