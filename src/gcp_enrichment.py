"""
GCP Enrichment Logic (Phase 3).
Deterministic classification of Actors and Automation Tools with confidence scoring.
"""

import re
from typing import Optional

# WEAK SIGNALS: User-Agent string patterns (hints, not proof)
# Normalized with prefixes: iac_, cli_, sdk_, cicd_, workflow_
AUTOMATION_SIGNALS = {
    # IaC
    "terraform": "iac_terraform",
    "pulumi": "iac_pulumi",
    "ansible": "cfg_ansible",
    # GCP tooling
    "google-cloud-sdk": "cli_gcloud",
    "gcloud/": "cli_gcloud",
    "cloud-sdk": "cli_gcloud",
    # SDKs (usually automation/workloads)
    "google-cloud-go/": "sdk_go",
    "google-cloud-python": "sdk_python",
    "google-api-python-client": "sdk_python",
    "aws-sdk-go": "sdk_go",
    "boto3": "sdk_python",
    "botocore": "sdk_python",
    # CI/CD systems
    "cloudbuild": "cicd_cloud_build",
    "github-actions": "cicd_github_actions",
    "actions.github.com": "cicd_github_actions",
    "jenkins": "cicd_jenkins",
    "bitbucket": "cicd_bitbucket",
    "circleci": "cicd_circleci",
    "gitlab": "cicd_gitlab",
    # Workflow / automation runners
    "tines": "workflow_tines",
    "n8n": "workflow_n8n",
    "temporal": "workflow_temporal",
}


def classify_actor_type(email: str) -> str:
    """
    Distinguish Human vs Service Account based on email domain.
    STRONG TELL for GCP automation.
    """
    if not email:
        return "unknown"

    email = email.lower().strip()

    # Service Accounts always end in .gserviceaccount.com
    if email.endswith(".gserviceaccount.com"):
        return "service_account"

    # Google Managed Service Agents (e.g., backup-rotation@...)
    if "google-cloud" in email or "gcp-sa-" in email:
        return "google_service_agent"

    # Assume everything else is human (or at least user-managed)
    return "human"


def detect_automation_tool(user_agent: str) -> Optional[str]:
    """
    Check User Agent for known IaC or CI/CD tool signatures.
    WEAK SIGNAL - requires corroboration from strong tells.
    Returns normalized tool label (e.g., 'iac_terraform', 'sdk_go').
    """
    if not user_agent:
        return None

    ua_lower = user_agent.lower()

    for pattern, label in AUTOMATION_SIGNALS.items():
        if pattern in ua_lower:
            return label

    return None


def detect_workload_identity(principal_subject: str) -> bool:
    """
    Check for GKE workload identity pattern.
    STRONG TELL for Kubernetes-orchestrated automation.
    Format: principal://iam.googleapis.com/projects/.../locations/.../workloadIdentityPools/.../subject/ns/.../sa/...
    """
    if not principal_subject:
        return False
    return "workloadIdentityPools" in principal_subject


def is_private_ip(ip_address: str) -> bool:
    """
    Check if IP is RFC1918 private address (runtime context hint).
    SUPPORTING TELL - runtime/workload likely.
    """
    if not ip_address:
        return False

    # Simple RFC1918 check (10.x, 172.16-31.x, 192.168.x)
    if ip_address.startswith("10."):
        return True
    if ip_address.startswith("192.168."):
        return True
    if ip_address.startswith("172."):
        try:
            second_octet = int(ip_address.split(".")[1])
            return 16 <= second_octet <= 31
        except (IndexError, ValueError):
            return False
    return False


def is_cross_project(actor_email: str, resource_name: str) -> bool:
    """
    Check if the Actor's Project ID differs from the Resource's Project ID.
    Simple heuristic: extract project ID from SA email and Resource string.
    """
    if not actor_email or not resource_name:
        return False

    # Only applicable to Service Accounts
    if not actor_email.endswith(".gserviceaccount.com"):
        return False

    # Extract SA Project: sa-name@PROJECT-ID.iam.gserviceaccount.com
    try:
        sa_project = actor_email.split("@")[1].split(".iam")[0]
    except IndexError:
        return False

    # Extract Resource Project: projects/PROJECT-ID/...
    # or implicit in resource name
    res_project = None
    match = re.search(r"projects/([^/]+)/", resource_name)
    if match:
        res_project = match.group(1)

    if sa_project and res_project:
        return sa_project != res_project

    return False


def compute_automation_confidence(
    actor_type: str,
    automation_tool: Optional[str],
    workload_identity: bool,
    private_ip: bool,
) -> str:
    """
    Multi-layered confidence scoring for automation attribution.

    HIGH: service account OR workload identity + supporting signals
    MEDIUM: CI/IaC user agent alone
    LOW: gcloud alone (humans use it too)
    NONE: no automation signals
    """
    # STRONG TELLS (high confidence)
    if actor_type == "service_account":
        return "high"

    if workload_identity:
        return "high"

    # MEDIUM: automation tool detected but no strong identity tell
    if automation_tool:
        # Exception: gcloud alone is weak (humans use it)
        if automation_tool == "cli_gcloud":
            return "low"
        # IaC or CI/CD tools = medium confidence
        if automation_tool.startswith(("iac_", "cicd_", "sdk_")):
            return "medium"

    # SUPPORTING: private IP suggests runtime but not conclusive
    if private_ip and not automation_tool:
        return "low"

    return "none"
