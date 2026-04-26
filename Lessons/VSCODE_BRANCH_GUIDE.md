# VS Code Quick Guide - Finding Your Branch

## 🔍 Where To Look In VS Code

### 1. Bottom-Left Corner (Easiest Way)

Look at the **very bottom-left** of your VS Code window:

```
🔀 enhancement/aws-cloudtrail    0↓ 0↑    ⓘ 0  ⚠ 0
    ↑
    This shows your current branch
```

**What you should see right now:**
- `enhancement/aws-cloudtrail` ← Your branch name

**If you click it:**
- A menu pops up showing all branches
- You can switch branches by clicking a different one

---

### 2. Source Control Panel (Left Sidebar)

**How to open:**
- Click the branch icon (3rd icon from top, left sidebar)
- OR press `Ctrl+Shift+G`

**What you'll see:**
```
SOURCE CONTROL

enhancement/aws-cloudtrail    ← Branch name at top
                               ↓

Source Control Repositories
├── Bespin AI Security Analyst Assistant
    └── 0 changes

Commits
├── docs: Phase 0 - baseline verification and branch strategy
└── Commit all outstanding changes
```

---

### 3. Files You Should See

**In your Explorer panel (1st icon, left sidebar):**

Expand the project tree - you should see:

```
BESPIN AI SECURITY ANALYST ASSISTANT
├── 📁 data
├── 📁 docs
│   ├── 📄 ARCHITECTURE.md
│   ├── 📄 BASELINE_VERIFICATION_2026-01-02.md     ← NEW FILE
│   ├── 📄 BRANCH_STRATEGY_AWS_CloudTrail.md       ← NEW FILE
│   ├── 📄 GIT_BRANCHES_EXPLAINED.md               ← NEW FILE
│   └── 📄 ThreatPrism_NorthStar_Enhancement_1_AWS_CloudTrail.md
├── 📁 src
├── 📁 tests
├── 📄 CONTRIBUTING.md                              ← NEW FILE
├── 📄 README.md
└── ...
```

**The files marked "NEW FILE" only exist on your enhancement branch.**

---

## 🎨 Visual Reference

```
┌─────────────────────────────────────────────────────────────┐
│ File  Edit  Selection  View  Go  Run  Terminal  Help       │ ← Menu Bar
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📁  🔍  ⎇  ▶  🧩    │  docs/GIT_BRANCHES_EXPLAINED.md     │
│   ↑                  │                                      │
│   Explorer           │  # Git Branches Explained           │
│   Search             │  ...content...                      │
│   Source Control ← Here                                    │
│   Run & Debug        │                                      │
│   Extensions         │                                      │
│                      │                                      │
├──────────────────────┴──────────────────────────────────────┤
│ Problems  Output  Terminal  Debug Console                  │ ← Bottom Panel
├─────────────────────────────────────────────────────────────┤
│ 🔀 enhancement/aws-cloudtrail    Ln 1, Col 1      UTF-8    │ ← BRANCH HERE!
└─────────────────────────────────────────────────────────────┘
     ↑
     Bottom-Left Status Bar - Your current branch shows here
```

---

## ✅ Verification Checklist

**Check these 3 things right now:**

### 1. Bottom-Left Branch Name
- [ ] I can see `enhancement/aws-cloudtrail` in the bottom-left corner

### 2. New Files Visible
- [ ] I can see `CONTRIBUTING.md` in the root folder
- [ ] I can see `docs/BASELINE_VERIFICATION_2026-01-02.md`
- [ ] I can see `docs/BRANCH_STRATEGY_AWS_CloudTrail.md`
- [ ] I can see `docs/GIT_BRANCHES_EXPLAINED.md`

### 3. Source Control Panel
- [ ] Source Control panel shows "0 changes" (clean)
- [ ] Last commit shows "docs: Phase 0 - baseline verification..."

**If all 3 are checked, you're all set!**

---

## 🚨 Troubleshooting

### "I don't see the branch name in bottom-left"

**Fix:**
1. Make sure you opened the **folder**, not just a file
2. Go to: File → Open Folder → Select `C:\Projects\Bespin AI Security Analyst Assistant`
3. VS Code will reload and show the branch name

### "I don't see the new files"

**Check which branch you're on:**
1. Open Terminal in VS Code (`Ctrl+` backtick)
2. Run: `git branch --show-current`
3. Should output: `enhancement/aws-cloudtrail`

**If it says `master`:**
```bash
git checkout enhancement/aws-cloudtrail
```

VS Code will refresh and the files will appear!

### "Source Control shows many changes"

**This means you have uncommitted files.**

**Fix:**
1. Check what changed: `git status`
2. If files are from work you did: commit them
3. If files are accidental: discard or stash them

---

## 🎯 Bottom Line

**Answer to your original questions:**

### Q: "Do we need branch files present in VS Code?"
**A:** They ARE present! You're looking at them right now. Git branches don't require separate folders - everything is in `C:\Projects\Bespin AI Security Analyst Assistant`.

### Q: "Where are branch files stored locally?"
**A:** In the hidden `.git` folder inside your project. Git manages this automatically.

### Q: "Should we create a separate folder so things don't get mixed up?"
**A:** No! That's the beauty of Git - it keeps branches separated **virtually** (in its database) while using the **same physical folder**. When you switch branches, Git swaps the files for you.

---

## 🔬 Try This Right Now

**See it work for yourself:**

1. **Open** `CONTRIBUTING.md` in VS Code (it should be in your file tree)
2. **Run** in terminal: `git checkout master`
3. **Watch** VS Code close or grey out CONTRIBUTING.md (it doesn't exist on master)
4. **Run** in terminal: `git checkout enhancement/aws-cloudtrail`
5. **Watch** CONTRIBUTING.md become available again!

**This proves branches use the same folder with different file versions.**

---

**You're all set! The files are there, Git is working, and you're ready to continue Phase 0B development.**
