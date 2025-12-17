
# Bespin AI Security Analyst Assistant
## Master Rubric & Verification Checklist (Knowns Filled)

---

## 1. Tool Definition & Intent (Core Requirement)

**Tool name:**  
> Bespin AI Security Analyst Assistant

**What is the tool (one sentence):**  
> This is a secure Python-based SOC analysis tool that ingests security artifacts and outputs a single human-readable SOC analyst report.

**Primary purpose:**  
> The tool exists to extract structured security intelligence from raw artifacts for human SOC analysts and security engineers.

**Who the tool is for:**  
- ☑ SOC analysts  
- ☑ Security engineers  
- ☑ Purple Team operators  
- ☑ MSSP environments  
- ☐ Other: _______________________________

**Explicit non-goals (must all be true):**  
- ☑ Does NOT take automated actions  
- ☑ Does NOT claim enforcement or remediation  
- ☑ Does NOT make final determinations (benign/malicious)  
- ☑ Does NOT operate without human oversight  

---

## 2. Security Dataset Selection (Input Artifacts)

**Dataset type(s) used:**  
- ☑ SIEM logs  
- ☑ Windows Security Event logs  
- ☐ Firewall / proxy logs  
- ☐ Cloud identity logs  
- ☐ Vulnerability scan summaries  
- ☐ Other: _______________________________

**Dataset source:**  
**Primary Dataset:** Windows EVTX Attack Samples

**Dataset name:** EVTX-ATTACK-SAMPLES

**Dataset source:** Public GitHub repository: https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES

**Dataset description:**
This dataset contains Windows Security Event Log (EVTX) samples mapped to MITRE ATT&CK tactics and techniques, designed to simulate adversary behavior and defensive telemetry in enterprise environments.

### **Acquisition Steps**

Clone the repository:
git clone https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git

### Dataset Scoping for This Project (Intentionally Minimal)
To keep the demo focused and Purple-Team aligned, select 2–4 EVTX files only:

☐ One Execution tactic sample
☐ One Credential Access tactic sample
☐ (Optional) One Lateral Movement tactic sample

This controlled selection provides both adversarial activity and defensive visibility without introducing unnecessary ingestion or normalization complexity.

### Why This Dataset Was Chosen (Locked Rationale)
Windows-native telemetry used in real SOC environments
Explicitly mapped to MITRE ATT&CK techniques
Contains both benign and adversary-like event patterns
Enables Purple Team analysis (offense + defense context)
Public, legal, and easy to explain in interviews
Purple Team justification (fill-in optional detail):
These EVTX samples simulate __________________________________________ while allowing defensive analysis of __________________________________________.

### Dataset Trust & Disclosure Notes
- Data is publicly available and non-sensitive
- Events are representative but not exhaustive
- Dataset is used for analysis demonstration, not detection benchmarking

**Why this dataset is realistic:**  
> This dataset reflects real-world security operations because it mirrors common enterprise authentication, process execution, and audit telemetry.

**Purple Team relevance (required):**  
> The dataset contains signals associated with credential abuse, suspicious process execution, and misconfiguration exploitation, and allows defensive analysis of adversary tradecraft.

**Examples of adversarial or weak-signal activity present:**  
> Suspicious PowerShell execution  
> Abnormal authentication patterns

**Dataset limitations (explicit disclosure):**  
> [INFERRED FROM SCOPE] Only 2-4 EVTX files used (not exhaustive); limited to Windows telemetry; representative samples rather than production-scale. [TO VERIFY] Dataset-specific quirks after inspection.

**Architect Lock Statement:**
The EVTX-ATTACK-SAMPLES dataset is the primary and authoritative dataset for this project. All ingestion, analysis, and reporting logic is designed and validated against this dataset.

---

## Phase 0 Progress Tracking

**Phase 0 Status:** ✅ COMPLETE — APPROVED FOR HANDOFF  
**Last Updated:** December 16, 2025

### Phase 0 Deliverables:
- ☑ Phase 0 specification document created
- ☑ System boundaries defined
- ☑ Repo structure locked
- ☑ Data flow defined (with failure paths)
- ☑ Output schema defined (with provenance + error handling)
- ☑ SQLite schema defined
- ☑ CLI specification complete
- ☑ Security policies enumerated
- ☑ EVTX preprocessing approach locked (out-of-scope)

**Validation Reports:**
- Initial: `validation/Phase_0_Validation_Report.md`
- Final: `validation/Phase_0_AI_Ready_Handoff.md` (pending)

**Next Action:** Overseer to generate AI-Ready Handoff Document for principle engineer

---

## 3. Ingestion & Normalization (System Design)

**Input formats supported:**  
- ☑ JSON  
- ☑ JSONL  
- ☑ CSV  

**Ingestion behavior:**  
> The tool ingests artifacts by loading files from disk via a CLI entrypoint.

**Normalization approach:**  
> Raw input is normalized into structured event records to enable consistent analysis and evidence correlation.

**Data trust model:**  
- ☑ All inputs treated as untrusted  
- ☑ Logs are delimited before LLM use  
- ☑ Provenance preserved (file, line, event ID)

---

## 4. Storage & Persistence

**Storage backend:**  
- ☑ SQLite  
- ☐ JSON file  
- ☐ Other: _______________________________

**What is stored:**  
- ☑ Raw artifact metadata  
- ☑ Normalized events / findings  
- ☑ LLM structured outputs  
- ☑ Final analyst report text  

**Why persistence matters:**  
> Persistence enables auditability and reproducibility of analysis.

---

## 5. LLM Usage (Constrained & Safe)

**LLM provider/model:**  
> OpenAI API (model configurable via environment variable)

**LLM role (must be extraction only):**  
> The LLM is used exclusively to extract structured security intelligence from provided artifacts.

**LLM is explicitly prevented from:**  
- ☑ Writing the final report  
- ☑ Claiming actions were taken  
- ☑ Making determinations  
- ☑ Executing or simulating response actions  

**Prompt safety controls:**  
- ☑ Logs clearly delimited  
- ☑ Instruction hierarchy enforced  
- ☑ System prompt restricts output format  

---

## 6. Structured Intelligence Schema (Core Requirement)

**LLM output format:**  
- ☑ JSON only  
- ☑ Schema-validated  
- ☑ Machine-readable  

**Required structured fields:**  
- ☑ findings[]  
- ☑ hypotheses[]  
- ☑ indicators_of_compromise[]  
- ☑ evidence[]  
- ☑ confidence score  
- ☑ recommended_next_steps[]

**Evidence requirement:**  
> Every finding must reference specific artifact identifiers or line numbers.

---

## 7. Analyst Report Generation (Core Requirement 4)

**Who generates the report:**  
- ☑ Python system code  
- ☑ NOT the LLM  

**Report assembly method:**  
> The report is generated by formatting schema-validated structured intelligence into a SOC-style narrative report.

**Report characteristics:**  
- ☑ Human-readable  
- ☑ Deterministic  
- ☑ SOC-appropriate tone  
- ☑ Explicit uncertainty acknowledged  

**Policy enforcement:**  
- ☑ No hallucinated actions  
- ☑ No false claims  
- ☑ No remediation assertions  

---

## 8. Output & Presentation

**Primary output:**  
- ☑ Console-printed SOC report  

**Optional outputs:**  
- ☑ Stored report in SQLite  
- ☐ JSON structured output  
- ☐ Markdown report  

**Why this output format was chosen:**  
> Console output enables fast demonstration and interview-friendly execution.

---

## 9. README & Documentation (Required)

**README includes:**  
- ☑ Tool overview  
- ☑ Setup instructions  
- ☑ How to run the tool  
- ☑ Dataset explanation  
- ☑ Known limitations  
- ☑ Future enhancements  

**Known limitations documented:**  
> Limited to 2-4 EVTX sample files; no real-time ingestion; single LLM call per analysis run; SQLite-only persistence; no automated remediation

**Future enhancements listed:**  
> Multi-source ingestion (Sysmon, firewall logs)  
> Streaming analysis support  
> Alternative LLM providers  
> Enhanced schema mapping to MITRE ATT&CK

---

## 10. Demo & Interview Readiness

**Demo scenario included:**  
- ☑ Benign or low-risk example  
- ☑ Suspicious / anomalous example  

**Live demo steps:**  
> 1. Run tool against benign sample  
> 2. Run tool against suspicious sample  
> 3. Review generated SOC report  

**One live-edit example (interview):**  
> __________________________________________

---

## 11. Security & AI Safety Posture

**Security controls implemented:**  
- ☑ Prompt-injection resistance  
- ☑ Output validation  
- ☑ Policy guardrails  
- ☑ Evidence enforcement  

**Why this design is safe:**  
> The system enforces strict role separation between analysis and action and validates all model outputs before use.

---

## 12. Architectural Explanation (Interview Use)

**60-second explanation:**  
> "This tool ingests parsed Windows EVTX files, sends delimited events to an LLM for structured extraction, validates the output against a strict schema, and generates a deterministic SOC-style report. The LLM extracts intelligence; Python enforces safety and formats the narrative. It never takes actions, makes determinations, or operates without human review."

**Analogy used:**  
> “It’s like a junior SOC analyst that can read a pile of logs very fast, summarize patterns, suggest hypotheses, and cite evidence — but it can’t touch production systems and must justify everything it says.”

---

## Architect Closing Check

If every remaining blank in this document is filled, the project will satisfy all known assignment and interview requirements.
