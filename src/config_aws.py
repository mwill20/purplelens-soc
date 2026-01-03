"""AWS Phase 2 configuration constants."""

CORRELATION_CONFIG = {
    "time_window_seconds": 300,  # 5 minutes
    "max_cluster_size": 50,
    "cluster_strategies": ["actor_src_ip", "actor_resource", "actor_only"],
}
