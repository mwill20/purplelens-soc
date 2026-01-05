# Contributing to PurpleLens

## Branch Protection Policy

**Do not commit directly to `master`.**

All development work should follow a feature branch workflow.

### Workflow

1. **Create a feature branch** from `master`:
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/your-feature-name
   ```

2. **Develop and test** on your branch:
   - Make commits as needed
   - Run tests frequently
   - Keep commits focused and atomic

3. **Verify all tests pass** before merging:
   ```bash
   pytest tests/
   # Plus any new tests for your feature
   ```

4. **Create a Pull Request** (or squash merge locally):
   ```bash
   # Push to remote
   git push origin feature/your-feature-name

   # Create PR via GitHub UI or:
   gh pr create --base master --head feature/your-feature-name
   ```

5. **Squash merge** when approved:
   - Combines all commits into one clean commit
   - Keeps project history readable
   - Required for all feature merges

### Pre-Merge Checklist

Before merging any feature branch:

- [ ] All existing tests pass (zero regression)
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docs, code comments)
- [ ] Architecture invariants preserved:
  - [ ] LLM is extraction-only (no action claims)
  - [ ] Evidence is mandatory (source + provenance)
  - [ ] Python writes reports (deterministic)
  - [ ] Guardrails block prohibited patterns
  - [ ] SQLite persistence works

---

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where practical
- Docstrings for all public functions
- Maximum line length: 120 characters

### Testing Requirements
- Unit tests for all new modules
- End-to-end tests for new workflows
- Negative tests for error handling
- Mock LLM calls in tests (no live API usage)
- Each test file must include a header comment with **Usage**, **Purpose**, and **Limitations**

### How to Run Tests
Run the full suite:
```bash
pytest tests/
```

Run a single file:
```bash
pytest tests/test_phase1b.py
```

Notes:
- `tests/test_full_flow.py` is skipped if `data/evtx_sample` is missing.
- Tests do not call external APIs; LLM calls are mocked.

### Security Requirements
- **Never commit secrets** (.env files excluded via .gitignore)
- Validate all LLM outputs (Pydantic schemas)
- Enforce policy guardrails (no false authority claims)
- Use parameterized SQL queries (prevent injection)

---

## Architecture Invariants (DO NOT VIOLATE)

These rules are non-negotiable across all features:

1. **LLM is extraction-only**
   - Output must be JSON-only
   - Schema-validated via Pydantic
   - No narrative text generation by LLM

2. **Evidence is mandatory**
   - Every finding references `source_file` + `record_index`
   - Provenance attached to all events
   - Raw data hashed for audit trail

3. **Python writes the report**
   - Deterministic formatting
   - LLM does not write narrative
   - Reproducible output

4. **Policy guardrails run after schema validation**
   - Block "I blocked", "I remediated"
   - Block "definitely malicious", "confirmed"
   - Block any claims of completed actions

5. **SQLite persistence**
   - Store run metadata
   - Store structured findings
   - Store final report text
   - Enable audit trail

---

## Getting Help

- **Architecture:** See `docs/ARCHITECTURE.md`
- **Demo runbook:** See `docs/DEMO_SCRIPT.md`
- **Troubleshooting:** See `docs/TROUBLESHOOTING.md`
- **Test failures:** Re-run with `pytest -vv tests/`

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
