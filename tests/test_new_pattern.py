"""
Usage:
  pytest tests/test_new_pattern.py

Purpose:
  Validate the base64 PowerShell guardrail pattern in security.py.

Limitations:
  - Uses synthetic strings; does not parse real event logs.
"""

import json

import pytest

from src.security import validate_output


def _payload(next_steps: list[str]) -> str:
    data = {
        "status": "success",
        "findings": [],
        "hypotheses": [],
        "indicators_of_compromise": [],
        "recommended_next_steps": next_steps,
        "confidence": 0.85,
    }
    return json.dumps(data, ensure_ascii=False)


def test_guardrail_allows_clean_text() -> None:
    response_text = _payload(
        [
            "Review process tree for suspicious activity",
            "Check authentication logs for failed logins",
        ]
    )
    is_valid, _ = validate_output(response_text)
    assert is_valid


@pytest.mark.parametrize(
    "cmd",
    [
        (
            "Run powershell -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAAaAB0AHQAcAA6AC8A"
            "LwBlAHYAaQBsAC4AYwBvAG0ALwBtAGEAbAB3AGEAcgBlAC4AZQB4AGU="
        ),
        "pwsh.exe -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
        "POWERSHELL -e VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
        "powershell.exe -ec VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
    ],
)
def test_guardrail_blocks_base64_powershell(cmd: str) -> None:
    response_text = _payload([cmd])
    is_valid, _ = validate_output(response_text)
    assert not is_valid


def test_guardrail_allows_normal_powershell() -> None:
    response_text = _payload(["Run powershell Get-Process to check for suspicious processes"])
    is_valid, _ = validate_output(response_text)
    assert is_valid
