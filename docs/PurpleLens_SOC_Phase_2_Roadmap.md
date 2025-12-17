
# 🌌 PurpleLens SOC — Phase 2 Roadmap (Conceptual)

## Purpose of Phase 2
Phase 2 evolves **PurpleLens SOC** from a single-run analytical assistant into a more SOC-aligned analysis platform while preserving core guarantees:
- No autonomous action
- No hallucinated outcomes
- Evidence-first reasoning
- Human-in-the-loop judgment

This roadmap is **conceptual only**. No Phase 2 code is required for interviews.

---

## Phase 2A — Multi-Source Log Support
**Goal:** Expand analysis beyond Windows EVTX without altering the core engine.

**Concepts:**
- Support EDR JSON exports, firewall logs, and cloud audit logs
- Normalize all sources into a shared internal event schema

**Key Rule:**
> New data sources must not change the LLM contract or report logic.

---

## Phase 2B — Analyst Determination Layer (Human-in-the-Loop)
**Goal:** Introduce analyst judgment without automation.

**Additions:**
- Analyst determination: Benign / Suspicious / Malicious
- Analyst notes and timestamps

**Critical Rule:**
> The LLM never assigns determinations.

---

## Phase 2C — Confidence & Evidence Scoring
**Goal:** Make uncertainty explicit and measurable.

**Enhancements:**
- Aggregate confidence scoring
- Evidence strength indicators
- Conflict detection between evidence items

---

## Phase 2D — Timeline Reconstruction
**Goal:** Improve situational awareness.

**Enhancements:**
- Chronological event sequencing
- Textual attack-chain reconstruction
- MITRE ATT&CK technique alignment

---

## Phase 2E — GUI Wrapper (Optional)
**Goal:** Improve junior analyst usability.

**Concept:**
- Thin GUI layer (e.g., Streamlit)
- File upload + report viewing

**Architectural Rule:**
> GUI is presentation-only and calls the same core logic as the CLI.

---

## Phase 2F — SOC Workflow Integration (Read-Only)
**Goal:** Fit safely into SOC workflows.

**Enhancements:**
- Ticket export (JSON / CSV)
- Report archival
- SIEM ingestion of PurpleLens outputs

**No write-back. No response automation.**

---

## Explicit Non-Goals
Phase 2 will NOT include:
- Auto-remediation
- Blocking or quarantine actions
- Continuous monitoring
- Agentic autonomy

---

## Interview Framing
> “Phase 1 proves safe, deterministic AI-assisted analysis. Phase 2 focuses on realism—multi-source data, analyst judgment, confidence handling, and usability—without violating SOC trust boundaries.”
