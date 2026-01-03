# PurpleLens AI SOC Assistant — Demo Script & Runbook

**Purpose:** Step-by-step guide for demonstrating this project in technical interviews or presentations.  
**Duration:** 5-10 minutes (flexible based on audience)  
**Audience:** Security engineers, hiring managers, technical interviewers

---

## Pre-Demo Checklist

**Before the interview/demo, verify:**

- [ ] `.env` file exists with valid `OPENAI_API_KEY`
- [ ] Virtual environment activated
- [ ] Dataset present: `data/evtx_parsed/` has 3 JSONL files (15 events)
- [ ] Tests passing: Run quick validation if time permits
- [ ] Terminal ready with project directory open

**Quick verification command:**
```powershell
# Check environment
python -m src.main --dry-run --input data/evtx_parsed

# Expected output: "Validation successful. Loaded 15 events from data\evtx_parsed"
```

---

## Demo Script (5-Minute Version)

### 1. Introduction (30 seconds)

**What to say:**
> "This is **PurpleLens**, an AI-powered SOC analyst assistant I built to demonstrate secure LLM integration in cybersecurity workflows. It analyzes Windows event logs and produces structured threat intelligence reports while enforcing strict security guardrails."

**Key points:**
- CLI-based tool (deterministic, demo-friendly)
- Uses OpenAI GPT models with Pydantic schema validation
- Real MITRE ATT&CK dataset from public repository

---

### 2. Architecture Overview (60 seconds)

**Show:** README.md architecture section or draw quick diagram

**What to say:**
> "The architecture is designed with security-first principles:
> 1. **Ingestion** — JSONL files loaded with full provenance tracking
> 2. **LLM Analysis** — Constrained prompts request structured JSON only
> 3. **Validation** — Pydantic schemas + regex guardrails block hallucinations
> 4. **Report Generation** — Deterministic Python (no LLM involvement)
> 5. **Persistence** — SQLite stores all analysis runs for auditability"

**Key architectural decisions:**
- Why CLI? Deterministic, secure, fast demos
- Why schemas? Prevent action claims, enforce evidence citations
- Why provenance? Every finding traceable to source file + line number

---

### 3. Dataset Quick Tour (30 seconds)

**Show:** `data/evtx_parsed/` contents

**What to say:**
> "I'm using 3 MITRE ATT&CK-aligned Windows event samples:
> - **Credential Dumping** (T1003) - lsass.exe access
> - **WMIC Command Execution** (T1047) - suspicious remote execution
> - **Lateral Movement** (T1047) - network authentication patterns
>
> These were converted from EVTX to JSONL using a PowerShell script I wrote."

**Show:** Quick peek at one JSONL file (1 line)

---

### 4. Live Execution (2 minutes)

#### **Demo Command:**
```powershell
python -m src.main --input data/evtx_parsed --verbose --model gpt-4o-mini
```

**What to narrate while it runs:**

**During load (first 2 seconds):**
> "Loading 15 events from 3 files with full provenance..."

**During LLM call (next 10-20 seconds):**
> "Calling OpenAI API with a structured prompt. The system prompt includes the full Pydantic schema and security policies—no free-form text generation allowed."

**When report appears:**
> "Here's the output. Notice:
> - **Findings** grouped by severity (HIGH/MEDIUM/LOW)
> - **Evidence** cites exact source file and line number
> - **Hypotheses** include confidence scores (0-1 scale)
> - **IOCs** extracted automatically
> - **Recommendations** suggest next investigative steps
> - **No action claims** — the LLM never says 'I blocked' or 'I removed'"

---

### 5. Key Features Highlight (90 seconds)

#### **Show security guardrails:**
```powershell
# Show the prohibited patterns
grep "PROHIBITED_PATTERNS" src/security.py
```

**What to say:**
> "These regex patterns block dangerous LLM outputs:
> - Action claims: 'I have removed...', 'System modified...'
> - Definitive determinations: 'This is malicious...', 'Confirmed benign...'
> - Any text matching these patterns triggers validation_error status"

#### **Show schema enforcement:**
```powershell
# Show the Pydantic models
grep -A 10 "class Finding" src/schemas.py
```

**What to say:**
> "Pydantic ensures every finding has required fields:
> - Severity (enum: CRITICAL/HIGH/MEDIUM/LOW/INFO)
> - Summary (string)
> - Evidence (list with source_file + record_index)
> - LLM can't return unstructured text or make up fields"

#### **Show database persistence:**
```powershell
# Query the database
sqlite3 db/analysis.db "SELECT run_id, status, model, created_at FROM analysis_runs LIMIT 1;"
```

**What to say:**
> "Every analysis run persists to SQLite for audit trails. You can query findings, hypotheses, IOCs—all timestamped and linked to the original analysis."

---

### 6. Testing & Quality (45 seconds)

**Show:** Test results

```powershell
# Run a quick test suite
python tests/test_phase1a.py
```

**What to say:**
> "The project has 67 automated tests covering:
> - Schema validation
> - Security policy enforcement
> - Malformed input handling
> - LLM error recovery
> - End-to-end integration
>
> 98.5% pass rate. The one failing test is due to enhanced .env file support—a false negative."

---

### 7. Wrap-Up & Technical Discussion (60 seconds)

**Key discussion points:**

1. **Why this architecture?**
   - "I chose CLI over web app for deterministic execution and minimal attack surface"
   - "Schemas prevent hallucination without complex prompt engineering"
   - "Provenance tracking ensures every finding is verifiable"

2. **Production considerations:**
   - "Real deployment would need: rate limiting, API key rotation, log correlation with SIEM"
   - "Dataset is demo-scale (15 events); production would batch 1000s of events"
   - "Could extend to multi-source ingestion (Sysmon, EDR, firewall logs)"

3. **What I learned:**
   - "LLM security is hard—schemas + guardrails are essential"
   - "Testing LLM systems requires creative mocking strategies"
   - "Provenance tracking is critical for SOC analyst trust"

---

## Extended Demo (10-Minute Version)

If you have more time, add these sections:

### Additional Topics:

**8. Code Quality Walkthrough (2 minutes)**
- Show type hints: `grep "def.*->" src/main.py`
- Show logging: `grep "logger\." src/main.py`
- Show error handling: `try/except` blocks in `src/llm_analyze.py`

**9. Development Process (2 minutes)**
- Show validation documents: `ls validation/`
- Explain phase-gated development (1A-1H)
- Discuss Overseer approval process

**10. Future Enhancements (1 minute)**
- GUI (Streamlit dashboard)
- Multi-source log ingestion
- Real-time streaming mode
- MITRE ATT&CK tagging automation
- Multi-agent orchestration (enrichment, triage, escalation)

---

## Interview Question Prep

**Expected questions and answers:**

### **Q: Why not use GPT-4 instead of gpt-4o-mini?**
**A:** "gpt-4o-mini is faster and cheaper for structured extraction tasks. For production, I'd benchmark multiple models and use GPT-4 for complex cases requiring deeper reasoning."

### **Q: How do you handle LLM hallucinations?**
**A:** "Three layers: (1) Pydantic schemas force structured output, (2) regex security policies block dangerous patterns, (3) provenance tracking makes every claim verifiable against source data."

### **Q: What about false positives?**
**A:** "The tool generates hypotheses with confidence scores, not verdicts. Analysts review recommendations and validate findings using the cited evidence. It's augmentation, not automation."

### **Q: Why SQLite instead of a real database?**
**A:** "For an MVP/demo, SQLite is perfect—zero config, portable, sufficient for 1000s of analysis runs. Production would use PostgreSQL for concurrent access and better query performance."

### **Q: How would you scale this?**
**A:** "Horizontally: batch processing with message queues (RabbitMQ/Kafka). Vertically: switch to async API calls, cache frequent queries, use streaming for large event sets. Also consider self-hosted LLMs for cost control."

### **Q: What about sensitive data in logs?**
**A:** "Production needs: PII detection/masking before LLM submission, on-prem LLM deployment, or data residency-compliant APIs (Azure OpenAI with private endpoints)."

### **Q: How do you test LLM integrations?**
**A:** "Mock LLM responses for deterministic unit tests. Use real API with small datasets for integration tests. Validate schema compliance, error handling, and retry logic separately."

---

## Troubleshooting

### Common demo issues:

**Issue: `OPENAI_API_KEY not set`**
- **Fix:** Check `.env` file exists and has uncommented key
- **Prevention:** Run `--dry-run` before demo

**Issue: No events loaded**
- **Fix:** Verify `data/evtx_parsed/*.jsonl` files exist
- **Prevention:** Run dataset preparation script first

**Issue: LLM timeout**
- **Fix:** Use `gpt-4o-mini` instead of `gpt-4` for faster responses
- **Fallback:** Show cached output from validation document

**Issue: Test failures**
- **Fix:** Ensure virtual environment activated
- **Prevention:** Run full test suite before interview

---

## Quick Reference Commands

```powershell
# Setup
git clone https://github.com/mwill20/purplelens-soc.git
cd purplelens-soc
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Edit .env and add OPENAI_API_KEY=sk-...

# Dataset prep (if needed)
.\scripts\prep_evtx.ps1 -InputPath ".\data\evtx_raw" -OutputPath ".\data\evtx_parsed"

# Demo commands
python -m src.main --input data/evtx_parsed --verbose --model gpt-4o-mini
python -m src.main --input data/evtx_parsed --dry-run
python -m src.main --input data/evtx_parsed --output file

# Testing
python tests/test_phase1a.py
python tests/test_full_flow.py

# Database query
sqlite3 db/analysis.db "SELECT * FROM findings;"
```

---

## Post-Demo Follow-Up

**If interviewer asks for code samples:**
- Show `src/schemas.py` (clean Pydantic models)
- Show `src/security.py` (security guardrails)
- Show `tests/test_full_flow.py` (integration test)

**If asked about deployment:**
- Reference validation documents in `validation/`
- Discuss Phase 2 enhancements (see Phase_1_Implementation_Plan_UPDATED.md)
- Explain CI/CD pipeline needs (GitHub Actions, pytest, coverage reporting)

**If asked to walk through code:**
- Start with `src/main.py` (orchestration logic)
- Deep dive into `src/llm_analyze.py` (LLM integration + retry logic)
- Show `src/report.py` (deterministic report generation)

---

## Success Metrics

**Demo went well if interviewer:**
- ✅ Asks about architecture decisions (shows engagement)
- ✅ Requests code walkthrough (technical validation)
- ✅ Discusses production considerations (thinking about real deployment)
- ✅ Asks about security concerns (recognizes threat awareness)
- ✅ Comments on code quality/testing (appreciates engineering rigor)

**Red flags (adjust approach):**
- ❌ Confused about LLM integration → simplify explanation
- ❌ Questions about basics (Python, Git) → may need junior-level positioning
- ❌ No technical questions → may not be technical role

---

## Final Tips

1. **Practice the 5-minute version** until you can deliver it smoothly
2. **Have backup outputs ready** in case of API failures
3. **Tailor the depth** to interviewer seniority (junior vs. senior vs. architect)
4. **Emphasize security awareness** throughout—this is a cybersecurity project
5. **Be honest about limitations**—shows maturity and production thinking

**Good luck with your demo!** 🚀
