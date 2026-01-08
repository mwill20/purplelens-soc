# 🛡️ **Lesson 05: Phase 3 Deep Dive - Validation (Schema + Security)**

This lesson takes you inside Phase 3, which validates the LLM's output using two complementary mechanisms: **Pydantic schema validation** ([src/schemas.py](../src/schemas.py)) and **security pattern enforcement** ([src/security.py](../src/security.py)).

---

## **🎯 Learning Goals**

By the end of this lesson, you'll be able to:
- ✅ Explain why validation is critical (trust but verify)
- ✅ Understand Pydantic schemas and how they enforce structure
- ✅ Walk through YOUR AnalysisOutput model field-by-field
- ✅ Explain field validators (event_id int→str coercion)
- ✅ Understand the 5 prohibited security patterns
- ✅ Trace how validation catches bad LLM output
- ✅ Debug validation errors
- ✅ Extend validation with custom rules

---

## **📚 Why Validation Matters: Trust But Verify**

### **The Problem**

Phase 2 sends data to OpenAI's GPT model. You're trusting an external AI to:
- Return properly structured JSON
- Follow your schema exactly
- Not include malicious content
- Respect your security rules

**But what if:**
- ❌ GPT returns `{"severity": "SUPER_HIGH"}` instead of `"high"`?
- ❌ GPT claims "I have blocked the threat" when it only analyzed logs?
- ❌ GPT omits required fields like source_file?
- ❌ GPT returns `event_id` as integer instead of string?

**Without validation, garbage in = garbage out!**

### **The Solution: Two-Layer Defense**

**Layer 1: Pydantic Schema Validation** (Structure & type safety, happens FIRST)
- Validates JSON structure after parsing from LLM response
- Enforces data types (strings, integers, floats, lists)
- Validates required vs optional fields
- Checks enums (severity must be "low", "medium", "high", or "critical")
- Coerces types where safe (int → str for event_id)
- Provides clear error messages

**Layer 2: Security Language Policy** (Content safety, happens SECOND)
- Validates the stringified JSON for prohibited language patterns
- Blocks false action claims ("I have blocked...")
- Blocks definitive judgments ("This is malicious...")
- Blocks execution claims ("Action taken...")
- Blocks modification claims ("System patched...")
- Blocks false certainty ("Confirmed that...")

**Together:** Language Policy + Structure = Safe Output

---

## **🔍 Phase 3 Architecture Overview**

### **Where Validation Happens**

In [src/main.py](../src/main.py), lines 116-128:

```python
# Phase 2: LLM Analysis
analysis_data = analyze_events(events, model=args.model)

# Phase 3A: Pydantic Validation (FIRST)
analysis = _validate_analysis_output(analysis_data)  # Line 117

# Phase 3B: Security Validation (SECOND - on stringified JSON)
policy_valid, policy_error = validate_output(
    json.dumps(analysis_data, ensure_ascii=False)
)
if not policy_valid:
    logger.error("Security policy violation: %s", policy_error)
    analysis = _build_error_analysis("validation_error", policy_error)
```

**Two sequential checks:**
1. **Pydantic** (line 117): Structure and types validation
2. **Security** (line 119): Language policy on stringified JSON

**If either fails, the pipeline stops!**

---

## **📋 Part 1: Pydantic Schema Validation**

Open [src/schemas.py](../src/schemas.py) - this defines YOUR data model.

### **What is Pydantic?**

**Pydantic** = A Python library for data validation using type hints

**Key features:**
- Define models using Python classes
- Automatic type conversion (when safe)
- Clear validation errors
- JSON serialization/deserialization
- Used by FastAPI, many AI tools

**Simple example:**
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

# This works
person = Person(name="Alice", age=30)

# This fails (age must be int)
person = Person(name="Bob", age="thirty")  # ValidationError!
```

---

### **YOUR Schema: AnalysisOutput**

Let's read YOUR model line-by-line:

```python
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AnalysisOutput(BaseModel):
    """
    Complete structured output expected from the LLM extraction step.
    """

    status: Literal["success", "validation_error", "llm_error", "timeout"]
    error_message: Optional[str] = None
    findings: List[Finding] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    indicators_of_compromise: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
```

**Breaking down each field:**

---

#### **Field 1: status**

```python
status: Literal["success", "validation_error", "llm_error", "timeout"]
```

**What this means:**
- `Literal[...]` = Enum (must be one of these exact strings)
- Valid values: "success", "validation_error", "llm_error", "timeout"
- **REQUIRED FIELD** - No default value (LLM must provide)
- If GPT returns `status: "FAILED"`, Pydantic raises ValidationError!

**Why Literal instead of Enum class?**
- Simpler for LLMs (just strings)
- Clear in JSON schema sent to GPT
- Less code

---

#### **Field 2: error_message**

```python
error_message: Optional[str] = None
```

**What this means:**
- `Optional[str]` = Can be a string OR None (optional)
- `= None` = Defaults to None if not provided
- If status="llm_error", this should contain the error details

**Type union syntax:**
- `Optional[str]` is equivalent to `Union[str, None]` or `str | None` in Python 3.10+

---

#### **Field 3: findings**

```python
findings: List[Finding] = Field(default_factory=list)
```

**What this means:**
- `List[Finding]` = A list of Finding objects (we'll see this model next)
- `default_factory=list` = If not provided, create empty list `[]`
- Each item in the list must be a valid `Finding` object

**Why default_factory instead of default?**
```python
# WRONG - all instances share the same list!
findings: List[Finding] = Field(default=[])

# RIGHT - each instance gets a new list
findings: List[Finding] = Field(default_factory=list)
```

---

#### **Field 4: hypotheses**

```python
hypotheses: List[Hypothesis] = Field(default_factory=list)
```

**Same pattern as findings**, but for `Hypothesis` objects.

---

#### **Field 5: indicators_of_compromise**

```python
indicators_of_compromise: List[str] = Field(default_factory=list)
```

**What this means:**
- `List[str]` = A simple list of IOC strings (not structured objects)
- Examples: `["wmic.exe", "192.168.1.100", "mimikatz.exe", "lsass.exe"]`
- Simpler than structured IOC objects - just the raw indicators

---

#### **Field 6: recommended_next_steps**

```python
recommended_next_steps: List[str] = Field(default_factory=list)
```

**What this means:**
- `List[str]` = List of strings (not objects)
- Example: `["Review process tree", "Check for lateral movement"]`
- Simpler than findings/hypotheses (just text recommendations)

---

#### **Field 7: confidence**

```python
confidence: float = Field(..., ge=0.0, le=1.0)
```

**What this means:**
- `float` = Decimal number
- `...` = **REQUIRED FIELD** - Ellipsis means no default value
- `ge=0.0` = Greater than or Equal to 0.0
- `le=1.0` = Less than or Equal to 1.0

**Why required instead of default=0.0?**
- **Fail-closed security design** - System refuses to proceed without explicit confidence
- Forces LLM to explicitly assess confidence (no silent defaults)
- Prevents misleading analysts with automatic "0.0" confidence
- Validation fails fast if confidence missing

**Validation constraints:**
- If GPT omits confidence, Pydantic raises ValidationError!
- If GPT returns `confidence: 1.5`, Pydantic raises ValidationError!
- If GPT returns `confidence: -0.3`, Pydantic raises ValidationError!
- Valid range: 0.0 to 1.0 inclusive

---

### **Nested Model 1: Evidence**

Findings use a structured Evidence model for provenance tracking:

```python
class Evidence(BaseModel):
    """Structured reference tying a finding back to a specific artifact."""

    source_file: str = Field(..., description="Path to the source JSONL file")
    record_index: int = Field(
        ..., ge=0, description="Zero-based record index inside the source file"
    )
    event_id: Optional[str] = Field(
        None, description="Event identifier if present in the source data"
    )
    excerpt: str = Field(..., description="Relevant snippet extracted from the event")

    @field_validator('event_id', mode='before')
    @classmethod
    def coerce_event_id_to_string(cls, v):
        """Convert event_id to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v
```

**Key features:**
- **source_file**: Required - which JSONL file the evidence came from
- **record_index**: Required integer ≥ 0 - which line in the file
- **event_id**: Optional string - Windows Event ID (coerced from int if needed)
- **excerpt**: Required - actual text snippet from the event

**Field Validator: event_id Coercion**

```python
@field_validator('event_id', mode='before')
@classmethod
def coerce_event_id_to_string(cls, v):
    """Convert event_id to string if it's an integer."""
    if v is not None and not isinstance(v, str):
        return str(v)
    return v
```

**Why is this needed?**

**Problem:** GPT sometimes returns Event IDs as integers:
```json
{"event_id": 4688}  // Integer (wrong type!)
```

But YOUR schema expects strings:
```python
event_id: Optional[str]
```

**Without the validator:**
```python
Evidence(event_id=4688, ...)  # ValidationError: expected str, got int
```

**With the validator:**
```python
Evidence(event_id=4688, ...)  # Automatically converts to "4688" ✓
```

**This is defensive programming** - accommodate common LLM mistakes!

---

### **Nested Model 2: Finding**

```python
class Finding(BaseModel):
    """Concrete observation identified within the analyzed events."""

    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    evidence: List[Evidence] = Field(..., min_length=1)
```

**Simpler than the lesson's old example:**
- **title**: Required string - brief finding name
- **summary**: Required string - description of the finding
- **severity**: Required literal - must be "info", "low", "medium", "high", or "critical"
- **evidence**: Required list with at least 1 Evidence object

**Key design decision:**
- Evidence is a separate structured model (provenance + excerpt)
- Each finding MUST have at least 1 piece of evidence (`min_length=1`)
- Forces LLM to cite sources for every claim

**Severity Literal:**
```python
severity: Literal["info", "low", "medium", "high", "critical"]
```

**Enforces controlled vocabulary:**
- Must be one of: "info", "low", "medium", "high", "critical"
- Note: "info" added for informational findings (not security issues)
- Prevents: "SUPER_HIGH", "kinda bad", "5", etc.
- Enables sorting/filtering in reports

---

### **Nested Model 3: Hypothesis**

```python
class Hypothesis(BaseModel):
    """Possible explanation that analysts should further investigate."""

    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
```

**Very simple model:**
- **description**: Required string - the hypothesis statement (e.g., "Attacker used mimikatz")
- **confidence**: Required float 0.0-1.0 - how confident the LLM is in this hypothesis
- No severity (hypotheses aren't findings yet)
- No evidence list (simpler than Finding)

---

### **Note: indicators_of_compromise is Just Strings**

Unlike the old design shown above, the actual implementation uses a simple string list:

```python
indicators_of_compromise: List[str] = Field(default_factory=list)
```

**No structured IOC model** - just raw strings:
- Example: `["wmic.exe", "192.168.1.100", "mimikatz.exe", "lsass.exe"]`
- LLM extracts key indicators without type/context metadata
- Simpler to parse, easier for LLM to generate
- Analyst can interpret IOC types from context

**Trade-off:**
- ✅ Simpler schema = less LLM errors
- ✅ Faster to generate
- ❌ No type metadata (is "wmic.exe" a process or file?)
- ❌ No context string (where was it seen?)

**Why this design choice:**
- IOCs are typically obvious from context in the findings
- Simplicity reduces validation errors
- Analysts can manually categorize IOCs if needed

---

## **🧪 How Pydantic Validation Works**

### **The Validation Process**

In [src/main.py](../src/main.py) line 105:

```python
validated = AnalysisOutput.model_validate(analysis_data)
```

**What happens internally:**

1. **Parse input** (analysis_data is a dict from Phase 2)
2. **Check required fields** (status, findings, hypotheses, etc.)
3. **Validate types** (strings are strings, ints are ints, floats are floats)
4. **Check constraints** (confidence is 0.0-1.0, severity is valid literal)
5. **Run field validators** (event_id int→str coercion)
6. **Recursively validate nested objects** (each Finding, Hypothesis, IOC)
7. **Return validated object** OR **raise ValidationError**

---

### **Example: Valid Input**

```python
analysis_data = {
    "status": "success",
    "findings": [
        {
            "title": "Credential Dumping",
            "description": "Process wmic.exe accessed lsass.exe",
            "severity": "high",
            "confidence": 0.85,
            "source_file": "Credential_hashdump.jsonl",
            "record_index": 0,
            "event_id": 4656  # Integer (will be coerced to "4656")
        }
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Review process tree"],
    "confidence": 0.85
}

validated = AnalysisOutput.model_validate(analysis_data)
print(validated.findings[0].event_id)  # "4656" (string now!)
```

**✓ Validation succeeds!** event_id was coerced from int to str.

---

### **Example: Invalid Input - Bad Severity**

```python
analysis_data = {
    "status": "success",
    "findings": [
        {
            "title": "Bad Thing",
            "description": "Something suspicious",
            "severity": "SUPER_HIGH",  # ❌ Invalid literal!
            "confidence": 0.85,
            "source_file": "test.jsonl",
            "record_index": 0
        }
    ],
    "confidence": 0.85
}

try:
    validated = AnalysisOutput.model_validate(analysis_data)
except ValidationError as exc:
    print(exc)
```

**Output:**
```
1 validation error for AnalysisOutput
findings.0.severity
  Input should be 'low', 'medium', 'high' or 'critical' [type=literal_error]
```

**❌ Validation fails!** Clear error message shows exactly what's wrong.

---

### **Example: Invalid Input - Confidence Out of Range**

```python
analysis_data = {
    "status": "success",
    "confidence": 1.5  # ❌ Too high!
}

try:
    validated = AnalysisOutput.model_validate(analysis_data)
except ValidationError as exc:
    print(exc)
```

**Output:**
```
1 validation error for AnalysisOutput
confidence
  Input should be less than or equal to 1.0 [type=less_than_equal]
```

---

## **🔒 Part 2: Security Pattern Enforcement**

Open [src/security.py](../src/security.py) - this scans for malicious content.

### **The 5 Prohibited Patterns (Lines 7-12)**

```python
PROHIBITED_PATTERNS = [
    r"I have (blocked|removed|deleted|remediated)",
    r"This (is|was) (benign|malicious|definitely)",
    r"Action (taken|executed|completed|performed)",
    r"System (modified|updated|patched|fixed)",
    r"(Confirmed|Certain|Guaranteed) that",
]
```

**Let's understand each pattern:**

---

#### **Pattern 1: False Action Claims (Line 8)**

```python
r"I have (blocked|removed|deleted|remediated)"
```

**Breakdown:**
- `I have` = First-person action claim
- `(blocked|removed|deleted|remediated)` = Past-tense action verbs
- Matches case-insensitively via `re.IGNORECASE` flag

**Catches:**
- "I have blocked the malicious process"
- "I have removed the threat"
- "I have deleted the suspicious file"
- "I have remediated the vulnerability"

**Why block this?**
- LLM only analyzes logs - it cannot take actions
- Prevents misleading analysts into thinking automated remediation occurred
- Maintains clear separation: LLM analyzes, humans act

---

#### **Pattern 2: Definitive Judgments (Line 9)**

```python
r"This (is|was) (benign|malicious|definitely)"
```

**Breakdown:**
- `This (is|was)` = Declarative statement
- `(benign|malicious|definitely)` = Absolute classifications
- Matches case-insensitively via `re.IGNORECASE` flag

**Catches:**
- "This is benign activity"
- "This was malicious behavior"
- "This is definitely an attack"
- "This was definitely benign"

**Why block this?**
- LLM provides hypotheses, not definitive verdicts
- Security analysis requires human judgment and context
- Prevents overconfidence that could lead to missed threats or false positives

---

#### **Pattern 3: Action Execution Claims (Line 10)**

```python
r"Action (taken|executed|completed|performed)"
```

**Breakdown:**
- `Action` = Refers to some action
- `(taken|executed|completed|performed)` = Past-tense completion verbs
- Matches case-insensitively via `re.IGNORECASE` flag

**Catches:**
- "Action taken to block the process"
- "Action executed successfully"
- "Action completed at 10:45 AM"
- "Action performed by the system"

**Why block this?**
- LLM cannot execute actions in the real environment
- Prevents confusion about whether automated response occurred
- Analysts must explicitly choose and execute response actions

---

#### **Pattern 4: System Modification Claims (Line 11)**

```python
r"System (modified|updated|patched|fixed)"
```

**Breakdown:**
- `System` = Refers to the actual system
- `(modified|updated|patched|fixed)` = Past-tense change verbs
- Matches case-insensitively via `re.IGNORECASE` flag

**Catches:**
- "System modified to block the threat"
- "System updated with new rules"
- "System patched successfully"
- "System fixed and secure now"

**Why block this?**
- LLM has read-only access to logs, cannot modify systems
- Prevents false confidence that remediation occurred
- Ensures analysts verify actual system state before trusting output

---

#### **Pattern 5: False Certainty Statements (Line 12)**

```python
r"(Confirmed|Certain|Guaranteed) that"
```

**Breakdown:**
- `(Confirmed|Certain|Guaranteed)` = Absolute certainty words
- `that` = Followed by a claim
- Matches case-insensitively via `re.IGNORECASE` flag

**Catches:**
- "Confirmed that this is an attack"
- "Certain that the system is compromised"
- "Guaranteed that no data was exfiltrated"
- "Confirmed that the threat is neutralized"

**Why block this?**
- Security analysis deals with probabilities, not certainties
- LLM should express confidence scores, not absolute verdicts
- Prevents overconfidence that could cause analysts to skip verification

---

### **The Validation Function: validate_output() (Lines 15-22)**

```python
def validate_output(response_text: str) -> Tuple[bool, Optional[str]]:
    """Check the raw LLM response for prohibited language."""

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Prohibited pattern detected: {pattern}"
    return True, None
```

**What this does:**

1. **Accept response text** - Checks a stringified version of the LLM output
2. **Loop through prohibited patterns** - All 5 language policy patterns
3. **Search with regex** - Uses `re.search()` with case-insensitive flag
4. **Return on first violation** - Fails fast when prohibited language detected
5. **Return success tuple** - `(True, None)` if all patterns pass

**Notice:** Unlike the Pydantic validation which checks structured fields, this validates the **text content** to catch prohibited language patterns in any part of the response.

---

### **Key Difference: Post-Parse Security Check**

**Important:** Security validation happens on the **parsed and re-stringified dict** AFTER JSON parsing:

```python
# In src/llm_analyze.py (Phase 2)
response_text = client.chat.completions.create(...)

# Parse JSON first
analysis_data = json.loads(response_text)  # String → Dict
# Return dict to main.py

# In src/main.py (Phase 3)
analysis_data = analyze_events(...)  # Dict returned from Phase 2
analysis = _validate_analysis_output(analysis_data)  # Pydantic validation

# Security check happens AFTER parsing and Pydantic validation
policy_valid, policy_error = validate_output(
    json.dumps(analysis_data, ensure_ascii=False)  # Dict → String for regex scan
)
if not policy_valid:
    analysis = _build_error_analysis("validation_error", policy_error)
```

**Why re-stringify the dict?**
- Regex patterns work on strings, not nested dicts
- Simpler to scan all content at once vs recursively checking each field
- Catches prohibited language regardless of where it appears in the structure
- If JSON parsing failed earlier, this security check never runs (error already returned)

---

## **🎯 How Both Validations Work Together**

### **The Complete Flow**

```
PHASE 2: LLM ANALYSIS
    ↓
  (LLM returns JSON string)
    ↓
  json.loads() → Python dict
    ↓
  (Returns dict to main.py)
    ↓
┌─────────────────────────────────────────────┐
│ Phase 3A: Pydantic Validation (FIRST)       │
│ File: src/schemas.py                        │
│                                             │
│ ✓ Check required fields                    │
│ ✓ Validate types (str, int, float, list)   │
│ ✓ Check constraints (confidence 0.0-1.0)   │
│ ✓ Validate literals (severity enum)        │
│ ✓ Run field validators (event_id coercion) │
│ ✓ Recursively validate nested models       │
│                                             │
│ IF FAILS → analysis = error object         │
│ IF PASSES → analysis = valid object        │
│ Pipeline ALWAYS continues                  │
└─────────────────────────────────────────────┘
    ↓
  json.dumps(dict) → Re-stringify for regex
    ↓
┌─────────────────────────────────────────────┐
│ Phase 3B: Security Validation (SECOND)      │
│ File: src/security.py                       │
│                                             │
│ ✓ Check re-stringified dict for patterns   │
│ ✓ "I have blocked..." → FAIL              │
│ ✓ "This is malicious..." → FAIL           │
│ ✓ "Action taken..." → FAIL                │
│ ✓ "System modified..." → FAIL             │
│ ✓ "Confirmed that..." → FAIL              │
│                                             │
│ IF VIOLATIONS → analysis = error object    │
│ IF CLEAN → Keep existing analysis object   │
│ Pipeline ALWAYS continues                  │
└─────────────────────────────────────────────┘
    ↓
PHASE 4: REPORT GENERATION
    ↓
  generate_report(analysis)
    ↓
  Receives: AnalysisOutput Pydantic object
  - If valid: findings, hypotheses, IOCs, etc.
  - If error: empty arrays, error_message
    ↓
PHASE 5: DATABASE STORAGE
    ↓
  save_analysis(analysis, ...)
    ↓
  Stores: Same AnalysisOutput object
  - Valid data OR error object
  - Both formats persisted for audit trail
    ↓
EXIT CODE
  - 0 if analysis.status == "success"
  - 1 if analysis.status == "validation_error"
  
Pipeline NEVER stops - reports and stores 
results even when validation fails
```

---

## **🧪 Hands-On Exercises**

### **Exercise 1: Test Security Validation**

```python
from src.security import validate_output

# Test 1: Valid response (no prohibited patterns)
valid_response = """
{
  "findings": [{
    "title": "Suspicious LSASS Access",
    "description": "Process wmic.exe accessed lsass.exe memory. This may indicate credential dumping attempt.",
    "severity": "high",
    "confidence": 0.85
  }],
  "recommended_next_steps": [
    "Investigate parent process of wmic.exe",
    "Review authentication logs for unusual activity"
  ]
}
"""

valid, error = validate_output(valid_response)
print(f"✓ Valid response: {valid}")  # Should be True
print(f"Error: {error}")  # Should be None

# Test 2: Invalid - false action claim
invalid_response_1 = """
{
  "findings": [{
    "title": "Malicious Process",
    "description": "I have blocked the malicious process."
  }]
}
"""

valid, error = validate_output(invalid_response_1)
print(f"\n✗ Valid: {valid}")  # Should be False
print(f"Error: {error}")  # Should contain pattern

# Test 3: Invalid - definitive judgment
invalid_response_2 = """
{
  "findings": [{
    "description": "This is definitely malicious activity."
  }]
}
"""

valid, error = validate_output(invalid_response_2)
print(f"\n✗ Valid: {valid}")  # Should be False
print(f"Error: {error}")  # Should contain pattern

# Test 4: Invalid - false certainty
invalid_response_3 = """
{
  "hypotheses": [{
    "hypothesis": "Confirmed that this is an attack."
  }]
}
"""

valid, error = validate_output(invalid_response_3)
print(f"\n✗ Valid: {valid}")  # Should be False
print(f"Error: {error}")  # Should contain pattern
```

---

### **Exercise 2: Test Pydantic Validation**

```python
from src.schemas import AnalysisOutput, Finding
from pydantic import ValidationError

# Test 1: Valid input
valid_data = {
    "status": "success",
    "findings": [
        {
            "title": "Credential Dumping",
            "description": "Process accessed lsass.exe memory",
            "severity": "high",
            "confidence": 0.85,
            "source_file": "Credential_hashdump.jsonl",
            "record_index": 0,
            "event_id": 1234  # Integer - will be coerced to string
        }
    ],
    "confidence": 0.85
}

validated = AnalysisOutput.model_validate(valid_data)
print(f"✓ Validation passed!")
print(f"Event ID type: {type(validated.findings[0].event_id)}")  # Should be str
print(f"Event ID value: {validated.findings[0].event_id}")  # Should be "1234"

# Test 2: Invalid severity
invalid_data = valid_data.copy()
invalid_data["findings"][0]["severity"] = "SUPER_HIGH"

try:
    AnalysisOutput.model_validate(invalid_data)
except ValidationError as exc:
    print(f"\n✗ Validation failed (expected):")
    print(exc.errors()[0])

# Test 3: Confidence out of range
invalid_data = valid_data.copy()
invalid_data["confidence"] = 1.5

try:
    AnalysisOutput.model_validate(invalid_data)
except ValidationError as exc:
    print(f"\n✗ Validation failed (expected):")
    print(exc.errors()[0])
```

---

### **Exercise 3: Test event_id Coercion**

```python
from src.schemas import Finding

# Test different event_id types
test_cases = [
    ("String event_id", {"event_id": "4688"}),
    ("Integer event_id", {"event_id": 4688}),
    ("None event_id", {"event_id": None}),
    ("Missing event_id", {}),
]

for name, event_id_data in test_cases:
    finding_data = {
        "title": "Test",
        "description": "Test description",
        "severity": "low",
        "confidence": 0.5,
        "source_file": "test.jsonl",
        "record_index": 0,
        **event_id_data
    }
    
    finding = Finding.model_validate(finding_data)
    print(f"{name}: event_id = {finding.event_id!r} (type: {type(finding.event_id).__name__})")
```

**Expected output:**
```
String event_id: event_id = '4688' (type: str)
Integer event_id: event_id = '4688' (type: str)  ← Coerced!
None event_id: event_id = None (type: NoneType)
Missing event_id: event_id = None (type: NoneType)
```

**The integer was automatically converted to string!**

---

## **🎯 Key Takeaways**

### **Why Two Validation Layers:**
- **Pydantic** = Structure & types (enforces schema)
- **Security** = Content safety (blocks malicious patterns)
- Together = Comprehensive defense

### **Pydantic Features YOU Use:**
- ✅ Type hints (str, int, float, list)
- ✅ Literals (enums for controlled vocabulary)
- ✅ Constraints (ge, le, min_length, max_length)
- ✅ Field validators (event_id coercion)
- ✅ Nested models (Finding, Hypothesis, IOC)
- ✅ Default factories (empty lists)

### **Security Patterns YOU Enforce (Language Policy):**
1. ✅ False Action Claims ("I have blocked...")
2. ✅ Definitive Judgments ("This is malicious...")
3. ✅ Action Execution ("Action taken...")
4. ✅ System Modification ("System modified...")
5. ✅ False Certainty ("Confirmed that...")

### **Fail-Fast Philosophy:**
- Validation errors stop the pipeline immediately
- Don't waste time generating reports from bad data
- Don't persist garbage to database
- Clear error messages for debugging

---

## **💬 Interview Talking Points**

### **"How do you ensure LLM outputs are trustworthy?"**

> "I implement a two-layer validation strategy in Phase 3. First, I validate the structure using Pydantic schemas in `src/schemas.py` - this enforces that required fields are present, severity is one of four valid values (low/medium/high/critical), confidence scores are 0.0-1.0, and all nested objects (findings, hypotheses, IOCs) conform to their schemas. I also have field validators that gracefully handle common LLM mistakes, like converting event_id integers to strings. Second, after the structure is validated, I check the content against 5 prohibited language patterns in `src/security.py` by stringifying the data. This catches false authority claims like 'I have blocked the threat' or 'This is definitely malicious' - the LLM only analyzes logs, it can't take actions or make definitive verdicts. If any pattern matches, I build an error analysis. This two-layer approach ensures both the structure and content are safe before generating reports or storing to the database."

---

### **"Walk me through the event_id field validator"**

> "I noticed during testing that OpenAI's GPT sometimes returns event_id as an integer - 4688 instead of the string '4688' - even though my schema specifies it should be a string. Rather than letting Pydantic raise a validation error and failing the entire analysis, I implemented a field validator with mode='before' that runs preprocessing. It checks if the value is None and preserves that for optional fields, otherwise converts any value to a string using Python's str() function. This is defensive programming - accommodating a common LLM mistake while still enforcing type consistency. The validator is defined as a classmethod decorated with @field_validator('event_id', mode='before'), and it's located in the Finding model since event_id is a finding-level field. This pattern is documented in Pydantic v2's field validator documentation."

---

### **"Why do you need security validation on top of schema validation?"**

> "Pydantic validates structure and types but doesn't understand content semantics. The security validation enforces our language policy - ensuring the LLM doesn't claim authority it doesn't have. The five prohibited patterns prevent the LLM from saying 'I have blocked' (it only analyzes), 'This is malicious' (it provides hypotheses, not verdicts), 'Action taken' (it can't execute), 'System modified' (it has no write access), or 'Confirmed that' (security analysis deals with probabilities). This happens on the raw response text before JSON parsing, so we catch policy violations immediately. Without this layer, the LLM could return structurally valid JSON that misleads analysts into thinking automated remediation occurred or that findings are definitive when they're just hypotheses. The security layer enforces our threat model: the LLM is an analysis tool that supports human decision-making, not an autonomous agent."

---

### **"How would you extend the validation system?"**

> "There are several extension points. For Pydantic, I could add more field validators - for example, validating that IP addresses in IOCs match IPv4/IPv6 regex patterns, or that file hashes are valid lengths for their hash type (MD5=32 chars, SHA256=64 chars). I could add cross-field validators using @model_validator to check relationships - like ensuring high severity findings have confidence above 0.7, or that findings reference valid source files. For security validation, I'd add more patterns based on threat modeling - checking for base64 or hex-encoded payloads that might hide obfuscated commands, or patterns for sensitive data like API keys or credentials that shouldn't appear in output. I'd also implement allowlisting - certain patterns might be legitimate in security context with proper escaping. Finally, I'd add telemetry - tracking validation failure rates, which patterns trigger most often, and using that data to improve the LLM's system prompt to reduce failures."

---

## **🔗 Connections to Other Phases**

**Where does Phase 3 fit?**

```
Phase 2: src/llm_analyze.py returns unvalidated dict
    ↓
Phase 3A: src/schemas.py validates structure (Pydantic) ← YOU ARE HERE
    ↓
Phase 3B: src/security.py validates language policy ← YOU ARE HERE
    ↓
Phase 4: src/report.py generates markdown report
    ↓
Phase 5: src/storage.py persists to SQLite
```

**What does Phase 4 receive?**
```python
# Phase 3A: Pydantic validation (happens first)
analysis = _validate_analysis_output(analysis_data)

# Phase 3B: Security validation (happens second, on stringified JSON)
policy_valid, policy_error = validate_output(json.dumps(analysis_data))
if not policy_valid:
    # Build error analysis
    analysis = _build_error_analysis("validation_error", policy_error)

# Phase 4: Report generation
report_text = generate_report(analysis)  
# analysis is now a Pydantic model with guaranteed structure and safe content!
```

---

## **📝 Quick Reference**

### **Files:**
- [src/schemas.py](../src/schemas.py) - Pydantic models
- [src/security.py](../src/security.py) - Security patterns

### **Main Models:**
- `AnalysisOutput` - Top-level model (lines 10-34)
- `Finding` - Security finding (lines 37-68)
- `Hypothesis` - Investigative hypothesis (lines 71-83)
- `IndicatorOfCompromise` - IOC (lines 86-97)

### **Key Pydantic Features:**
- `Literal[...]` - Enum validation
- `Field(ge=0.0, le=1.0)` - Numeric constraints
- `Field(min_length=1, max_length=200)` - String constraints
- `@field_validator` - Custom preprocessing
- `default_factory=list` - Empty list default

### **Security Patterns (Language Policy):**
1. False Action Claims - `I have (blocked|removed|deleted|remediated)`
2. Definitive Judgments - `This (is|was) (benign|malicious|definitely)`
3. Action Execution - `Action (taken|executed|completed|performed)`
4. System Modification - `System (modified|updated|patched|fixed)`
5. False Certainty - `(Confirmed|Certain|Guaranteed) that`

---

## **🚀 Next Steps**

You now understand Phase 3! Move on to:
- **Lesson 06**: Phases 4 & 5 Deep Dive (Report Generation & Database Storage)
- **Lesson 07**: Hands-On - Add Custom Security Pattern
- **Lesson 08**: Hands-On - Customize Report Format

You can now confidently explain validation strategies and implement your own validation rules! 🛡️
