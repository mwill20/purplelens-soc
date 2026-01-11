# PURPLELENS_AIOPS_CODEX_SPEC.md
## Purpose
This document is a **CodeX build spec** to add a minimal, portable **AIOps V1 ops harness** into the existing PurpleLens project without rewriting the architecture.

**Goal:** Make PurpleLens operable and debuggable like a real service by adding:
- **OBSERVE:** structured JSON logs + correlation ID (`run_id`) + minimal metrics (latency, error_count, tokens/cost)
- **RUNBOOK:** how to run, how to debug, known failures
- **FAILURE DRILL #1:** intentionally break the pipeline and recover using logs + metrics
- **EVIDENCE ARTIFACT:** paste-ready proof output + short "what broke / how I fixed it" note per run

---

## Fit Note (Current Repo Status)
This spec is additive and assumes the ops harness does not exist yet.
Once implemented, the run artifacts will live under runs/<run_id>/ and the lesson spec becomes fully accurate.

---

## Guardrails / Constraints (important)
- Keep changes minimal: **additive**, not a refactor.
- Preserve existing CLI behavior and outputs.
- Do not require Docker or external services for V1.
- Do not introduce a web server for V1.
- Do not log secrets, raw API keys, or full raw log bodies.
- Logs must be **one-line JSON** (JSONL).
- Metrics must be written deterministically to a file for each run.

---

## Define "Request" in PurpleLens
PurpleLens is CLI-first, so a "request" is:

- **One CLI execution / analysis run**

Everything should correlate to a single `run_id`.

---

## Deliverables (CodeX must create/modify)
### New/Updated Files
1) `src/ops/ops_context.py` (new)
2) `src/ops/json_logger.py` (new)
3) `src/ops/metrics.py` (new)
4) `src/ops/artifacts.py` (new)
5) `RUNBOOK.md` (new or updated if exists)
6) `scripts/failure_drill_1.py` (new)
7) `scripts/evidence_artifact.py` (new)
8) `README.md` (update: point to RUNBOOK + ops harness)
9) Minimal edits to the PurpleLens entrypoint (where the run starts) to wrap pipeline execution with ops context.

> Note: If PurpleLens has a different folder layout, adapt paths but keep the same intent and artifacts.

---

## AIOps V1 Design
### 1) Run ID (correlation_id)
At the start of a run:
- Generate `run_id = uuid4()` unless user supplies `--run-id` (optional).
- Store `run_id` in an ops context object.
- Include `run_id` in **every** structured log and in metrics.

### 2) Structured Logs (JSONL)
Write logs to:
- `runs/<run_id>/run_log.jsonl`

Each log line is a **single JSON object**.

**Required log fields**:
- `ts` (ISO8601 UTC)
- `level` (`INFO`, `ERROR`, etc.)
- `run_id`
- `stage` (e.g., `ingest`, `parse`, `normalize`, `sanitize`, `enrich`, `llm_analyze`, `validate_output`, `report`, `persist`)
- `event` (short string: `stage_start`, `stage_end`, `exception`, `summary`)
- `ok` (bool)
- `duration_ms` (for stage_end)
- `source_type` (evtx/aws/gcp/unknown if not known)
- `source_file` (basename only)
- `records_in`, `records_out` (ints; if unknown, omit or set null)
- `error_type` (for failures; e.g. `MissingApiKey`, `MalformedInput`, `LLMError`)
- `error_msg` (truncate to 200 chars; no secrets)
- `llm_tokens_in`, `llm_tokens_out` (if available; else estimate)
- `llm_cost_usd` (estimated OK for V1)

**Stage boundaries**
For each pipeline stage:
- emit `stage_start`
- emit `stage_end` with duration + counts
On exception:
- emit `exception` with `ok=false`, `error_type`, `stage`, `duration_ms` until failure

### 3) Minimal Metrics (file-based)
Write metrics summary to:
- `runs/<run_id>/metrics.json`

**Required metrics fields**:
- `run_id`
- `started_at_utc`, `ended_at_utc`
- `total_duration_ms`
- `ok` (bool)
- `error_count`
- `source_type_counts` (dict)
- `files_processed`
- `records_processed_total`
- `llm_calls`
- `llm_tokens_in_total`, `llm_tokens_out_total`
- `llm_cost_usd_total` (estimate OK)
- `prompt_injection_hits`
- `events_sanitized`
- `events_quarantined`
- `top_errors` (list of {error_type, count})

### 4) Run Artifacts Folder
Create:
- `runs/<run_id>/`

This folder must include:
- `run_log.jsonl`
- `metrics.json`
- `evidence.txt` (created by evidence script or run)
- `what_broke.md` (created only if failure occurs)

### 5) "What broke" note (mini-postmortem)
On failure, write:
- `runs/<run_id>/what_broke.md`

Template (5 bullets):
- What failed (stage + symptom)
- Impact (what did not get produced)
- Root cause (best known)
- Fix applied (exact change)
- Prevention (what to add next: test/guardrail/validation)

---

## Failure Drill #1 (must exist)
Create `scripts/failure_drill_1.py` that:
1) Prints exact commands to run PurpleLens normally (do not start automatically).
2) Runs a "good" analysis command (or provides a sample command) and captures:
   - the `run_id`
   - where the run artifacts are
   - how to inspect logs (`findstr`/`grep` examples)
   - how to view metrics (`cat runs/<run_id>/metrics.json`)
3) Runs a "broken" scenario (choose one):
   - Malformed input file (bad JSONL line)
   - Missing API key (simulate by unsetting env var)
   - Invalid CLI arg / nonexistent file path
4) Shows how to locate the failure by:
   - searching `run_log.jsonl` by `run_id`
   - finding `stage` + `error_type`
   - verifying `error_count` in `metrics.json`

The drill should be runnable on Windows and Linux:
- Provide both `PowerShell` and `bash` command snippets in output.

---

## Evidence Artifact (must exist)
Create `scripts/evidence_artifact.py` that:
- Reads the latest run folder or a provided `--run-id`
- Prints a paste-ready block that includes:
  - 2-3 example JSON log lines (one success stage_end, one exception if available)
  - selected metrics fields (duration, error_count, tokens/cost)
- Writes the same content to:
  - `runs/<run_id>/evidence.txt`

---

## RUNBOOK Requirements
Create `RUNBOOK.md` with:
1) How to run
2) How to debug
   - where artifacts are
   - how to filter logs by run_id
   - how to interpret common fields
3) Known failures
   - Missing API key
   - Malformed JSONL
   - Schema mismatch (AWS/GCP)
   - Rate limit / LLM error
4) What "good" looks like
   - example metrics.json snippet
   - example log line
5) Failure Drill #1 instructions

---

## Integration Points (where CodeX should hook in)
CodeX must identify the PurpleLens entrypoint where a run begins (likely `main.py` / `cli.py` / similar) and wrap:

- run start: create ops context + run folder
- per-stage calls: add start/end logging + timing
- llm call site(s): increment llm_calls, tokens, cost estimates
- exceptions: log exception + write what_broke.md + set ok=false
- run end: write metrics.json

**Do not** change the business logic of parsing/normalizing/report generation. Only wrap it.

---

## Implementation Mapping (Current Repo Layout)
- Entry point: `src/main.py` (wrap run start/end, per-stage logging).
- Ingest:
  - Windows: `src/ingest.py`
  - AWS: `src/ingest_aws.py`
  - GCP: `src/ingest_gcp.py`
- Normalize/Enrich (GCP): `src/ingest_gcp.py` + `src/gcp_enrichment.py`
- LLM: `src/llm_analyze.py` (batch counts -> llm_calls)
- Report: `src/report.py`
- Persist: `src/storage.py`
- Ops harness modules: `src/ops/*.py`
- Run artifacts: `runs/<run_id>/run_log.jsonl`, `runs/<run_id>/metrics.json`, `runs/<run_id>/what_broke.md`

---

## Acceptance Criteria (Definition of Done)
AIOps V1 is complete when:
- Running PurpleLens creates `runs/<run_id>/` with `run_log.jsonl` and `metrics.json`.
- Each run has a `run_id` present in every log line.
- At least 5 stages emit start/end logs with durations.
- A failure run produces `what_broke.md` and increments `error_count`.
- `scripts/failure_drill_1.py` successfully demonstrates a good run and a broken run.
- `scripts/evidence_artifact.py` prints paste-ready proof and writes `evidence.txt`.
- `RUNBOOK.md` explains run, debug, known failures.

---

## Optional V2 (not required now)
- OpenTelemetry tracing
- Prometheus endpoint
- Central log shipping
- Alert rules / SLO enforcement in CI

Do not implement V2 unless explicitly requested.
