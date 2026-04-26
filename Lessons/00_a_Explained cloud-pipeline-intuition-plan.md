# 3-Week Cloud & Data Pipeline Intuition Plan (GCP-Focused)

## Purpose
This document outlines a focused, time-bounded approach to building **cloud security and data pipeline intuition** sufficient for a senior-level technical interview, while compounding long-term AI Security Engineering skills.

The goal is **not mastery**.  
The goal is **credible reasoning about production systems**.

---

## Core Reframe
You are **not learning “cloud”**.

You are learning one specific slice:

> How security-relevant telemetry is generated, moved, transformed, and consumed.

Everything else is out of scope for now.

---

## The Three Non-Negotiable Mental Models

### 1. Cloud = Control Plane + Data Plane + Telemetry
- **Control Plane**: API calls, identity actions, configuration changes  
- **Data Plane**: Workloads, runtime behavior, traffic  
- **Telemetry**: Logs, metrics, traces emitted by both

Security investigations primarily rely on **control-plane logs and audit trails**, not raw packets.

---

### 2. Logs Move Through Pipelines (Not Magic)
All log systems follow the same lifecycle:

**Source → Ingest → Parse → | TB Normalization | Enrich → Store → Query → Alert / Analyze**

Vendors differ. Architecture does not.

If you can reason through this flow, you can reason about most security platforms.



**_GCP Example:_**
**Source:** GCP Audit Logs (Admin Activity, Data Access)
**Ingest:** Google Cloud Logging or Pub/Sub
**Parse:** Extracts key fields from raw log data, turning logs into structured records (user, action, resource from a JSON or text log). Log router, Cloud Function, or collector.
**TB Normalization:** Takes those structured fields and maps them to a consistent, predefined schema across all log sources. Log sink transformation.
**Enrich:** Dataflow or Cloud Function adds user/threat/security context
**Store:** BigQuery, Cloud Storage, or Logging buckets
**Query:** BigQuery SQL or Logging query interface
**Alert / Analyze / Automate / AI:** SOAR, Security Command Center, Logging alerts, or Vertex AI (AI/ML)

---

### 3. AI Belongs After Structure, Not Before
- Raw logs are noisy and ambiguous  
- Parsing and normalization must come first  
- AI operates on **structured, scoped artifacts**  
- Evidence, traceability, and constraints are mandatory in security systems

This aligns directly with the ThreatPrism design philosophy.

---

## GCP Scope (Intentionally Narrow)

### 1. GCP Audit Logs (Primary Focus)
Understand:
- Admin Activity logs
- Data Access logs
- Actor, action, resource, timestamp, outcome

Key intuition:
> Most cloud security incidents reduce to “who did what, where, and when.”

---

### 2. IAM (Conceptual Only)
Focus on:
- Principals (users, service accounts)
- Roles vs permissions
- How identity appears in logs
- Why misconfiguration is a major risk vector

---

### 3. Log Routing / Sinks
Understand:
- Logs can be routed to multiple destinations
- Centralization is intentional
- Ingestion and analysis are decoupled by design

This mirrors SIEM architecture patterns.

---

### 4. Observability Tool: OpenObserve
Purpose:
- Visualize a complete pipeline end-to-end
- See ingest, parse, store, query, and visualize in one system

Goal is **intuition**, not tool mastery.

---

## 3-Week Execution Plan

### Week 1 — Mental Models & Vocabulary
**Goal**: Become fluent enough to discuss cloud logs without confusion.

Actions:
- Read GCP Audit Logs overview
- Review example audit log entries
- Identify actor, action, resource, timestamp, outcome

Outcome:
- Can verbally explain what a suspicious cloud event looks like

---

### Week 2 — Pipeline Intuition (Light Hands-On)
**Goal**: Understand why pipelines matter.

Actions:
- Run OpenObserve locally
- Ingest sample structured logs
- Query and observe effects of parsing and enrichment

Outcome:
- Can explain why raw logs are unusable without preprocessing

---

### Week 3 — Mapping to ThreatPrism (Interview Leverage)
**Goal**: Connect cloud concepts to your existing system.

Actions:
- Conceptually map:
  - GCP Audit Logs → ingestion layer
  - Parsing → deterministic preprocessing
  - Evidence extraction → AI step
  - Report → analyst-facing output

Outcome:
- Can explain how ThreatPrism would extend to cloud logs without changing its philosophy

---

## Interview Readiness Litmus Test

You are ready if you can confidently answer:

- Where do cloud security logs originate?
- What breaks when parsing is incorrect?
- Why should AI not operate on raw logs?
- How do you add a new log source safely?
- What telemetry matters most during an incident at 3 a.m.?

---

## Important Guardrail
Do **not** attempt to fully implement cloud ingestion right now.

Premature implementation:
- Increases risk
- Dilutes focus
- Adds stress
- Produces half-built systems

Senior engineers explain systems clearly **before** building them.

---

## End State
After completing this plan, you should be able to:
- Reason confidently about cloud security telemetry
- Explain data pipelines in plain language
- Defend architectural decisions in interviews
- Extend your system conceptually without over-engineering

This is the bridge between interview success and real-world AI Security Engineering.
