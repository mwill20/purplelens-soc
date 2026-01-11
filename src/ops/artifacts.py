from __future__ import annotations

import json
from pathlib import Path
from src.ops.metrics import MetricsCollector


def ensure_run_dir(run_id: str, base_dir: Path | str = "runs") -> Path:
    run_dir = Path(base_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_metrics(run_dir: Path, metrics: MetricsCollector) -> Path:
    path = run_dir / "metrics.json"
    path.write_text(json.dumps(metrics.to_dict(), indent=2), encoding="utf-8")
    return path


def _truncate(value: str | None, limit: int = 200) -> str:
    if not value:
        return ""
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def write_what_broke(
    run_dir: Path, stage: str, error_type: str, error_msg: str | None
) -> Path:
    path = run_dir / "what_broke.md"
    content = "\n".join(
        [
            "# What Broke",
            "",
            f"- What failed: {stage} ({error_type})",
            "- Impact: (what did not get produced)",
            f"- Root cause: {_truncate(error_msg) or 'unknown'}",
            "- Fix applied: (exact change or action taken)",
            "- Prevention: (test/guardrail/validation to add)",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    return path
