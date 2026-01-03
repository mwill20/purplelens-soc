# PurpleLens Troubleshooting Guide

## Common Issues

### LLM API Errors
**Symptom:** `openai.BadRequestError: Unsupported model`
**Cause:** Model does not support JSON mode
**Fix:** Use a supported model: `--model gpt-4o` or `gpt-4o-mini`

### Empty Analysis Results
**Symptom:** Report shows 0 findings despite events ingested
**Cause:** LLM response did not match extraction patterns
**Fix:** Run with `--verbose` and review logs; verify event data quality

### Source Detection Errors
**Symptom:** "Mixed source types detected"
**Cause:** Directory contains both `.evtx` and CloudTrail `.jsonl`
**Fix:** Specify source explicitly: `--source windows` or `--source aws`

### CSV Converter Errors
**Symptom:** KeyError during CSV conversion
**Cause:** CloudTrail CSV missing required columns
**Fix:** Verify CSV has CloudTrail schema fields (eventTime, eventName, userIdentity)

---

## Recovery Procedures

### Rollback to Baseline
```powershell
git checkout 2b25fc0d  # Pre-AWS baseline commit
```

### Database Corruption
```powershell
Remove-Item db\\analysis.db
# Re-run analysis to rebuild
```

### Test Failures
```powershell
pytest tests/ -v
pytest tests/ -k test_name
```

---

## Performance Notes

- Windows EVTX: ~15 events/sec (parse-limited)
- AWS CloudTrail: ~50 events/batch (LLM-limited)
- Cost: ~$0.01 per 100 CloudTrail events (gpt-4o-mini)
- Database: SQLite handles 10K+ analysis runs without degradation
