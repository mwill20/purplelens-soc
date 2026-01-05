"""AWS CloudTrail event batching for LLM prompt optimization."""

from datetime import datetime, timezone
from typing import Any, Dict, List


def build_aws_batches(
    events: List[Dict[str, Any]], max_batch_size: int
) -> List[Dict[str, Any]]:
    """
    Build deterministic batches of AWS CloudTrail events for LLM processing.

    Strategy:
    1. Group by cluster_id (Phase 2 correlation output)
    2. Sort within groups by event_time, then (source_file, record_index)
    3. Split large clusters across batches while preserving order
    4. Generate stable batch_ids

    Returns list of batch objects with batch_id and events[].
    """
    # Filter to AWS events only
    aws_events = [
        e for e in events if e.get("raw_event", {}).get("source") == "aws_cloudtrail"
    ]
    if not aws_events:
        return []

    # Group by cluster_id (including None/unclustered)
    clusters: Dict[str | None, List[Dict[str, Any]]] = {}
    for event in aws_events:
        cluster_id = event.get("raw_event", {}).get("cluster_id")
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(event)

    # Sort events within each cluster deterministically
    for cluster_id in clusters:
        clusters[cluster_id].sort(key=_event_sort_key)

    # Build batches respecting size limits
    batches = []
    batch_index = 0

    # Process clusters in deterministic order (None first, then sorted)
    cluster_ids = sorted([cid for cid in clusters.keys() if cid is not None])
    if None in clusters:
        cluster_ids.insert(0, None)

    for cluster_id in cluster_ids:
        cluster_events = clusters[cluster_id]

        # Split large clusters across multiple batches
        for i in range(0, len(cluster_events), max_batch_size):
            batch_events = cluster_events[i : i + max_batch_size]
            batch_id = f"b{batch_index:03d}"

            batches.append(
                {
                    "batch_id": batch_id,
                    "events": batch_events,
                    "cluster_id": cluster_id,
                    "event_count": len(batch_events),
                }
            )
            batch_index += 1

    return batches


def _event_sort_key(event: Dict[str, Any]) -> tuple:
    """Generate deterministic sort key for events."""
    raw_event = event.get("raw_event", {})

    # Parse event time for sorting
    event_time_str = raw_event.get("event_time", "")
    try:
        if event_time_str.endswith("Z"):
            event_time = datetime.fromisoformat(event_time_str[:-1]).replace(
                tzinfo=timezone.utc
            )
        else:
            event_time = datetime.fromisoformat(event_time_str).replace(
                tzinfo=timezone.utc
            )
    except Exception:
        event_time = datetime.min.replace(tzinfo=timezone.utc)

    # Tie-breaker using source file and record index
    source_file = event.get("source_file", "")
    record_index = event.get("record_index", 0)

    return (event_time, source_file, record_index)
