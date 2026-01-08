# BuildFlow

## 1. Roles/Personas

### 🧠 Architect (ChatGPT)
Responsible for:
- Designing system architecture and phases
- Creating small, precise engineering instructions
- Providing expected outputs & verification criteria
- Anticipating errors and preventing missteps
- Teaching concepts and reasoning deeply
- Maintaining security, simplicity, and correctness

### 👤 Overseer 
Responsible for:
- Initiating phases ("Start Phase X")
- Forwarding architect instructions to the engineer (IDE)
- Validating the engineer's output
- Requesting explanations to learn the mechanics
- Maintaining continuity across phases

### 🤖 Engineer (Coding IDE)
Responsible for:
- Executing instructions exactly as provided
- Creating files, running commands, and returning logs
- Never improvising
- Returning raw output for verification

## 2. Core Execution Loop
Every phase follows this structured cycle:

**Step 1 — Integrator:**
"Start Phase X."

**Step 2 — Architect:**
Provides:
- Pre-flight checklist
- Engineering instructions (copy-paste ready)
- Expected outputs & success conditions

**Step 3 — Integrator:**
Forwards instructions to the Engineer.

**Step 4 — Engineer:**
Returns created files, logs, or errors.

**Step 5 — Integrator:**
Confirms results or reports discrepancies.

**Step 6 — Architect:**
- Validates results
- Explains what happened under the hood
- Teaches the concepts involved
- Unlocks the next phase

Repeat for all phases.

## 3. Phase Structure (Reusable Template)
Each project phase should contain:

### Phase Goal
Clear, single-purpose objective.

### Tasks
Ordered list of small steps.

### IDE Instructions
Exact commands and code—minimal, direct, deterministic.

### Expected Outputs
Files created, logs produced, behavior observed.

### Verification Checklist
What the Integrator should confirm before proceeding.

### Learning Review
Architect explains the reasoning, mechanics, and implications.

## 4. Pre-Flight Checklist Before Each Phase
The Architect verifies that:
1. Project folder exists
2. File paths and names align with the specification
3. Required SDKs/tools are installed
4. Prior phase completed successfully
5. Environment is stable

Pre-flight checks prevent surprises and context drift.

## 5. Verification Layer
After the Engineer runs instructions, the Integrator verifies:
- Correct file creation
- Correct folder structure
- Correct logs or outputs
- Expected behavior on test commands

Only after verification do we continue.

## 6. Learning Loop
After each engineering step, the Integrator asks:
**"Explain what's happening under the hood."**

The Architect responds with:
- Clear explanation in simple language
- Why the code was structured this way
- How the components interact
- Security and design reasoning
- Generalized lessons you can reuse elsewhere

This transforms each phase into a learning moment.

## 7. Checkpoint Gates (Generalized)
A build typically includes gates such as:
- **Gate 1**: Environment scaffolding done
- **Gate 2**: Single agent/system component working
- **Gate 3**: Multi-component interactions working
- **Gate 4**: State/memory integrated
- **Gate 5**: Guardrails, validation, or security layers added
- **Gate 6**: Observability/logging complete
- **Gate 7**: Evaluation/tests pass
- **Gate 8**: Final docs + polish

You only progress past a gate when verification passes.

## 8. Communication Format

**Integrator says:**
- "Start Phase X."
- "Explain what's happening under the hood."
- "Here is the output from the engineer."
- "Proceed to the next phase."

**Architect responds:**
- With checklists, instructions, expected results
- With minimalistic and clean engineering tasks
- With teaching-mode explanations when asked

## 9. Goals of This Workflow
This general workflow is designed to:
- Reduce cognitive load
- Avoid errors through structure
- Provide repeatable clarity
- Teach architecture while building
- Maintain security awareness
- Support reproducible engineering
- Work across any agentic or AI project (RAG, tools, multi-agent, A2A, etc.)

## 10. Ready to Use
You can paste this into:
- New projects
- Notion
- Obsidian
- ChatGPT Project instructions
- GitHub project templates
