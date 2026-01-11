from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.artifacts import ensure_run_dir, write_metrics, write_what_broke
from src.ops.json_logger import JsonLogger
from src.ops.metrics import MetricsCollector


def _basename(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return Path(value).name
    except OSError:
        return value


@dataclass
class OpsContext:
    run_id: str
    run_dir: Path
    json_logger: JsonLogger
    metrics: MetricsCollector
    source_type: str = "unknown"

    def set_source_type(self, source_type: str) -> None:
        if source_type:
            self.source_type = source_type
            self.metrics.set_source_type(source_type)

    def log_run_start(self, payload: dict[str, Any]) -> None:
        event = {"stage": "run", "event": "run_start", "ok": True}
        event.update(payload)
        self._log(event)

    def log_summary(self, ok: bool) -> None:
        self._log(
            {
                "stage": "run",
                "event": "summary",
                "ok": ok,
                "duration_ms": self.metrics.total_duration_ms,
            }
        )

    def stage_start(
        self,
        stage: str,
        source_file: str | None = None,
        records_in: int | None = None,
    ) -> None:
        self.metrics.stage_start(stage)
        self._log(
            {
                "stage": stage,
                "event": "stage_start",
                "ok": True,
                "source_file": _basename(source_file),
                "records_in": records_in,
            }
        )

    def stage_end(
        self,
        stage: str,
        ok: bool = True,
        source_file: str | None = None,
        records_in: int | None = None,
        records_out: int | None = None,
        duration_ms: int | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        duration = duration_ms if duration_ms is not None else self.metrics.stage_end(stage)
        payload = {
            "stage": stage,
            "event": "stage_end",
            "ok": ok,
            "duration_ms": duration,
            "source_file": _basename(source_file),
            "records_in": records_in,
            "records_out": records_out,
        }
        if extra_fields:
            payload.update(extra_fields)
        self._log(payload)

    def exception(
        self, stage: str, error_type: str, error_msg: str | None
    ) -> None:
        duration = self.metrics.stage_end(stage)
        self.metrics.record_error(error_type)
        self._log(
            {
                "stage": stage,
                "event": "exception",
                "ok": False,
                "duration_ms": duration,
                "error_type": error_type,
                "error_msg": (error_msg or "")[:200],
            }
        )
        write_what_broke(self.run_dir, stage, error_type, error_msg)

    def record_llm_calls(self, count: int) -> None:
        self.metrics.record_llm_calls(count)

    def finalize(self, ok: bool) -> Path:
        self.metrics.finalize(ok)
        metrics_path = write_metrics(self.run_dir, self.metrics)
        self.log_summary(ok)
        return metrics_path

    def _log(self, payload: dict[str, Any]) -> None:
        base = {
            "level": "INFO" if payload.get("ok", True) else "ERROR",
            "run_id": self.run_id,
            "source_type": self.source_type,
            "llm_tokens_in": self.metrics.llm_tokens_in_total,
            "llm_tokens_out": self.metrics.llm_tokens_out_total,
            "llm_cost_usd": round(self.metrics.llm_cost_usd_total, 6),
            "source_file": None,
            "records_in": None,
            "records_out": None,
            "duration_ms": None,
            "error_type": None,
            "error_msg": None,
            "prompt_injection_hits": None,
            "events_sanitized": None,
            "events_quarantined": None,
            "affected_event_ids": None,
            "sanitized_event_refs": None,
            "quarantined_event_refs": None,
        }
        base.update(payload)
        self.json_logger.log(base)


def create_ops_context(run_id: str) -> OpsContext:
    run_dir = ensure_run_dir(run_id)
    json_logger = JsonLogger(run_dir / "run_log.jsonl")
    metrics = MetricsCollector(run_id=run_id)
    return OpsContext(
        run_id=run_id,
        run_dir=run_dir,
        json_logger=json_logger,
        metrics=metrics,
    )
