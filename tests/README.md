# Tests

This folder contains pytest-compatible tests for the PurpleLens pipeline.

## Recommended usage
Run the full suite with pytest:
```bash
pytest tests/
```

Run a single file:
```bash
pytest tests/test_phase1d.py
```

## Notes and limitations
- `test_phase1b.py` uses a temporary directory provided by pytest.
- `test_full_flow.py` is skipped when `data/evtx_sample` is missing.
- LLM calls are mocked; tests do not contact external APIs.
