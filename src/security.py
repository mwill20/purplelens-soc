"""Security policy enforcement for LLM responses."""

import re
from typing import Optional, Tuple

# Exact patterns provided by architect spec.
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
]


def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """Check the raw LLM response for prohibited language."""

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Prohibited pattern detected: {pattern}"
    return True, None
