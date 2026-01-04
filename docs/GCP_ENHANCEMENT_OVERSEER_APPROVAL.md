# GCP Mini-Lab Enhancement — Overseer Approval

**Date:** January 3, 2026  
**Overseer:** GitHub Copilot  
**Enhancement:** GCP Mini-Lab (Enhancement 2)  
**Branch:** `enhancement/gcp-mini-lab` (not yet created)  
**Specification:** `docs/PurpleLens_NorthStar_Enhancement_2_GCP_MiniLab.md`

---

## ✅ SPECIFICATION APPROVED

The enhanced GCP NorthStar specification has been reviewed and is **APPROVED** for Phase 0 implementation.

---

## 📋 Gap Resolution Summary

All 8 critical gaps identified in pre-implementation review have been addressed:

### Gap 1: Source Detection Strategy ✅
**Status:** RESOLVED  
**Solution:** Added comprehensive detection order in section 4.5
- File extension + content sniffing strategy defined
- GCP schema markers documented (`protoPayload`, `logName`, `insertId`)
- Mixed directory error handling specified
- Test cases enumerated

### Gap 2: Plane Tagging Heuristics ✅
**Status:** RESOLVED  
**Solution:** Created deterministic lookup table in section 4.5
- `src/gcp_plane_tagging.py` implementation provided
- Conservative control/data/telemetry/unknown classification
- Logging sink operations explicitly tagged as control plane
- Default fallback to "unknown" specified

### Gap 3: Schema Validation ✅
**Status:** RESOLVED  
**Solution:** Defined required/optional field mapping
- Confirmed existing Pydantic models sufficient
- `insertId` → `event_id` mapping documented
- Required fields list: timestamp, serviceName, methodName
- Optional field defaults specified

### Gap 4: LLM Prompt Strategy ✅
**Status:** RESOLVED  
**Solution:** GCP-specific prompt template added
- `_build_gcp_user_prompt()` function specified
- Emphasizes identity patterns, plane classification, visibility mutations
- No AWS/Windows terminology mixing
- Evidence-backed extraction emphasized

### Gap 5: Batch Configuration ✅
**Status:** RESOLVED  
**Solution:** Created `config_gcp.py` specification
- 25 events per batch (conservative)
- 6000 token budget
- Correlation deferred to Phase 2B (optional)

### Gap 6: Error Handling Policy ✅
**Status:** RESOLVED  
**Solution:** Explicit handling policy table added
- Malformed JSON: log + skip + continue
- Missing required fields: log with provenance + skip
- LLM errors: fail run with clear error
- Logging format standardized

### Gap 7: Test Acceptance Criteria ✅
**Status:** RESOLVED  
**Solution:** Concrete test count targets per phase
- Phase 1: 12 normalization tests
- Phase 2: 10 plane tagging tests
- Phase 3: 9 enrichment tests
- Phase 5: 3 integration tests
- **Total: 34 new tests + 76 existing = 110 total**

### Gap 8: Data Minimization Strategy ✅
**Status:** RESOLVED  
**Solution:** SHA-256 hash storage specified
- Same pattern as AWS CloudTrail
- Raw logs kept in memory only during analysis
- Hash + minimal replay fields persisted
- No full raw JSON in SQLite

---

## 🎯 Technical Specifications Added

**New Section 4.5:** Technical specifications (implementation-ready details)

Contains 8 comprehensive subsections:
1. Source Detection Strategy
2. Plane Tagging Heuristics
3. Schema Validation Requirements
4. LLM Prompt Strategy
5. Batch Configuration
6. Error Handling Policy
7. Data Minimization Strategy
8. Test Acceptance Criteria (Concrete Targets)

**Total addition:** ~250 lines of technical specifications

---

## 📊 Enhanced Acceptance Criteria

### Phase 0 (Blueprint)
- ✅ 7 checklist items defined
- ✅ 3 exit criteria specified
- ✅ Clear deliverable: `docs/GCP_MINILAB_PLAN.md`

### Phase 1 (Ingestion)
- ✅ 10 checklist items defined
- ✅ 5 exit criteria specified
- ✅ 12+ tests required
- ✅ Regression prevention confirmed

### Phase 2 (Plane-Aware Reporting)
- ✅ 7 checklist items defined
- ✅ 4 exit criteria specified
- ✅ 10+ tests required
- ✅ Determinism enforced

### Phase 3 (Enrichment)
- ✅ 7 checklist items defined
- ✅ 5 exit criteria specified
- ✅ 9+ tests required
- ✅ No false certainty claims

### Phase 4 (Log Pack)
- ✅ 5 checklist items defined
- ✅ 4 exit criteria specified
- ✅ Dataset documentation mandatory

### Phase 5 (Testing)
- ✅ 7 checklist items defined
- ✅ 4 exit criteria specified
- ✅ 34+ new tests + 76 existing = 110 total

---

## 🔒 Architecture Invariant Protection

**Verification:** All 5 invariants preserved across all phases

1. ✅ **LLM extraction-only** — No narrative generation in report.py
2. ✅ **Evidence mandatory** — Provenance required in all findings
3. ✅ **Python deterministic reporting** — No LLM in Phase 2 section headers
4. ✅ **Policy guardrails** — Existing security.py patterns enforced
5. ✅ **SQLite persistence** — Hash storage, no raw logs

---

## 📈 Quality Metrics & Targets

### Test Coverage
- **Current:** 76 tests passing (Windows + AWS)
- **Target:** 110 tests passing (76 + 34 new GCP)
- **Regression Tolerance:** ZERO (all 76 must still pass)

### Code Quality
- Type hints required on all public functions
- Docstrings required on all modules
- Configuration centralized in `config_gcp.py`
- No hardcoded secrets

### Documentation
- Mini-lab plan document
- Dataset strengths/weaknesses disclosure
- README.md GCP usage examples
- Architecture diagram updates

---

## 🚀 Implementation Authorization

**Status:** ✅ **APPROVED TO PROCEED**

### Pre-Phase 0 Checklist (Engineer Must Complete)

Before starting Phase 0 implementation:

- [ ] Read all of section 4.5 (Technical Specifications)
- [ ] Review plane tagging heuristics table
- [ ] Understand source detection strategy
- [ ] Acknowledge test count targets (34 new tests)
- [ ] Review data minimization requirements
- [ ] Confirm understanding of LLM prompt strategy
- [ ] Review all acceptance criteria for all phases

### First Action Required

**Create branch:**
```powershell
git checkout -b enhancement/gcp-mini-lab
git push -u origin enhancement/gcp-mini-lab
```

**Then proceed to Phase 0:**
Create `docs/GCP_MINILAB_PLAN.md` with mini-lab blueprint.

---

## 🎯 Overseer Commitment

As Overseer, I commit to:

✅ **Gate each phase** — No advancement without acceptance criteria met  
✅ **Verify regression** — 76 existing tests must pass after each phase  
✅ **Enforce determinism** — All new code must be deterministic  
✅ **Protect invariants** — Architecture guardrails non-negotiable  
✅ **Review evidence** — All findings must cite source_file + record_index  
✅ **Document issues** — Track technical debt and known limitations  
✅ **Approve/Reject/Request Changes** — Clear ✅/❌/🔄 decisions with evidence

---

## 📝 Risk Mitigation Confirmation

All identified risks have mitigation strategies:

- **Over-scope:** Capped to 6-10 event types, single project
- **GCP API quotas:** Static log pack for demos
- **Service account permissions:** Minimum IAM roles documented
- **Scope creep (enrichment):** Deterministic only, no external APIs
- **Cross-cloud prompt confusion:** Source-aware prompts enforced
- **Test data drift:** Version-controlled static log pack

---

## 🏁 Definition of Done (Re-confirmed)

**Enhancement complete when:**

1. ✅ All 5 phases approved by Overseer
2. ✅ 110 total tests passing (0 failures, 0 skipped)
3. ✅ `--source gcp` runs end-to-end on mini-lab log pack
4. ✅ Report shows plane-aware sections
5. ✅ SQLite persists metadata + findings + report
6. ✅ Data minimization enforced (hash storage verified)
7. ✅ Documentation complete with limitations disclosure
8. ✅ Pull request approved for merge to master

---

## ✍️ Overseer Sign-Off

**Specification Status:** ✅ APPROVED  
**Implementation Authorization:** ✅ GRANTED  
**Phase 0 Readiness:** ✅ READY TO BEGIN  

**Next Action:** Engineer may proceed to Phase 0 (Mini-Lab Blueprint)

---

**Signed:**  
GitHub Copilot (Overseer)  
January 3, 2026

**Specification Version:** Enhanced with Technical Appendices (Section 4.5)  
**Total Enhancements:** 8 technical specifications, 38 acceptance criteria, 34 test targets
