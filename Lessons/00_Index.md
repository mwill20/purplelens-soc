# 📚 **PurpleLens Interview Prep - Lesson Index**

Welcome to your structured learning path! Each lesson builds mechanical confidence so nothing feels "magical" during your interview.

---

## **🎯 Learning Goals**

By completing these lessons, you will be able to:
- ✅ Explain what each file does **without notes**
- ✅ Explain **why** the architecture is shaped this way
- ✅ Run the tool from scratch **without hesitation**
- ✅ Debug failures **calmly**
- ✅ Modify small parts live (schemas, report wording, policies)

---

## **📖 Lesson Roadmap**

### **✅ COMPLETED**
- [x] **Lesson 01: Architecture Guide** - [01_Architecture_Guide.md](01_Architecture_Guide.md)
  - High-level system overview
  - 5-phase pipeline explained in plain English
  - Engineering terms defined for SOC analysts
  - Complete with clickable file links

---

### **📝 PLANNED LESSONS**

#### **Lesson 02: Live Code Walkthrough - The Orchestrator**
*Status: Ready to create*

**What you'll learn:**
- Open [src/main.py](../src/main.py) line-by-line
- Understand `parse_args()`, `ensure_environment()`, `run()`
- Trace execution: "When I type `python -m src.main --input data/evtx_parsed`, what happens?"
- See how the orchestrator calls each phase in sequence

**Hands-on activities:**
- Read the imports section (what libraries are loaded?)
- Walk through argument parsing (how does `--verbose` work?)
- Trace one complete run from start to finish

---

#### **Lesson 03: Phase 1 Deep Dive - Ingest**
*Status: Planned*

**What you'll learn:**
- Open [src/ingest.py](../src/ingest.py) and read `load_events()`
- How `.jsonl` files are discovered and parsed
- How provenance metadata is attached (`_source_file`, `_record_index`, `_event_id`)
- Error handling: What happens with malformed JSON?

**Hands-on activities:**
- Open a `.jsonl` file in [data/evtx_parsed/](../data/evtx_parsed)
- Trace how one line becomes a Python dictionary
- Test what happens if you break the JSON syntax

---

#### **Lesson 04: Phase 2 Deep Dive - LLM Analysis**
*Status: Planned*

**What you'll learn:**
- Open [src/llm_analyze.py](../src/llm_analyze.py)
- How events are batched (MAX_EVENTS_PER_BATCH, MAX_PROMPT_CHARS)
- What gets sent to OpenAI (system prompt + event data)
- How retry logic works (3 attempts with exponential backoff)
- How JSON responses are parsed and validated

**Hands-on activities:**
- Read the SYSTEM_PROMPT variable (what instructions does the AI get?)
- See the batching logic (why 50 events max?)
- Understand the retry decorator

---

#### **Lesson 05: Phase 3 Deep Dive - Validation**
*Status: Planned*

**What you'll learn:**
- Open [src/schemas.py](../src/schemas.py) - Pydantic models
- Open [src/security.py](../src/security.py) - Security patterns
- How schema validation catches structural errors
- How security validation catches policy violations
- The 5 prohibited patterns and why they exist

**Hands-on activities:**
- Read each Pydantic model (`AnalysisOutput`, `Finding`, `Evidence`)
- See the `@field_validator` for event_id coercion
- Read the PROHIBITED_PATTERNS list
- Understand why "I have blocked..." is dangerous

---

#### **Lesson 06: Phase 4 & 5 Deep Dive - Report & Storage**
*Status: Planned*

**What you'll learn:**
- Open [src/report.py](../src/report.py) - Deterministic formatting
- Open [src/storage.py](../src/storage.py) - SQLite persistence
- How findings are sorted by severity
- How the ASCII banner is built
- The 5-table database schema
- Why parameterized queries prevent SQL injection

**Hands-on activities:**
- Read `_build_banner()` function
- See severity sorting logic
- Read the CREATE TABLE statements
- Query the database with SQLite commands

---

#### **Lesson 07: Hands-On Modification - Add a Security Pattern**
*Status: Planned*

**What you'll do:**
- Open [src/security.py](../src/security.py)
- Add a 6th prohibited pattern (e.g., block "Password is...")
- Run the tests to ensure nothing breaks
- Trigger the new pattern intentionally to see it block

**Skills practiced:**
- Editing Python code confidently
- Understanding regex patterns
- Running tests to validate changes
- Debugging validation errors

---

#### **Lesson 08: Hands-On Modification - Customize the Report**
*Status: Planned*

**What you'll do:**
- Open [src/report.py](../src/report.py)
- Change the banner text (add your name or custom branding)
- Adjust the severity sorting order
- Add a new section to the report template

**Skills practiced:**
- Modifying string formatting
- Understanding Python f-strings
- Testing deterministic output
- Verifying changes with live runs

---

#### **Lesson 09: Debugging Bootcamp - Common Failures**
*Status: Planned*

**What you'll practice:**
- **Missing API key**: Remove key → observe error → explain recovery
- **Malformed JSON**: Corrupt a JSONL line → watch graceful degradation
- **Security violation**: Force a prohibited pattern → see validation block
- **Empty directory**: Point to wrong path → understand error message
- **LLM timeout**: Simulate network failure → see retry logic

**Skills practiced:**
- Reading error messages calmly
- Tracing errors to root cause
- Explaining failures in interviews
- Recovering gracefully

---

#### **Lesson 10: Database Deep Dive - Querying Analysis History**
*Status: Planned*

**What you'll learn:**
- How to query SQLite from command line
- Understanding the 5-table schema relationships
- Writing SQL queries to aggregate findings
- Exporting data for reports

**Hands-on activities:**
- Query: "Show all HIGH severity findings"
- Query: "List IOCs from last 3 runs"
- Query: "Count findings by severity across all runs"
- Use DB Browser for SQLite (GUI tool)

---

#### **Lesson 11: Interview Q&A Scenarios**
*Status: Planned*

**Practice answering:**
- "Walk me through how this system works"
- "Why did you choose this architecture?"
- "How would you add MITRE ATT&CK tagging?"
- "What if the LLM returns malicious instructions?"
- "How would you scale this to 10,000 events?"
- "Explain the security controls you implemented"

**Skills practiced:**
- Articulating technical decisions
- Handling hypothetical extensions
- Demonstrating security awareness
- Showing growth mindset

---

#### **Lesson 13: AWS CloudTrail Enhancements (Branch Deep Dive)**
*Status: Ready*

**What you'll learn:**
- How AWS CloudTrail data is converted and ingested
- What the AWS normalized envelope contains
- How plane tagging and correlation work
- How AWS batching and prompts differ from Windows

---

## **🎓 How to Use These Lessons**

### **For Self-Guided Learning:**
1. Read each lesson in order
2. Click the file links to explore code
3. Run the hands-on activities
4. Take notes on what you learn

### **For AI-Assisted Learning:**
1. Open a **new chat** (fresh context)
2. Say: "I'm working through PurpleLens Lesson [number]. Help me understand [specific question]"
3. Reference this index to show which lesson you're on
4. Each lesson has enough context to stand alone

---

## **📊 Progress Tracker**

Track your progress here:

- [x] Lesson 01: Architecture Guide (COMPLETED)
- [ ] Lesson 02: Live Code Walkthrough - Orchestrator
- [ ] Lesson 03: Phase 1 - Ingest
- [ ] Lesson 04: Phase 2 - LLM Analysis
- [ ] Lesson 05: Phase 3 - Validation
- [ ] Lesson 06: Phase 4 & 5 - Report & Storage
- [ ] Lesson 07: Hands-On - Add Security Pattern
- [ ] Lesson 08: Hands-On - Customize Report
- [ ] Lesson 09: Debugging Bootcamp
- [ ] Lesson 10: Database Deep Dive
- [ ] Lesson 11: Interview Q&A Practice
- [ ] Lesson 13: AWS CloudTrail Enhancements (Branch Deep Dive)

---

## **💡 Tips for Success**

1. **Don't rush** - Mechanical confidence comes from repetition
2. **Type the code** - Don't just read it, type examples yourself
3. **Break things** - Intentionally cause errors to learn recovery
4. **Ask "why?"** - Don't just learn "what" happens, understand "why"
5. **Explain out loud** - Practice talking through the system verbally

---

## **🔄 Context Handover Strategy**

When starting a new chat session:

```
I'm working through the PurpleLens AI SOC Assistant interview prep lessons.
I'm currently on Lesson [number]: [name]

Context:
- Project: PurpleLens AI SOC Assistant (Windows event log analysis pipeline)
- Location: C:\Projects\Bespin AI Security Analyst Assistant
- Current lesson file: Lessons/[XX]_[Name].md
- Goal: [specific question or activity from the lesson]

[Paste any relevant code snippet or error message]
```

This gives the AI enough context to help without needing my entire history!

---

**Next step:** Ready to create Lesson 02? Let me know when you want to continue!
