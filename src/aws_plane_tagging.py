"""Conservative AWS plane tagging for Phase 2."""


def tag_plane(service: str, action: str) -> str:
    """Tag AWS events into control/data/telemetry planes (conservative)."""
    service = (service or "").lower().strip()
    action = (action or "").strip()

    # Control plane (identity + org + logging control)
    if service in {
        "iam.amazonaws.com",
        "sts.amazonaws.com",
        "organizations.amazonaws.com",
        "kms.amazonaws.com",
    }:
        return "control"

    # CloudTrail special case - logging-blind actions override
    if service == "cloudtrail.amazonaws.com":
        if action in {"StopLogging", "DeleteTrail", "UpdateTrail", "PutEventSelectors"}:
            return "control"
        return "control"  # All CloudTrail is control

    # Telemetry plane
    if service in {
        "logs.amazonaws.com",
        "cloudwatch.amazonaws.com",
        "events.amazonaws.com",
    }:
        return "telemetry"

    # Data plane (object/data access)
    if service == "s3.amazonaws.com":
        if action in {"GetObject", "PutObject", "DeleteObject", "ListBucket"}:
            return "data"

    if service == "dynamodb.amazonaws.com":
        if any(action.startswith(prefix) for prefix in {"Get", "Put", "Update", "Delete", "Query", "Scan"}):
            return "data"

    return "unknown"  # Conservative default
