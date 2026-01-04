"""AWS event correlation using proximity-based clustering."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List


def correlate_events(
    events: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Add correlation fields to events using time proximity clustering."""
    # Sort by event_time ascending
    sorted_events = sorted(
        events,
        key=lambda e: _parse_event_time(e.get("raw_event", {}).get("event_time", "")),
    )
    clusters = []
    for event in sorted_events:
        assigned = False
        raw_event = event.get("raw_event", {})

        # Try to assign to existing cluster
        for cluster in clusters:
            if _can_join_cluster(event, cluster, config):
                cluster["events"].append(event)
                assigned = True
                break

        # Create new cluster if no match
        if not assigned:
            strategy = _determine_strategy(event, config["cluster_strategies"])
            clusters.append(
                {
                    "strategy": strategy,
                    "events": [event],
                    "first_time": raw_event.get("event_time", ""),
                    "actor": raw_event.get("actor", ""),
                    "src_ip": raw_event.get("src_ip", ""),
                    "primary_resource": _get_primary_resource(
                        raw_event.get("resources", [])
                    ),
                }
            )

    # Apply size limits and assign IDs
    final_clusters = _apply_size_limits(clusters, config["max_cluster_size"])
    return _assign_cluster_ids(final_clusters)


def _parse_event_time(time_str: str) -> datetime:
    """Parse ISO timestamp with fallback."""
    try:
        # Handle various CloudTrail timestamp formats
        if time_str.endswith("Z"):
            return datetime.fromisoformat(time_str[:-1]).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _can_join_cluster(
    event: Dict[str, Any], cluster: Dict[str, Any], config: Dict[str, Any]
) -> bool:
    """Check if event can join existing cluster."""
    if len(cluster["events"]) >= config["max_cluster_size"]:
        return False

    raw_event = event.get("raw_event", {})
    event_time = _parse_event_time(raw_event.get("event_time", ""))
    cluster_time = _parse_event_time(cluster["first_time"])

    # Time window check
    time_diff = abs((event_time - cluster_time).total_seconds())
    if time_diff > config["time_window_seconds"]:
        return False

    # Strategy matching
    strategy = cluster["strategy"]
    actor = raw_event.get("actor", "")
    src_ip = raw_event.get("src_ip", "")
    resources = raw_event.get("resources", [])

    if strategy == "actor_src_ip":
        return actor == cluster["actor"] and src_ip == cluster["src_ip"]
    if strategy == "actor_resource":
        cluster_resources = [
            e.get("raw_event", {}).get("resources", []) for e in cluster["events"]
        ]
        return actor == cluster["actor"] and _shares_resource(
            resources, cluster_resources
        )
    if strategy == "actor_only":
        return actor == cluster["actor"]

    return False


def _determine_strategy(event: Dict[str, Any], strategies: List[str]) -> str:
    """Determine clustering strategy for event."""
    raw_event = event.get("raw_event", {})

    # Priority order matching
    if "actor_src_ip" in strategies:
        if raw_event.get("actor") and raw_event.get("src_ip"):
            return "actor_src_ip"

    if "actor_resource" in strategies:
        resources = raw_event.get("resources", [])
        if raw_event.get("actor") and any(resource != "NONE" for resource in resources):
            return "actor_resource"

    if "actor_only" in strategies:
        if raw_event.get("actor"):
            return "actor_only"

    return "actor_only"  # Fallback


def _shares_resource(resources1: List[str], cluster_resources: List[List[str]]) -> bool:
    """Check if event shares resources with cluster."""
    res1_clean = [resource for resource in resources1 if resource != "NONE"]
    if not res1_clean:
        return False

    for cluster_res_list in cluster_resources:
        cluster_clean = [
            resource for resource in cluster_res_list if resource != "NONE"
        ]
        if set(res1_clean) & set(cluster_clean):
            return True

    return False


def _get_primary_resource(resources: List[str]) -> str:
    """Get primary resource for cluster ID generation."""
    clean_resources = [resource for resource in resources if resource != "NONE"]
    return clean_resources[0] if clean_resources else "NONE"


def _apply_size_limits(
    clusters: List[Dict[str, Any]], max_size: int
) -> List[Dict[str, Any]]:
    """Split oversized clusters deterministically."""
    final_clusters = []

    for cluster in clusters:
        events = cluster["events"]
        if len(events) <= max_size:
            final_clusters.append(cluster)
            continue

        # Split into chunks
        for i in range(0, len(events), max_size):
            chunk_events = events[i : i + max_size]
            final_clusters.append(
                {
                    **cluster,
                    "events": chunk_events,
                    "split_index": i // max_size,
                }
            )

    return final_clusters


def _assign_cluster_ids(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign deterministic cluster IDs and add fields to events."""
    result_events = []
    seed_counts: Dict[str, int] = {}

    for cluster_idx, cluster in enumerate(clusters):
        # Generate deterministic cluster ID
        seed_base = (
            f"{cluster['strategy']}|{cluster['actor']}|{cluster['src_ip']}|"
            f"{cluster['primary_resource']}|{cluster['first_time']}"
        )
        if cluster.get("split_index") is not None:
            seed_base += f"|split_{cluster['split_index']}"

        seed_counts[seed_base] = seed_counts.get(seed_base, 0) + 1
        seed = seed_base
        if seed_counts[seed_base] > 1:
            seed = f"{seed_base}|dup_{seed_counts[seed_base] - 1}"

        cluster_id = (
            f"{cluster['strategy']}_{hashlib.sha1(seed.encode()).hexdigest()[:10]}"
        )
        cluster_size = len(cluster["events"])

        # Add correlation fields to each event
        for event_idx, event in enumerate(cluster["events"]):
            raw_event = event.get("raw_event", {})
            raw_event.update(
                {
                    "cluster_id": cluster_id,
                    "cluster_strategy": cluster["strategy"],
                    "cluster_index": event_idx,
                    "cluster_size": cluster_size,
                }
            )
            result_events.append(event)

    return result_events
