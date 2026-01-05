"""Security policy enforcement for LLM responses."""

import re
from typing import Optional, Tuple

# Guardrail contract: no false authority or claimed actions; we only recommend.
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    # Prevent first-person claims of taking actions while avoiding false positives
    # like "no action taken" or attacker-action descriptions.
    r"\b(I|we)\b.*\b(took|have taken|has taken|executed|completed|performed)\b.*\baction\b",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
    r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}",
]


def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """Check the raw LLM response for prohibited language."""

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Prohibited pattern detected: {pattern}"
    return True, None
