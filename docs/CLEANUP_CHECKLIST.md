# CLEANUP CHECKLIST - Fix Your VS Code Windows

**Problem:** Two VS Code windows open, only one has the folder loaded  
**Solution:** Close the extra window, work from the main project window

---

## ✅ Step-by-Step Fix (Do This Now)

### 1. Close The "Files Only" Window
- [ ] Close the VS Code window where you only see individual markdown files
- [ ] (The one you started this conversation in)

### 2. Switch to Your Main Project Window
- [ ] Open/switch to the VS Code window that has the folder tree on the left
- [ ] Should show: `BESPIN AI SECURITY ANALYST ASSISTANT` at the top of file explorer

### 3. Verify Branch Status

**Look at the bottom-left corner:**
- [ ] Should say: `🔀 enhancement/aws-cloudtrail`
- [ ] If it says `master` or something else, run: `git checkout enhancement/aws-cloudtrail`

### 4. Check For Uncommitted Changes

**In the terminal, run:**
```bash
git status
```

**Expected output:**
```
On branch enhancement/aws-cloudtrail
nothing to commit, working tree clean
```

**If you see uncommitted changes** (files from your original work):
```bash
# Option A: Commit them to the enhancement branch
git add .
git commit -m "WIP: Save current progress"

# Option B: Stash them temporarily
git stash

# Option C: See what changed and decide
git diff
```

### 5. Verify You Have All The New Files

**In the file explorer, check these exist:**
- [ ] `CONTRIBUTING.md` (root folder)
- [ ] `docs/BASELINE_VERIFICATION_2026-01-02.md`
- [ ] `docs/BRANCH_STRATEGY_AWS_CloudTrail.md`
- [ ] `docs/GIT_BRANCHES_EXPLAINED.md`
- [ ] `docs/VSCODE_BRANCH_GUIDE.md`

**If you can't see them:**
```bash
# Make sure you're on the right branch
git checkout enhancement/aws-cloudtrail

# Refresh VS Code (File → Reload Window)
```

---

## 🎯 After Cleanup - You're Ready To Continue

### Current Status

**Branch:** `enhancement/aws-cloudtrail`  
**Last Commit:** "docs: Add Git branches and VS Code guides for developer learning"  
**Status:** Clean working tree (all Overseer documentation committed)

### Next Phase: Phase 0B

**Per the NorthStar, your next tasks are:**

1. Create `src/ingest_aws.py` (adapter stub)
2. Add `data/aws_cloudtrail_sample/` directory
3. Update CLI to accept `--source aws|windows`
4. Verify Windows EVTX workflow still works

**All work happens in your main project window on the `enhancement/aws-cloudtrail` branch.**

---

## 🚨 Quick Reference

### "Which window should I use?"
**The one with the folder open** - should show full file tree on the left

### "How do I know I'm on the right branch?"
**Bottom-left corner** shows: `enhancement/aws-cloudtrail`

### "What if I see changes I didn't make?"
**Run `git status`** to see what changed, then commit or stash them

### "Can I delete the other window?"
**Yes!** Close any VS Code window that doesn't have the folder loaded

---

## ✅ Success Criteria

You're ready when:
- [ ] One VS Code window open (with full folder)
- [ ] Bottom-left shows `enhancement/aws-cloudtrail`
- [ ] All 5 new documentation files visible
- [ ] `git status` shows clean working tree
- [ ] Terminal shows current directory: `C:\Projects\Bespin AI Security Analyst Assistant`

**Once all checked, you're set to continue Phase 0B development!**

---

**Having issues? Run this diagnostic:**
```bash
cd "C:\Projects\Bespin AI Security Analyst Assistant"
Write-Host "Branch:" (git branch --show-current)
Write-Host "Status:" (git status --short)
Write-Host "Window:" $pwd
```

Should output:
```
Branch: enhancement/aws-cloudtrail
Status: (empty - clean tree)
Window: C:\Projects\Bespin AI Security Analyst Assistant
```
