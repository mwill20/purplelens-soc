"""Security policy enforcement for LLM responses.

LLM output is untrusted input:
- We enforce behavior, not hope for compliance
- PROHIBITED_PATTERNS blocks false authority claims
- validate_output() inspects all responses before acceptance
"""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# LLM output is untrusted input - enforce behavior with regex guardrails
# Guardrail contract: no false authority or claimed actions; we only recommend.
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    # Prevent first-person claims of taking actions while avoiding false positives
    # like "no action taken" or attacker-action descriptions.
    r"\b(I|we)\b.*\b(took|have taken|has taken|executed|completed|performed)\b.*\baction\b",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
    # Block base64 PowerShell commands (common attack vector)
    r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}",
]


# We enforce behavior, not hope: validate_output() inspects every LLM response
def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """Check the raw LLM response for prohibited language."""

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Security validation: Checking response (%d chars) against %d patterns",
            len(response_text),
            len(PROHIBITED_PATTERNS),
        )

    for pattern in PROHIBITED_PATTERNS:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Security VIOLATION: Pattern '%s' matched (length=%d)",
                    pattern,
                    len(match.group(0)),
                )
            return False, f"Prohibited pattern detected: {pattern}"

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Security validation: PASS - No prohibited patterns found")
    return True, None
