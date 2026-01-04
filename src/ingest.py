"""Load parsed EVTX JSONL files and attach provenance metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB cap
# prevent excessive memory usage
# must split huge logs into chunks


def load_events(input_path: str) -> List[Dict[str, Any]]:
    # Load JSONL files from the provided directory and add provenance data.

    base_path = Path(input_path)
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(
            f"Input path does not exist or is not a directory: {input_path}"
        )

    jsonl_files = sorted(base_path.glob("*.jsonl"))
    if not jsonl_files:
        raise ValueError(f"No JSONL files found in {input_path}")

    events: List[Dict[str, Any]] = []
    for file_path in jsonl_files:
        try:
            size = file_path.stat().st_size
        except OSError as exc:
            logger.warning("Unable to stat file %s: %s", file_path, exc)
            continue

        if size > MAX_FILE_SIZE_BYTES:
            logger.warning("Skipping %s because it exceeds 10 MB limit", file_path)
            continue

        valid_events = _load_file_events(file_path)
        events.extend(valid_events)

    if not events:
        raise ValueError("No valid events were loaded from the provided directory")

    logger.info("Loaded %d events from %s files", len(events), len(jsonl_files))
    return events


def _load_file_events(file_path: Path) -> List[Dict[str, Any]]:
    """Load events from a single JSONL file."""

    records: List[Dict[str, Any]] = []
    try:
        with file_path.open("r", encoding="utf-8-sig") as handle:
            for record_index, line in enumerate(handle):
                stripped = line.strip()
                if not stripped:
                    continue

                try:
                    raw_event = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Skipping malformed JSON in %s at line %d: %s",
                        file_path,
                        record_index + 1,
                        exc,
                    )
                    continue

                records.append(
                    {
                        "source_file": str(file_path),
                        "record_index": record_index,
                        "event_id": _extract_event_id(raw_event),
                        "raw_event": raw_event,
                    }
                )
    except OSError as exc:
        logger.error("Failed to read %s: %s", file_path, exc)

    if not records:
        logger.warning("File %s contained no valid events", file_path)

    return records


def _extract_event_id(raw_event: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of the Windows EventID field."""

    try:
        event_id = raw_event["Event"]["System"]["EventID"]
    except (KeyError, TypeError):
        return None
    return str(event_id)
