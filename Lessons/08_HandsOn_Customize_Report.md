# 📝 **Lesson 08: Hands-On - Customize Your Report Format**

This is your second **hands-on modification** lesson! You'll add a custom section to your markdown report, modify formatting functions, and understand how to explain report generation design choices in an interview.

**Prerequisites:** Complete Lessons 01-06 (especially Lesson 06 on reporting)

---

## **⚠️ IMPORTANT: Protect Your Code First!**

This lesson **modifies your actual project files**. Let's use Git to practice safely!

### **Step 0: Create a Practice Branch (If You Haven't Already)**

**If you already did Lesson 07**, you're probably still on the `lessons-practice` branch. Check with:

```powershell
git branch  # Shows all branches, * indicates current branch
```

**If you see `* lessons-practice`**, you're good! Skip to the learning goals.

**If you see `* master` or `* main`**, create the practice branch:

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
- ✅ Add custom sections to YOUR report template
- ✅ Modify formatting functions safely
- ✅ Understand report structure design trade-offs
- ✅ Test report generation with different data
- ✅ Explain report customization to interviewers
- ✅ Balance human readability with technical detail

---

## **📚 The Scenario**

You're in an interview and the interviewer says:

> "I see your report has sections for findings, hypotheses, and IOCs. That's great for technical analysts. But what if a non-technical manager needs to understand the report? How would you add an **Executive Summary** section at the top with high-level bullet points?"

**Your goal:** Add an Executive Summary section, implement the formatting, test it, and explain your design choices.

---

## **🔍 Step 1: Understanding Report Consumers**

### **Who Reads Security Reports?**

Your report serves multiple audiences:

1. **SOC Analysts** (technical) - Need detailed findings, evidence, IOCs
2. **Incident Responders** (technical) - Need hypotheses, recommended next steps
3. **Security Managers** (semi-technical) - Need summary statistics, severity distribution
4. **Executive Leadership** (non-technical) - Need business impact, risk level, action items

**Current report structure:**
```markdown
# Security Analysis Report
## Findings (3)
[detailed technical findings...]
## Hypotheses (2)
[investigative theories...]
## Indicators of Compromise (5)
[IOCs with types...]
## Recommended Next Steps
[action items...]
```

**Problem:** Managers have to read the entire report to understand the situation!

---

## **🎨 Step 2: Designing the Executive Summary**

### **What Should It Include?**

Let's add a section at the **top** of the report with:
- **Overall Risk Level** (calculated from finding severities)
- **Key Statistics** (number of findings, hypotheses, IOCs)
- **Critical Issues** (high/critical severity findings only)
- **Top Recommendation** (most important next step)

### **Example Executive Summary**

```markdown
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🔴 **HIGH** (2 critical, 1 high-severity findings)
- **Analysis Scope**: 15 events analyzed across 3 log files
- **Key Findings**: 3 security findings identified
- **Indicators of Compromise**: 5 IOCs detected
- **Immediate Action Required**: Review suspicious PowerShell execution with encoded commands

**Critical Issues:**
- 🔴 **CRITICAL**: Suspicious encoded PowerShell execution detected
- 🔴 **CRITICAL**: Unauthorized remote access attempt

---

## 🔍 Findings (3)
[rest of report...]
```

**Why this works:**
- ✅ Non-technical readers get the "so what?" immediately
- ✅ Risk level uses color coding (🔴🟡🟢) for visual impact
- ✅ Statistics provide context without detail overload
- ✅ Critical issues surface the most important problems

---

## **💻 Step 3: Modifying YOUR Code**

### **Part A: Add Executive Summary Function**

Open [src/report.py](../src/report.py) and add this new function **before** `generate_report()` (around line 10):

```python
def _generate_executive_summary(analysis: AnalysisOutput, event_count: int) -> str:
    """
    Generate an executive summary section for non-technical readers.
    
    Args:
        analysis: The validated analysis output
        event_count: Number of events analyzed
        
    Returns:
        Formatted markdown string for executive summary
    """
    # Calculate risk level based on finding severities
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in analysis.findings:
        severity_counts[finding.severity] += 1
    
    # Determine overall risk level
    if severity_counts["critical"] > 0:
        risk_level = "🔴 **HIGH**"
        risk_detail = f"({severity_counts['critical']} critical, {severity_counts['high']} high-severity findings)"
    elif severity_counts["high"] > 0:
        risk_level = "🟡 **MEDIUM**"
        risk_detail = f"({severity_counts['high']} high, {severity_counts['medium']} medium-severity findings)"
    elif severity_counts["medium"] > 0:
        risk_level = "🟢 **LOW**"
        risk_detail = f"({severity_counts['medium']} medium, {severity_counts['low']} low-severity findings)"
    else:
        risk_level = "🟢 **MINIMAL**"
        risk_detail = "(all findings are low severity)"
    
    # Build the summary
    lines = [
        "## 📊 Executive Summary\n",
        f"- **Risk Level**: {risk_level} {risk_detail}",
        f"- **Analysis Scope**: {event_count} events analyzed",
        f"- **Key Findings**: {len(analysis.findings)} security findings identified",
        f"- **Hypotheses**: {len(analysis.hypotheses)} investigative theories",
        f"- **Indicators of Compromise**: {len(analysis.indicators_of_compromise)} IOCs detected",
    ]
    
    # Add immediate action if we have recommended steps
    if analysis.recommended_next_steps:
        top_recommendation = analysis.recommended_next_steps[0]
        lines.append(f"- **Immediate Action Required**: {top_recommendation}")
    
    # Add critical issues section if any exist
    critical_findings = [f for f in analysis.findings if f.severity in ["critical", "high"]]
    if critical_findings:
        lines.append("\n**Critical Issues:**")
        for finding in critical_findings[:3]:  # Show max 3 critical issues
            emoji = "🔴" if finding.severity == "critical" else "🟠"
            lines.append(f"- {emoji} **{finding.severity.upper()}**: {finding.description}")
    
    lines.append("\n---\n")  # Separator before main report
    
    return "\n".join(lines)
```

**Save the file** (Ctrl+S).

---

### **Part B: Update generate_report() Function**

Now modify the `generate_report()` function to call your new executive summary function.

**Find this code (lines 10-20 in generate_report):**

```python
def generate_report(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """
    Generate a formatted markdown report from analysis output.
    
    Args:
        analysis: The validated analysis output
        event_count: Number of events analyzed (optional, for context)
        
    Returns:
        Formatted markdown report string
    """
    lines = [
        "# Security Analysis Report\n",
```

**Replace with:**

```python
def generate_report(analysis: AnalysisOutput, event_count: int = 0) -> str:
    """
    Generate a formatted markdown report from analysis output.
    
    Args:
        analysis: The validated analysis output
        event_count: Number of events analyzed (optional, for context)
        
    Returns:
        Formatted markdown report string
    """
    lines = [
        "# Security Analysis Report\n",
        _generate_executive_summary(analysis, event_count),  # NEW!
```

**That's it!** Your report now starts with an executive summary.

**Save the file** (Ctrl+S).

---

## **🧪 Step 4: Testing Your New Section**

### **Test 1: Run the Full Pipeline**

```powershell
# Activate virtual environment
.venv\Scripts\Activate

# Run analysis
python -m src.main --input data/evtx_parsed --model gpt-4o-mini --output analysis_report.md
```

**Open the generated report:**

Open [analysis_report.md](../analysis_report.md) and you should see:

```markdown
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🟡 **MEDIUM** (1 high, 2 medium-severity findings)
- **Analysis Scope**: 15 events analyzed
- **Key Findings**: 3 security findings identified
- **Hypotheses**: 2 investigative theories
- **Indicators of Compromise**: 5 IOCs detected
- **Immediate Action Required**: Review authentication logs for failed login attempts

**Critical Issues:**
- 🟠 **HIGH**: Suspicious PowerShell execution with encoded commands

---

## 🔍 Findings (3)
[rest of report...]
```

**🎉 Your executive summary is working!**

---

### **Test 2: Create Test Data with Different Severities**

Let's test the risk level calculation with different severity distributions:

Create `test_report_custom.py`:

```python
"""Test the new executive summary section."""

from src.schemas import AnalysisOutput, Finding
from src.report import generate_report

# Test Case 1: All critical (should be HIGH risk)
print("=" * 60)
print("TEST 1: All Critical Findings")
print("=" * 60)

critical_data = {
    "status": "success",
    "findings": [
        {
            "event_id": "evt_001",
            "description": "Ransomware encryption detected",
            "severity": "critical",
            "evidence": ["File: malware.exe"],
            "tags": ["malware"]
        },
        {
            "event_id": "evt_002",
            "description": "Data exfiltration to external IP",
            "severity": "critical",
            "evidence": ["Network: 1.2.3.4:443"],
            "tags": ["exfiltration"]
        }
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Isolate affected systems immediately"],
    "confidence": 0.95
}

validated = AnalysisOutput.model_validate(critical_data)
report = generate_report(validated, event_count=20)
print(report[:500])  # Print first 500 chars to see summary
print("\n")

# Test Case 2: Mix of severities (should be HIGH risk - has criticals)
print("=" * 60)
print("TEST 2: Mixed Severities")
print("=" * 60)

mixed_data = {
    "status": "success",
    "findings": [
        {
            "event_id": "evt_001",
            "description": "Critical issue",
            "severity": "critical",
            "evidence": ["Evidence 1"],
            "tags": ["tag1"]
        },
        {
            "event_id": "evt_002",
            "description": "High issue",
            "severity": "high",
            "evidence": ["Evidence 2"],
            "tags": ["tag2"]
        },
        {
            "event_id": "evt_003",
            "description": "Medium issue",
            "severity": "medium",
            "evidence": ["Evidence 3"],
            "tags": ["tag3"]
        }
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Investigate critical issue first"],
    "confidence": 0.85
}

validated = AnalysisOutput.model_validate(mixed_data)
report = generate_report(validated, event_count=15)
print(report[:500])
print("\n")

# Test Case 3: Only low severity (should be MINIMAL risk)
print("=" * 60)
print("TEST 3: Only Low Severity")
print("=" * 60)

low_data = {
    "status": "success",
    "findings": [
        {
            "event_id": "evt_001",
            "description": "Informational finding",
            "severity": "low",
            "evidence": ["Log entry"],
            "tags": ["info"]
        }
    ],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["Continue monitoring"],
    "confidence": 0.60
}

validated = AnalysisOutput.model_validate(low_data)
report = generate_report(validated, event_count=5)
print(report[:500])
print("\n")

# Test Case 4: No findings (should be MINIMAL risk)
print("=" * 60)
print("TEST 4: No Findings (Clean)")
print("=" * 60)

clean_data = {
    "status": "success",
    "findings": [],
    "hypotheses": [],
    "indicators_of_compromise": [],
    "recommended_next_steps": ["No action required"],
    "confidence": 0.90
}

validated = AnalysisOutput.model_validate(clean_data)
report = generate_report(validated, event_count=10)
print(report[:500])
print("\n")

print("✅ All tests completed! Check the risk levels above.")
```

---

**Run the test:**

```powershell
python test_report_custom.py
```

**Expected output:**

```
============================================================
TEST 1: All Critical Findings
============================================================
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🔴 **HIGH** (2 critical, 0 high-severity findings)
- **Analysis Scope**: 20 events analyzed
- **Key Findings**: 2 security findings identified
- **Hypotheses**: 0 investigative theories
- **Indicators of Compromise**: 0 IOCs detected
- **Immediate Action Required**: Isolate affected systems immediately

**Critical Issues:**
- 🔴 **CRITICAL**: Ransomware encryption detected
- 🔴 **CRITICAL**: Data exfiltration to external IP

---

============================================================
TEST 2: Mixed Severities
============================================================
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🔴 **HIGH** (1 critical, 1 high-severity findings)
[...]

============================================================
TEST 3: Only Low Severity
============================================================
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🟢 **MINIMAL** (all findings are low severity)
[...]

============================================================
TEST 4: No Findings (Clean)
============================================================
# Security Analysis Report

## 📊 Executive Summary

- **Risk Level**: 🟢 **MINIMAL** (all findings are low severity)
[...]

✅ All tests completed! Check the risk levels above.
```

**Perfect!** Your risk level calculation works across all scenarios.

---

## **📊 Step 5: Understanding Design Choices**

### **Why Add an Executive Summary?**

**Benefit 1: Accessibility**
- Non-technical readers get the story immediately
- No need to parse technical jargon to understand impact

**Benefit 2: Prioritization**
- Risk level tells you how urgent the issue is
- Critical issues section surfaces what needs immediate attention

**Benefit 3: Context**
- Statistics provide scale (3 findings vs 30 findings is very different)
- Event count shows analysis scope

**Benefit 4: Actionability**
- Top recommendation gives immediate next step
- Readers know what to do before reading details

---

### **Design Trade-offs**

| **Choice** | **Pro** | **Con** |
|------------|---------|---------|
| **Show max 3 critical issues** | Keeps summary concise | Might hide issues 4, 5, 6... |
| **Use emoji risk indicators** | Visual, accessible | Some tools don't render emoji |
| **Top recommendation only** | Forces prioritization | Other steps might be important too |
| **Summary at top** | First thing readers see | Technical readers might prefer details first |

**Your decision:** The current design prioritizes **executive accessibility** over **comprehensive detail**. That's appropriate for a summary section!

---

### **Alternative Designs**

**Option 1: Add Confidence Score**
```markdown
- **Analysis Confidence**: 85% (high confidence in findings)
```

**Option 2: Add Timeline**
```markdown
- **Analysis Duration**: 3.2 seconds
- **Report Generated**: 2025-12-18 14:32:15 UTC
```

**Option 3: Add Attack Chain Indicator**
```markdown
- **Potential Attack Chain**: Initial Access → Execution → Persistence
```

**Option 4: Add MITRE ATT&CK Summary**
```markdown
- **MITRE ATT&CK Techniques**: T1059.001 (PowerShell), T1071 (Application Layer Protocol)
```

**Which to choose?** Depends on your audience:
- **Executives** → Keep it simple (current design)
- **Technical managers** → Add confidence, MITRE mapping
- **SOC analysts** → Add timeline, attack chain

---

## **💬 Interview Explanation: How to Present This**

### **The Setup**

Interviewer: *"Walk me through how you'd customize your report for different audiences."*

### **Your Response (Step-by-Step)**

**Step 1: Audience Analysis**
> "First, I'd identify who consumes the report. For my security analysis tool, that's SOC analysts who need technical details, incident responders who need actionable hypotheses, and managers who need risk context. The challenge is serving all three without overwhelming anyone."

**Step 2: Solution Design**
> "I added an Executive Summary section at the top of the report. It includes calculated risk level based on finding severities - using emoji indicators like 🔴 for high risk, 🟡 for medium, and 🟢 for low. It also shows key statistics like event count and finding count, plus the most critical issues and top recommendation."

**Step 3: Implementation**
> "I implemented this as a separate function _generate_executive_summary in src/report.py at line 10. It takes the analysis output and event count, calculates severity distribution using a dictionary to count critical, high, medium, and low findings, then determines the overall risk level. If there are any critical findings, it's automatically HIGH risk. The function returns formatted markdown that I inject at the top of the report."

**Step 4: Risk Calculation Logic**
> "The risk level logic is: if any critical findings exist, risk is HIGH. If any high-severity findings exist (but no critical), risk is MEDIUM. If only medium-severity findings, risk is LOW. If only low-severity or no findings, risk is MINIMAL. This ensures critical issues always escalate the overall risk, which is appropriate for security reporting."

**Step 5: Testing**
> "I tested with four scenarios - all critical findings, mixed severities, only low severity, and no findings - to ensure the risk calculation works correctly across all cases. I also ran the full pipeline to verify the summary integrates properly with the existing report structure."

**Step 6: Trade-offs**
> "I made a design choice to show only the top 3 critical issues in the summary. This keeps it concise for executives who want the high-level story. Technical analysts can still see all findings in the detailed Findings section below. I also chose to use emoji indicators for visual impact, understanding that some email systems or ticketing tools might not render them - but the text labels like 'HIGH' still convey the message."

**Step 7: Future Enhancements**
> "For future versions, I'd consider making this configurable - like a --report-format executive vs --report-format technical flag. I might also add MITRE ATT&CK technique mapping in the summary for technical audiences, or add a confidence score to help readers understand how certain the analysis is."

---

## **🔍 Deep Dive: How the Risk Calculation Works**

Let's trace through an example:

**Input findings:**
```python
[
    Finding(severity="critical", ...),
    Finding(severity="high", ...),
    Finding(severity="medium", ...)
]
```

**Step 1: Count severities**
```python
severity_counts = {"critical": 1, "high": 1, "medium": 1, "low": 0}
```

**Step 2: Check conditions (in priority order)**
```python
if severity_counts["critical"] > 0:  # TRUE! (we have 1)
    risk_level = "🔴 **HIGH**"
    risk_detail = f"({1} critical, {1} high-severity findings)"
```

**Step 3: Build summary line**
```markdown
- **Risk Level**: 🔴 **HIGH** (1 critical, 1 high-severity findings)
```

**Why priority order matters:**
- Critical always wins (even if you have 100 low-severity findings)
- This is correct for security - one critical issue is a crisis!

---

## **🎯 Key Takeaways**

### **You Just Learned:**
- ✅ How to add custom sections to markdown reports
- ✅ How to implement risk level calculation with severity aggregation
- ✅ How to design for multiple audience types
- ✅ How to balance conciseness with comprehensiveness
- ✅ How to use emoji effectively for visual communication
- ✅ How to test report generation with different data scenarios

### **Interview Skills:**
- ✅ Articulate audience-driven design
- ✅ Explain risk calculation algorithms
- ✅ Discuss report formatting trade-offs
- ✅ Demonstrate thoughtful UX considerations
- ✅ Show testing with edge cases

---

## **🚀 Extension Challenges**

Want to practice more? Try these:

### **Challenge 1: Add MITRE ATT&CK Summary**

Extract MITRE techniques from findings (if they have tags like `"T1059.001"`):

```python
def _extract_mitre_techniques(analysis: AnalysisOutput) -> list[str]:
    """Extract unique MITRE ATT&CK technique IDs from findings."""
    techniques = set()
    for finding in analysis.findings:
        for tag in finding.tags:
            if tag.startswith("T"):  # MITRE techniques start with T
                techniques.add(tag)
    return sorted(techniques)
```

Add this to the executive summary:
```markdown
- **MITRE ATT&CK Techniques**: T1059.001, T1071, T1543.003
```

---

### **Challenge 2: Add Confidence Score Indicator**

Show the analysis confidence as a progress bar:

```python
def _format_confidence(confidence: float) -> str:
    """Format confidence as a visual indicator."""
    bars = int(confidence * 10)  # 0.85 -> 8 bars
    filled = "█" * bars
    empty = "░" * (10 - bars)
    percentage = int(confidence * 100)
    return f"{filled}{empty} {percentage}%"
```

Add to summary:
```markdown
- **Analysis Confidence**: ████████░░ 85%
```

---

### **Challenge 3: Add IOC Type Breakdown**

Show what types of IOCs were found:

```python
def _summarize_iocs(iocs: list[IndicatorOfCompromise]) -> str:
    """Summarize IOC types."""
    if not iocs:
        return "None detected"
    
    type_counts = {}
    for ioc in iocs:
        type_counts[ioc.indicator_type] = type_counts.get(ioc.indicator_type, 0) + 1
    
    summary = ", ".join([f"{count} {type}" for type, count in type_counts.items()])
    return summary
```

Add to summary:
```markdown
- **IOC Breakdown**: 3 ip_address, 2 file_hash, 1 domain
```

---

### **Challenge 4: Add Report Generation Metadata**

Add timestamp and version info:

```python
from datetime import datetime

def _add_metadata() -> str:
    """Add report metadata."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"\n*Report generated: {now} | Analysis version: 1.0*\n"
```

Add at the end of the executive summary!

---

## **📝 Quick Reference**

### **What You Modified:**
- **File:** [src/report.py](../src/report.py)
- **Line 10:** Added `_generate_executive_summary()` function (~50 lines)
- **Line ~65:** Modified `generate_report()` to call the new function
- **Change:** Added executive summary with risk level, statistics, critical issues

### **Your New Function:**
```python
def _generate_executive_summary(analysis: AnalysisOutput, event_count: int) -> str:
    """Generate an executive summary section for non-technical readers."""
    # Calculates risk level from severity counts
    # Shows key statistics
    # Highlights critical issues (max 3)
    # Returns formatted markdown
```

### **Risk Level Logic:**
1. **HIGH** (🔴): Any critical findings exist
2. **MEDIUM** (🟡): Any high-severity findings (no critical)
3. **LOW** (🟢): Any medium-severity findings (no high/critical)
4. **MINIMAL** (🟢): Only low-severity or no findings

### **Testing Strategy:**
1. ✓ All critical findings → HIGH risk
2. ✓ Mixed severities → Correct priority escalation
3. ✓ Low severity only → MINIMAL risk
4. ✓ No findings → MINIMAL risk

---

## **🔗 Next Steps**

You've completed your second code modification! Continue with:
- **Lesson 09**: Debugging Bootcamp (troubleshooting all phases)
- **Lesson 10**: Database Deep Dive (advanced SQL queries)
- **Lesson 11**: Interview Q&A Practice (comprehensive question bank)

You can now confidently modify report generation and explain audience-driven design choices in interviews! 📊✨
