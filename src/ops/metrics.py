from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MetricsCollector:
    run_id: str
    started_at_utc: str = field(default_factory=_utc_timestamp)
    ended_at_utc: str | None = None
    total_duration_ms: int | None = None
    ok: bool = True
    error_count: int = 0
    source_type_counts: Dict[str, int] = field(default_factory=dict)
    files_processed: int = 0
    records_processed_total: int = 0
    llm_calls: int = 0
    llm_tokens_in_total: int = 0
    llm_tokens_out_total: int = 0
    llm_cost_usd_total: float = 0.0
    prompt_injection_hits: int = 0
    events_sanitized: int = 0
    events_quarantined: int = 0
    top_errors: Dict[str, int] = field(default_factory=dict)
    _stage_starts: Dict[str, float] = field(default_factory=dict, init=False)
    _run_start: float = field(default_factory=time.perf_counter, init=False)

    def stage_start(self, stage: str) -> None:
        self._stage_starts[stage] = time.perf_counter()

    def stage_end(self, stage: str) -> int | None:
        start = self._stage_starts.pop(stage, None)
        if start is None:
            return None
        return int((time.perf_counter() - start) * 1000)

    def record_error(self, error_type: str) -> None:
        self.error_count += 1
        self.top_errors[error_type] = self.top_errors.get(error_type, 0) + 1

    def record_llm_calls(self, count: int) -> None:
        self.llm_calls += max(0, count)

    def record_llm_tokens(
        self, tokens_in: int | None = None, tokens_out: int | None = None, cost_usd: float | None = None
    ) -> None:
        if tokens_in:
            self.llm_tokens_in_total += tokens_in
        if tokens_out:
            self.llm_tokens_out_total += tokens_out
        if cost_usd:
            self.llm_cost_usd_total += cost_usd

    def record_prompt_injection(
        self, hits: int, events_sanitized: int, events_quarantined: int
    ) -> None:
        self.prompt_injection_hits += max(0, hits)
        self.events_sanitized += max(0, events_sanitized)
        self.events_quarantined += max(0, events_quarantined)

    def set_source_type(self, source_type: str) -> None:
        if not source_type:
            return
        self.source_type_counts[source_type] = self.source_type_counts.get(source_type, 0) + 1

    def set_counts(self, files_processed: int | None, records_processed: int | None) -> None:
        if files_processed is not None:
            self.files_processed = files_processed
        if records_processed is not None:
            self.records_processed_total = records_processed

    def finalize(self, ok: bool) -> None:
        self.ok = ok
        self.ended_at_utc = _utc_timestamp()
        self.total_duration_ms = int((time.perf_counter() - self._run_start) * 1000)

    def to_dict(self) -> Dict[str, object]:
        return {
            "run_id": self.run_id,
            "started_at_utc": self.started_at_utc,
            "ended_at_utc": self.ended_at_utc,
            "total_duration_ms": self.total_duration_ms,
            "ok": self.ok,
            "error_count": self.error_count,
            "source_type_counts": self.source_type_counts,
            "files_processed": self.files_processed,
            "records_processed_total": self.records_processed_total,
            "llm_calls": self.llm_calls,
            "llm_tokens_in_total": self.llm_tokens_in_total,
            "llm_tokens_out_total": self.llm_tokens_out_total,
            "llm_cost_usd_total": round(self.llm_cost_usd_total, 6),
            "prompt_injection_hits": self.prompt_injection_hits,
            "events_sanitized": self.events_sanitized,
            "events_quarantined": self.events_quarantined,
            "top_errors": [
                {"error_type": error_type, "count": count}
                for error_type, count in sorted(self.top_errors.items(), key=lambda item: item[0])
            ],
        }
