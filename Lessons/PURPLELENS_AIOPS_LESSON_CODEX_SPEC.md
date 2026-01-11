# PURPLELENS_AIOPS_LESSON_CODEX_SPEC.md
## Purpose
This is a **CodeX content build spec** to generate a teachable AIOps lesson that uses **PurpleLens** as the anchor example, while generalizing to real-world AIOps across systems.

**Output must be lesson-ready**: a single markdown lesson (plus optional supporting files) that I can publish in my repo and use for interview practice.

---

## Fit Note (Current Repo Status)
This lesson spec assumes the AIOps V1 harness exists (runs/<run_id>/ artifacts, run_log.jsonl, metrics.json).
If the harness is not implemented yet, treat the lesson as forward-looking and use placeholder commands.

---

## Lesson Output Requirements
CodeX must produce:

1) `LESSON_AIOPS_WITH_PURPLELENS.md` (primary lesson)
2) (Optional but helpful) `LESSON_ASSETS/` with:
   - `diagram_aiops_spine.txt` (ASCII diagram)
   - `rca_template.md`
   - `do_d_checklist.md`

Tone: professional, clear, security-engineering oriented.
Assume the reader is new to AIOps but technical.

---

## Lesson Title + Positioning
**Title:**
AIOps for Security Engineers: Operability First (PurpleLens as the Anchor)

**One-sentence hook:**
AIOps is how you turn "a cool AI tool" into a system you can run, debug, and trust under pressure.

---

## Learning Objectives (must include)
By the end of this lesson, I can:
- Explain AIOps in simple terms (what it is / what it is for)
- Implement the AIOps spine (Observe -> Detect -> Diagnose -> Respond safely)
- Apply AIOps to a CLI pipeline (PurpleLens) and generalize to services
- Run a failure drill and produce evidence (logs + metrics + mini-RCA)
- Describe how AIOps reduces MTTR and increases trustworthiness

---

## Lesson Structure (must match)
### Section 1 - What AIOps is (plain language)
- Define AIOps: operations + telemetry + automation to reduce time-to-detect and time-to-recover
- Clarify what it is NOT (not a vendor product, not auto-remediation everywhere)

### Section 2 - Why AIOps matters for AI systems
- AI adds nondeterminism, cost variability, and new failure modes
- Security context: auditability, evidence, incident response readiness

### Section 3 - The "Thin AIOps Spine" (core concept)
Teach 4 capabilities with a simple diagram:

OBSERVE -> DETECT -> DIAGNOSE -> RESPOND (safely)

Include:
- definitions
- minimal viable implementation
- what good looks like

### Section 4 - PurpleLens mapping (anchor example)
Explain:
- What a "request" means in PurpleLens (one CLI run)
- What a correlation ID is in CLI land (`run_id`)
- What stages are in PurpleLens and how you log them
- Where metrics come from in PurpleLens (metrics.json)

Include a small table mapping:
- AIOps concept + PurpleLens implementation

### Section 5 - Build steps (hands-on)
The lesson must guide the reader to:
- Run PurpleLens
- Locate artifacts (`runs/<run_id>/`)
- Inspect `run_log.jsonl`
- Inspect `metrics.json`
- Generate `evidence.txt`

Provide both PowerShell and bash examples where reasonable.

### Section 6 - Failure Drill #1 (hands-on)
Walk through:
- "Good run" baseline
- Break it intentionally (choose one: missing key, malformed JSONL, bad file path)
- Recover using only logs + metrics
- Write a mini RCA using the template

### Section 7 - Generalize beyond PurpleLens (the transfer learning)
Show how the same spine applies to:
- APIs (request/response services)
- async pipelines (queues, workers)
- agent systems (tool calls, memory, loops)
- SOC workflows (alerts, incidents, triage)

Include 2-3 concrete examples:
- "agent tool timeout"
- "prompt injection attempt causing refusal spikes"
- "sudden token cost explosion due to larger context"

### Section 8 - The rubric for building (must include)
Teach and apply:
**Ship -> Observe -> Break/Fix -> Explain -> Teach -> Harden**

Explain:
- how this creates portfolio proof
- why it is interview-grade credibility

### Section 9 - Checklists + templates
Include:
- AIOps V1 Definition of Done checklist
- Mini-RCA template
- "Evidence artifact" template (what to capture)

### Section 10 - Reflection + interview talk track
Include:
- 5 reflection questions
- 2-minute talk track script:
  - what PurpleLens is
  - how AIOps was added
  - what failure drill proved
  - why it matters operationally

---

## Required Diagrams (ASCII OK)
Include at least one ASCII diagram.

Example style:
- "pipeline stages"
- "AIOps spine"
- "run_id correlation flow"

---

## Required Practical Exercises
Must include 3 exercises:
1) Add/verify correlation_id in logs
2) Use metrics to detect a failure trend (error_count increase)
3) Run failure drill + RCA

---

## Security-Specific Constraints to Teach
The lesson must explicitly mention:
- Don't log secrets
- Avoid logging raw sensitive payloads
- Log *evidence pointers*, not everything (file name, record index, event ID)
- Prefer deterministic reporting for claims; LLM outputs are structured hints

---

## Acceptance Criteria (Lesson is "done" when)
- The lesson is understandable end-to-end without extra context.
- A reader can run PurpleLens and find `runs/<run_id>/` artifacts.
- The lesson includes commands, expected outputs, and troubleshooting tips.
- The lesson includes a generalization section that clearly transfers to other systems.
- The lesson includes the rubric and how it fits portfolio/interviews.

---

## Extra Instruction to CodeX (important)
When writing examples, align to PurpleLens naming conventions:
- Use `run_id` consistently.
- Reference pipeline stages that exist in PurpleLens (ingest/parse/normalize/sanitize/enrich/llm/validate_output/report/persist).
- If the exact CLI command differs, infer from README and provide a placeholder pattern like:
  `python -m purplelens ...` or `python src/main.py ...`
But **do not invent commands** that clearly conflict with repo structure - inspect the repo first.

---

## Output File(s)
- `LESSON_AIOPS_WITH_PURPLELENS.md` (required)
- `LESSON_ASSETS/rca_template.md` (optional)
- `LESSON_ASSETS/do_d_checklist.md` (optional)
- `LESSON_ASSETS/diagram_aiops_spine.txt` (optional)
