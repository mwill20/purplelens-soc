
# 🌟 North Star — Bespin AI Security Analyst Assistant

## 1. Project Vision (Why This Exists)

The Bespin AI Security Analyst Assistant exists to bridge the gap between raw security telemetry and human understanding.

Modern SOCs are overwhelmed by high-volume logs, low-context alerts, and fragmented data sources. This project demonstrates how a constrained, security-aware LLM can be safely integrated into a SOC workflow to synthesize context, surface weak signals, and present analyst-ready intelligence **without** overstepping into decision-making or response.

This tool is not meant to replace analysts. It is meant to accelerate first-pass analysis while preserving trust, evidence, and human authority.

---

## 2. One-Sentence North Star (Non-Negotiable)

> A secure Python-based SOC analysis tool that ingests Windows security artifacts, uses a constrained LLM to extract schema-validated structured intelligence with evidence, and deterministically generates a human-readable SOC report — without taking actions or making determinations.

---

## 3. Core Principles (Design Laws)

### 3.1 Analysis, Not Action
The system never claims remediation, blocking, or response. All outputs are framed as observations, hypotheses, and recommendations.

### 3.2 Structured Before Narrative
The LLM outputs only structured intelligence. Python code owns all narrative formatting.

### 3.3 Evidence Is Mandatory
Every meaningful claim must reference an event ID, log line, or source artifact.

### 3.4 Determinism Beats Cleverness
Predictable, explainable code is preferred. No autonomous agent loops. No hidden state.

### 3.5 Treat Inputs as Hostile
Logs are untrusted. Prompt injection is assumed. Output validation is enforced.

---

## 4. System Boundary (What’s In / What’s Out)

### In Scope
- Local file ingestion (EVTX → parsed formats)
- Structured LLM extraction
- Policy enforcement
- Report generation
- SQLite persistence
- CLI execution

### Out of Scope
- Real-time monitoring
- Streaming ingestion
- Alerting pipelines
- SOAR integrations
- Active response
- Model fine-tuning

---

## 5. Dataset North Star (Locked)

### Primary Dataset
**EVTX-ATTACK-SAMPLES (Windows Event Logs mapped to MITRE ATT&CK)**

This dataset provides real Windows Security Event semantics, explicit Purple Team relevance, and is easy to explain and demo in interview settings.

Only 2–4 EVTX files are used to maintain focus and simplicity.

---

## 6. Conceptual Architecture (Mental Model)

### Layer 1: Ingestion & Normalization
Input: EVTX-derived structured events  
Output: normalized event records  
Responsibility: correctness, provenance, consistency

### Layer 2: Intelligence Extraction (LLM)
Input: delimited, sanitized events  
Output: strict JSON matching a schema  
Responsibility: pattern recognition, hypothesis suggestion

### Layer 3: Report Synthesis (Python)
Input: validated structured intelligence  
Output: SOC-style analyst report  
Responsibility: clarity, safety, determinism

---

## 7. LLM Role (Precisely Defined)

The LLM acts as a constrained analytical reasoning engine that extracts structure from messy security data.

The LLM is not an analyst making decisions, not a report writer, not an autonomous agent, and not a responder.

---

## 8. Output North Star (What “Done” Looks Like)

The final output is a single SOC-style report with clear sections (Findings, Evidence, Hypotheses, Next Steps), neutral tone, explicit uncertainty, and no claims of action.

Success is achieved when a senior SOC analyst can reasonably build upon the analysis.

---

## 9. Security & Trust Posture

Trust is enforced through schema validation, policy guardrails, deterministic report generation, non-action language, and transparent limitations.

Even a misbehaving model cannot cause harm.

---

## 10. Success Criteria (Architect Acceptance)

- All rubric requirements satisfied
- Dataset choice is defensible
- Architecture explainable in under 60 seconds
- Live demo runnable in under 5 minutes
- No “magical” or hand-wavy components

---

## 11. Future-Facing (Without Scope Creep)

The North Star allows extensions such as additional log sources, alternative LLM providers, richer schemas, and SOC2-lite mappings without changing its core.

---

## 12. Architect’s Final Guardrail

> This project succeeds by being clear, safe, and boring in the right ways.

If something feels flashy, clever, or hard to explain, it likely violates the North Star.
