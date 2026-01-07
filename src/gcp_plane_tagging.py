"""
Conservative GCP plane tagging logic.
Classifies events into Control, Telemetry, or Data planes based on Service and Method.
Deterministic: No external API calls.

Phase 2 of GCP Adapter Stack:
- Called by normalize_gcp_audit() after initial field extraction
- tag_plane() maps service+method to security plane
- Pure function: same input always produces same output
"""


def tag_plane(service: str, method: str) -> str:
    """
    Tag GCP audit events into control/data/telemetry planes.

    Args:
        service: The value of protoPayload.serviceName (e.g., "iam.googleapis.com")
        method: The value of protoPayload.methodName (e.g., "CreateServiceAccountKey")

    Returns:
        One of: "control", "telemetry", "data", "unknown"
    """
    service = (service or "").lower().strip()
    method = (method or "").strip()

    # 1. Control Plane Services (Identity, Org Policy, API Mgmt, KMS)
    # These services govern the security posture of the environment.
    CONTROL_PLANE_SERVICES = {
        "iam.googleapis.com": "*",  # Identity & Access Management
        "cloudresourcemanager.googleapis.com": "*",  # Project/Folder/Org manipulation
        "serviceusage.googleapis.com": "*",  # Enabling/Disabling APIs
        "cloudkms.googleapis.com": "*",  # Key Management (Blast Radius critical)
        "iamcredentials.googleapis.com": "*",  # Service Account Impersonation / Token Gen
    }

    # 2. Logging/Telemetry Specifics (Visibility Risk)
    # Logging isn't just telemetry; changing Sinks is a Control Plane action.
    if service == "logging.googleapis.com":
        if method in {
            "CreateSink",
            "UpdateSink",
            "DeleteSink",
            "CreateExclusion",
            "UpdateExclusion",
            "DeleteExclusion",
        }:
            return "control"
        return "telemetry"  # Normal log writing or reading

    # 3. Pub/Sub Specifics (Telemetry Pipeline Manipulation)
    # Subscription/Topic changes can break SIEM ingestion (control plane impact).
    if service == "pubsub.googleapis.com":
        if method in {
            "CreateSubscription",
            "DeleteSubscription",
            "UpdateSubscription",
            "DetachSubscription",
            "CreateTopic",
            "DeleteTopic",
        }:
            return "control"
        return "telemetry"  # Normal message publishing/consumption

    # Check general control plane list
    if service in CONTROL_PLANE_SERVICES:
        return "control"

    # 4. Telemetry Plane (Monitoring & Tracing)
    # Passive observation data.
    TELEMETRY_SERVICES = {
        "monitoring.googleapis.com": "*",
        "cloudtrace.googleapis.com": "*",
    }

    if service in TELEMETRY_SERVICES:
        return "telemetry"

    # 5. Data Plane (Object Access)
    # Direct interaction with customer data.
    if service == "storage.googleapis.com":
        # Broad check for object/bucket operations
        if method.startswith("storage.objects.") or method.startswith(
            "storage.buckets."
        ):
            return "data"

    return "unknown"  # Conservative default
