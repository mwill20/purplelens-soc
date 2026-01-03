"""AWS CloudTrail ingestion adapter (Phase 0 - Stub Only)"""

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def ingest_cloudtrail(path: Path) -> List[Dict[str, Any]]:
    """
    Ingest AWS CloudTrail logs (STUB - Phase 0)

    Args:
        path: Path to CloudTrail log file or directory

    Returns:
        List of normalized events (empty in Phase 0)

    Raises:
        NotImplementedError: Always in Phase 0
    """
    raise NotImplementedError(
        "AWS CloudTrail ingestion is scaffolded in Phase 0; "
        "implemented in Phase 1. Use Windows EVTX data for now."
    )
