# Branch Strategy: AWS CloudTrail Enhancement

**Branch:** `enhancement/aws-cloudtrail`  
**Base Commit:** `2b25fc0d9af9b39dc5cf87a6ea18a13813409fe1` (verified baseline)  
**Target:** `master`  
**Created:** January 2, 2026

---

## 🎯 Branch Purpose

Add AWS CloudTrail ingestion adapter to PurpleLens while preserving:
- Core pipeline integrity
- Windows EVTX functionality (zero regression)
- Architecture invariants (LLM extraction-only, evidence-mandatory, deterministic reports)

---

## 🔒 Protection Strategy

### Master Branch Protection Rules

**Direct commits to `master` are PROHIBITED.**

All changes must follow this workflow:

1. **Development:** Work on `enhancement/aws-cloudtrail`
2. **Verification:** Pass all acceptance gates (see below)
3. **Pull Request:** Create PR from `enhancement/aws-cloudtrail` → `master`
4. **Review:** Overseer approval required
5. **Merge:** Squash merge only (clean history for demo/interview)

---

## 📋 Pre-Merge Acceptance Gates

### Gate 1: Regression Prevention
**Required:** All baseline tests must still pass

```powershell
# Run from project root
.\.venv\Scripts\python.exe tests/test_phase1a.py
.\.venv\Scripts\python.exe tests/test_phase1b.py
.\.venv\Scripts\python.exe tests/test_full_flow.py
```

**Acceptance Criteria:**
- ✅ All 3 tests output "PASSED"
- ✅ Windows EVTX workflow unchanged (15 events, 1 finding, report generated)

---

### Gate 2: AWS Adapter Tests
**Required:** New AWS tests pass

```powershell
# Phase-specific tests (created during development)
.\.venv\Scripts\python.exe tests/test_aws_normalization.py
.\.venv\Scripts\python.exe tests/test_aws_plane_tagging.py
.\.venv\Scripts\python.exe tests/test_aws_full_flow.py
```

**Acceptance Criteria:**
- ✅ Normalization handles required/optional fields correctly
- ✅ Plane tagging heuristics deterministic
- ✅ End-to-end AWS flow produces report + SQLite persistence
- ✅ Negative tests catch malformed data and guardrail violations

---

### Gate 3: Documentation Completeness
**Required:** README updated with AWS usage

**Checklist:**
- [ ] Dataset source documented (Kaggle flaws.cloud)
- [ ] **Critical limitation disclosure** (synthetic CTF data, not production)
- [ ] Correlation disclaimer (grouping ≠ proof)
- [ ] CLI usage example: `python -m src.main --source aws --input data/aws_cloudtrail_sample/`
- [ ] Auto-detect behavior documented

---

### Gate 4: Schema & Guardrail Integrity
**Required:** Architecture invariants enforced

**Verification:**
```powershell
# Test LLM response validation
.\.venv\Scripts\python.exe tests/test_guardrails_aws.py
```

**Acceptance Criteria:**
- ✅ Pydantic schema rejects malformed LLM output
- ✅ Policy guardrails block "I blocked" / "I remediated" claims
- ✅ Evidence items have mandatory provenance (source_file, record_index)
- ✅ Report generation remains deterministic (Python-written, not LLM)

---

### Gate 5: Performance Baseline
**Required:** Demo dataset runs efficiently

**Test:**
```powershell
# Measure execution time with 50-100 AWS CloudTrail events
Measure-Command { .\.venv\Scripts\python.exe -m src.main --source aws --input data/aws_cloudtrail_sample/ }
```

**Acceptance Criteria:**
- ✅ Completes in < 60 seconds (reasonable for demo)
- ✅ No memory leaks or unbounded growth
- ✅ Logs clearly indicate batch processing (if multi-batch)

---

## 🔄 Merge Process

### Step 1: Final Pre-Merge Verification
Run all gates sequentially:

```powershell
# From enhancement/aws-cloudtrail branch
cd "C:\Projects\Bespin AI Security Analyst Assistant"

Write-Host "=== Gate 1: Regression Prevention ===" -ForegroundColor Cyan
.\.venv\Scripts\python.exe tests/test_phase1a.py
.\.venv\Scripts\python.exe tests/test_phase1b.py
.\.venv\Scripts\python.exe tests/test_full_flow.py

Write-Host "`n=== Gate 2: AWS Adapter Tests ===" -ForegroundColor Cyan
.\.venv\Scripts\python.exe tests/test_aws_normalization.py
.\.venv\Scripts\python.exe tests/test_aws_plane_tagging.py
.\.venv\Scripts\python.exe tests/test_aws_full_flow.py

Write-Host "`n=== Gate 4: Schema & Guardrail Integrity ===" -ForegroundColor Cyan
.\.venv\Scripts\python.exe tests/test_guardrails_aws.py

Write-Host "`n=== Gate 5: Performance Baseline ===" -ForegroundColor Cyan
Measure-Command { .\.venv\Scripts\python.exe -m src.main --source aws --input data/aws_cloudtrail_sample/ } | Select-Object TotalSeconds
```

**All gates must pass before proceeding.**

---

### Step 2: Create Pull Request

```powershell
# Push branch to remote (if applicable)
git push origin enhancement/aws-cloudtrail

# Create PR via GitHub UI or CLI
gh pr create --base master --head enhancement/aws-cloudtrail --title "Add AWS CloudTrail ingestion adapter" --body "See docs/PurpleLens_NorthStar_Enhancement_1_AWS_CloudTrail.md for design rationale."
```

---

### Step 3: Squash Merge

**When PR is approved:**

```powershell
# Option A: Via GitHub UI
# - Click "Squash and merge"
# - Edit commit message:

# Example squash commit message:
```
feat: Add AWS CloudTrail ingestion adapter (#<PR_NUMBER>)

- New adapter: src/ingest_aws.py (normalization + plane tagging)
- Correlation: actor/resource clustering (5-min time window)
- Tests: normalization, plane tagging, guardrails, full flow
- Dataset: Kaggle flaws.cloud sample (IAM/STS/S3 patterns)
- Docs: Critical limitations disclosed (synthetic CTF data)

Phases completed: 0-5 per NorthStar doc
Baseline regression: zero (Windows EVTX unchanged)
Architecture invariants: preserved (LLM extraction-only)
```

**Option B: CLI merge (if not using GitHub)**
```powershell
# From master branch
git checkout master
git merge --squash enhancement/aws-cloudtrail
git commit -m "feat: Add AWS CloudTrail ingestion adapter"
git branch -d enhancement/aws-cloudtrail  # cleanup
```

---

## 🚨 Rollback Procedure

**If AWS enhancement causes issues:**

```powershell
# Revert to baseline
git checkout master
git reset --hard 2b25fc0d9af9b39dc5cf87a6ea18a13813409fe1

# Or revert the squash commit
git revert <squash-commit-sha>
```

**Baseline is always recoverable** via the verified commit `2b25fc0d9af9b39dc5cf87a6ea18a13813409fe1`.

---

## 📊 Branch Status Tracking

### Phase Completion Checklist

Update this checklist as phases complete:

- [x] **Phase 0:** Branch scaffold + guardrail continuity
  - [x] Branch created from verified baseline
  - [x] Baseline verification report documented
  - [ ] `src/ingest_aws.py` stub created
  - [ ] CLI accepts `--source aws|windows`
  - [ ] Baseline tests still pass

- [ ] **Phase 1:** CloudTrail parsing + normalization
  - [ ] Parse JSON/JSONL formats
  - [ ] Normalize to event envelope
  - [ ] Required/optional field handling
  - [ ] Provenance attachment
  - [ ] Tests: test_aws_normalization.py

- [ ] **Phase 2:** Plane tagging + correlation
  - [ ] Control/data/telemetry heuristics
  - [ ] Actor clustering (5-min window)
  - [ ] Resource clustering
  - [ ] Tests: test_aws_plane_tagging.py

- [ ] **Phase 3:** Prompt framing + schema validation
  - [ ] Pydantic schemas (Finding, EvidenceItem, AWSFinding)
  - [ ] Prompt batching (25 events/batch)
  - [ ] Guardrail tests
  - [ ] Tests: test_guardrails_aws.py

- [ ] **Phase 4:** Demo dataset + documentation
  - [ ] Curate 50-100 event sample
  - [ ] README with critical limitations
  - [ ] Correlation disclaimer
  - [ ] License compliance check

- [ ] **Phase 5:** Test coverage
  - [ ] All unit tests
  - [ ] Negative tests (8 cases)
  - [ ] Performance test (<60s)
  - [ ] Regression test (Windows unchanged)
  - [ ] Tests: test_aws_full_flow.py

---

## 🎓 Learning Notes (for Developer)

**This is your first feature branch - here's what's happening:**

### What is a branch?
A branch is like a separate copy of your project where you can make changes without affecting the main version. Think of it as:
- **`master`** = The "official" version that works
- **`enhancement/aws-cloudtrail`** = Your "sandbox" to build AWS features

### Why branch from a specific commit?
We branched from `2b25fc0d9af9b39dc5cf87a6ea18a13813409fe1` because:
1. We **verified** that commit works perfectly (all tests passed)
2. If something breaks during AWS work, we know it's the new code (not pre-existing bugs)
3. We have a clean "rollback point" if needed

### What is squash merge?
Instead of keeping every tiny commit ("fixed typo", "oops forgot semicolon"), squash merge:
- Combines all your commits into **one clean commit**
- Makes the project history easier to read
- Perfect for demos/interviews (shows the feature, not the messy process)

### Protection rules
"No direct commits to master" means:
- You can't accidentally break the working version
- All changes are reviewed (via Pull Request)
- Tests must pass before merging
- **Professional best practice** (shows you understand team workflows)

---

**Questions while developing?**
- Check the NorthStar doc (phase-by-phase instructions)
- Run tests frequently to catch issues early
- Commit often on your branch (it's safe!)
- Ask Overseer for acceptance checks before moving to next phase

---

**Signed:**  
GitHub Copilot (Overseer)  
January 2, 2026
