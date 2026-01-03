"""LLM batching and token budget configuration for Phase 3."""

# Batching limits (designed for modern GPT-class models)
MAX_EVENTS_PER_BATCH = 25
MAX_PROMPT_TOKENS = 6000  # Conservative limit leaving headroom for JSON response
BATCH_ORDER = "cluster_then_time"  # Deterministic ordering strategy

# Target model assumptions (no provider changes required)
# Designed for OpenAI GPT-4 class models with 8K context windows
# Batched conservatively to ensure reliable JSON extraction
