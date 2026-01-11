# AIOps V1 Definition of Done

- [ ] Each run creates `runs/<run_id>/` with `run_log.jsonl` and `metrics.json`.
- [ ] `run_id` appears in every log line.
- [ ] At least 5 stages emit `stage_start` and `stage_end` logs with durations.
- [ ] A failed run produces `what_broke.md`.
- [ ] `error_count` and `top_errors` are populated when failures occur.
- [ ] Evidence artifact script writes `evidence.txt`.
- [ ] RUNBOOK covers run, debug, and known failures.
