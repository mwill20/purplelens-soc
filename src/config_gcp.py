"""
GCP-specific configuration constants.
Centralizes settings for batching, prompt limits, and future correlation logic.
"""

# Analysis Constraints
GCP_BATCH_CONFIG = {
    "max_events_per_batch": 25,  # Conservative: GCP audit logs are verbose (large JSONs)
    "max_prompt_tokens": 6000,  # Reserve token budget for LLM response
}

# Future-proofing for Phase 2B (Correlation)
# Not active in Phase 1, but defined here to prevent magic numbers later.
GCP_CORRELATION_CONFIG = {
    "enabled": False,
    "time_window_seconds": 300,  # 5 minutes
    "max_cluster_size": 50,
    "cluster_strategies": ["actor_only"],
}
