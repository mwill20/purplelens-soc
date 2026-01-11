from __future__ import annotations

import argparse
import json
from pathlib import Path


def _latest_run_dir() -> Path | None:
    runs_dir = Path("runs")
    if not runs_dir.exists():
        return None
    candidates = [p for p in runs_dir.iterdir() if p.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _load_jsonl_lines(path: Path) -> list[dict]:
    lines: list[dict] = []
    if not path.exists():
        return lines
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                lines.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return lines


def _pick_line(lines: list[dict], event_value: str, stage: str | None = None) -> dict | None:
    for item in lines:
        if item.get("event") != event_value:
            continue
        if stage is not None and item.get("stage") != stage:
            continue
        return item
    return None


def _build_evidence(run_dir: Path) -> str:
    log_path = run_dir / "run_log.jsonl"
    metrics_path = run_dir / "metrics.json"

    lines = _load_jsonl_lines(log_path)
    stage_end_line = _pick_line(lines, "stage_end", stage="llm_analyze")
    if stage_end_line is None:
        stage_end_line = _pick_line(lines, "stage_end")
    exception_line = _pick_line(lines, "exception")

    metrics = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    evidence_lines = [
        "EVIDENCE ARTIFACT",
        f"run_dir: {run_dir.as_posix()}",
        "",
        "LOG SNIPPETS:",
    ]

    if stage_end_line:
        evidence_lines.append(json.dumps(stage_end_line, ensure_ascii=False))
    if exception_line:
        evidence_lines.append(json.dumps(exception_line, ensure_ascii=False))
    if not stage_end_line and not exception_line and lines:
        evidence_lines.append(json.dumps(lines[0], ensure_ascii=False))

    evidence_lines.extend(
        [
            "",
            "METRICS SUMMARY:",
            json.dumps(
                {
                    "run_id": metrics.get("run_id"),
                    "total_duration_ms": metrics.get("total_duration_ms"),
                    "error_count": metrics.get("error_count"),
                    "llm_calls": metrics.get("llm_calls"),
                    "llm_tokens_in_total": metrics.get("llm_tokens_in_total"),
                    "llm_tokens_out_total": metrics.get("llm_tokens_out_total"),
                    "llm_cost_usd_total": metrics.get("llm_cost_usd_total"),
                    "prompt_injection_hits": metrics.get("prompt_injection_hits"),
                    "events_sanitized": metrics.get("events_sanitized"),
                    "events_quarantined": metrics.get("events_quarantined"),
                },
                ensure_ascii=False,
            ),
        ]
    )

    return "\n".join(evidence_lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PurpleLens evidence artifact")
    parser.add_argument("--run-id", help="Specific run_id to extract")
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id if args.run_id else _latest_run_dir()
    if not run_dir:
        print("No runs directory found.")
        return 1
    if not run_dir.exists():
        print(f"Run not found: {run_dir}")
        return 1

    evidence = _build_evidence(run_dir)
    evidence_path = run_dir / "evidence.txt"
    evidence_path.write_text(evidence, encoding="utf-8")
    print(evidence)
    print(f"Evidence written to {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
