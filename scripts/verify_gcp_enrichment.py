#!/usr/bin/env python
"""
Quick verification script for Phase 3 GCP enrichment.
Tests enrichment functions against synthetic mini-lab data.
"""

import json
from pathlib import Path

from src.gcp_enrichment import (
    classify_actor_type,
    compute_automation_confidence,
    detect_automation_tool,
    detect_workload_identity,
    is_cross_project,
    is_private_ip,
)


def verify_enrichment():
    # Use consolidated master dataset (JSON array) for verification
    data_file = Path("data/gcp_log_pack/minilab_ground_truth_complete.json")

    print("=" * 80)
    print("GCP ENRICHMENT VERIFICATION")
    print("=" * 80)

    # Support either JSONL (per-line JSON) or a single JSON array file.
    with open(data_file, "r", encoding="utf-8") as f:
        text = f.read()
        try:
            # Try parsing as a JSON array first
            parsed = json.loads(text)
            if isinstance(parsed, list):
                events_iter = enumerate(parsed)
            else:
                # Fallback: treat as single object
                events_iter = enumerate([parsed])
        except json.JSONDecodeError:
            # Fallback to per-line JSON (JSONL)
            events_iter = enumerate(
                json.loads(line) for line in text.splitlines() if line.strip()
            )

        for idx, event in events_iter:
            pp = event.get("protoPayload", {})
            auth = pp.get("authenticationInfo", {})
            req_meta = pp.get("requestMetadata", {})

            email = auth.get("principalEmail", "unknown")
            subject = auth.get("principalSubject", "")
            user_agent = req_meta.get("callerSuppliedUserAgent", "")
            caller_ip = req_meta.get("callerIp", "")
            resource_name = pp.get("resourceName", "")

            actor_kind = classify_actor_type(email)
            automation_tool = detect_automation_tool(user_agent)
            workload_identity = detect_workload_identity(subject)
            private_ip = is_private_ip(caller_ip)
            cross_project = is_cross_project(email, resource_name)
            confidence = compute_automation_confidence(
                actor_kind, automation_tool, workload_identity, private_ip
            )

            print(f"\nEvent {idx}:")
            print(f"  Actor: {email}")
            print(f"  User-Agent: {user_agent}")
            print(f"  Caller IP: {caller_ip}")
            print(f"  Resource: {resource_name}")
            print("  ---")
            print(f"  actor_kind: {actor_kind}")
            print(f"  automation_tool: {automation_tool}")
            print(f"  automation_confidence: {confidence}")
            print(f"  workload_identity: {workload_identity}")
            print(f"  cross_project: {cross_project}")
            print(f"  private_ip: {private_ip}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    verify_enrichment()
