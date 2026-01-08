# Git Branches Explained (For First-Time Users)

**Date:** January 2, 2026  
**Your Question:** "Do we need separate folders for branches?"  
**Short Answer:** **NO! Branches use the SAME folder with different file versions.**

---

## 🎓 How Git Branches Actually Work

### The Magic of Git

Git is like having a **time machine** and **parallel universes** for your code:

```
Your Computer:
├── C:\Projects\Bespin AI Security Analyst Assistant\
│   ├── src\              ← These files CHANGE when you switch branches
│   ├── docs\             ← Same folder, different versions!
│   ├── tests\
│   └── .git\             ← Git's hidden storage (all versions stored here)
```

### What Happens When You Switch Branches

```bash
# You're on enhancement/aws-cloudtrail
git checkout master

# Git instantly swaps files:
# - CONTRIBUTING.md disappears (didn't exist on master)
# - docs/BASELINE_VERIFICATION_2026-01-02.md disappears
# - All other files stay the same (they're identical on both branches)

# Switch back:
git checkout enhancement/aws-cloudtrail

# Git instantly swaps files back:
# - CONTRIBUTING.md reappears
# - docs/BASELINE_VERIFICATION_2026-01-02.md reappears
```

**You stay in the SAME folder. Git just changes which files are visible.**

---

## 👀 How To See Your Current Branch in VS Code

### Method 1: Bottom-Left Status Bar

Look at the **bottom-left corner** of VS Code:

```
🔀 enhancement/aws-cloudtrail    ← Your current branch shows here
```

If you click it, you'll see all available branches and can switch between them.

### Method 2: Source Control Panel

1. Click the **Source Control icon** (left sidebar, looks like a branch)
2. At the top, you'll see: `enhancement/aws-cloudtrail`
3. Click the branch name to switch branches

### Method 3: Command Palette

1. Press `Ctrl+Shift+P` (Windows)
2. Type: "Git: Checkout to..."
3. You'll see all branches listed

---

## 📊 Your Current Branch Status

**Right Now (as of your last commit):**

```
Current Branch: enhancement/aws-cloudtrail
Base Commit: 2b25fc0 (same as master)
Your Changes: 3 new files
  ├── CONTRIBUTING.md
  ├── docs/BASELINE_VERIFICATION_2026-01-02.md
  └── docs/BRANCH_STRATEGY_AWS_CloudTrail.md

Commits Ahead of Master: 1
  └── 597f998 "docs: Phase 0 - baseline verification and branch strategy"
```

---

## 🗂️ Where Are Branch Files Stored?

### Physical Storage

**Everything is in one hidden folder:**

```
C:\Projects\Bespin AI Security Analyst Assistant\.git\
```

This `.git` folder contains:
- All branches
- All commits
- All file versions
- Git's magic database

**You never need to look inside `.git`** - Git manages it automatically.

### What You See vs What Git Stores

**What you see in Windows Explorer:**
```
C:\Projects\Bespin AI Security Analyst Assistant\
├── src\
├── docs\
├── CONTRIBUTING.md          ← Only visible on enhancement/aws-cloudtrail
├── README.md
└── .git\                    ← Hidden folder
```

**What Git stores internally:**
```
.git\objects\  (Git's database)
├── Version A: "master branch files"
├── Version B: "enhancement/aws-cloudtrail files"
└── Version C: "future commits"
```

Git shows you **one version at a time** based on which branch you're on.

---

## ✅ What You Should See in VS Code Right Now

If you're on `enhancement/aws-cloudtrail`, you should see:

### Files Tab (Left Sidebar)
```
BESPIN AI SECURITY ANALYST ASSISTANT
├── .venv\
├── data\
├── docs\
│   ├── ARCHITECTURE.md
│   ├── BASELINE_VERIFICATION_2026-01-02.md          ← NEW (only on this branch)
│   ├── BRANCH_STRATEGY_AWS_CloudTrail.md            ← NEW (only on this branch)
│   ├── PurpleLens_NorthStar_Enhancement_1_AWS_CloudTrail.md
│   └── ...
├── src\
├── tests\
├── CONTRIBUTING.md                                   ← NEW (only on this branch)
├── README.md
└── ...
```

### Source Control Panel
```
SOURCE CONTROL
🔀 enhancement/aws-cloudtrail

Changes (0)  ← Clean (we just committed)

Commits:
├── 597f998 docs: Phase 0 - baseline verification...
└── 2b25fc0 Commit all outstanding changes
```

---

## 🚫 Common Misconceptions (Don't Do This!)

### ❌ WRONG: Create Separate Folders

```
C:\Projects\
├── Bespin AI Security Analyst Assistant\           ← master branch
└── Bespin AI Security Analyst Assistant - AWS\     ← aws branch (WRONG!)
```

**Why this is bad:**
- Wastes disk space (duplicate files)
- Hard to merge changes
- Loses Git's power
- Not how professional teams work

### ✅ RIGHT: Use Git Branches

```
C:\Projects\Bespin AI Security Analyst Assistant\
└── .git\  ← Contains ALL branches

# Switch with commands:
git checkout master                    # Work on master
git checkout enhancement/aws-cloudtrail # Work on AWS feature
```

**Why this is good:**
- Git handles everything
- Easy to merge
- Professional workflow
- Can switch instantly

---

## 🔄 Switching Branches Safely

### Before You Switch

**ALWAYS commit or stash your changes first:**

```bash
# Check for uncommitted changes
git status

# If you have changes:
# Option A: Commit them
git add .
git commit -m "Save work in progress"

# Option B: Stash them (temporary save)
git stash

# NOW you can switch
git checkout master
```

### After Switching

**The files in your folder will change automatically.**

- Files unique to the old branch disappear
- Files unique to the new branch appear
- VS Code refreshes automatically

**Don't panic!** Your files aren't deleted - they're stored in `.git` and will reappear when you switch back.

---

## 🔍 Visual Comparison: Master vs Enhancement Branch

### On Master Branch

```bash
git checkout master
```

**Files you'll see:**
- ❌ CONTRIBUTING.md (doesn't exist yet)
- ❌ docs/BASELINE_VERIFICATION_2026-01-02.md (doesn't exist yet)
- ❌ docs/BRANCH_STRATEGY_AWS_CloudTrail.md (doesn't exist yet)
- ✅ Everything else (src/, tests/, README.md, etc.)

### On Enhancement Branch (Current)

```bash
git checkout enhancement/aws-cloudtrail
```

**Files you'll see:**
- ✅ CONTRIBUTING.md (NEW - we just created it)
- ✅ docs/BASELINE_VERIFICATION_2026-01-02.md (NEW)
- ✅ docs/BRANCH_STRATEGY_AWS_CloudTrail.md (NEW)
- ✅ Everything else (same as master, since we branched from it)

---

## 🎯 Quick Reference Commands

### Check Current Branch
```bash
git branch --show-current
# Output: enhancement/aws-cloudtrail
```

### List All Branches
```bash
git branch -vv
# * enhancement/aws-cloudtrail 597f998 docs: Phase 0 - baseline...
#   master                     2b25fc0 [origin/master] Commit all...
```

### See What's Different From Master
```bash
git diff master --name-only
# Output: 
# CONTRIBUTING.md
# docs/BASELINE_VERIFICATION_2026-01-02.md
# docs/BRANCH_STRATEGY_AWS_CloudTrail.md
```

### Switch Between Branches
```bash
# Go to master (files will change!)
git checkout master

# Go back to enhancement branch
git checkout enhancement/aws-cloudtrail
```

---

## 🧪 Try This Experiment

**See the magic for yourself:**

1. **Check you're on the enhancement branch:**
   ```bash
   git branch --show-current
   ```

2. **Open CONTRIBUTING.md in VS Code** (it exists now)

3. **Switch to master:**
   ```bash
   git checkout master
   ```

4. **Watch VS Code:**
   - CONTRIBUTING.md disappears (file closes or shows error)
   - Other files stay the same

5. **Switch back:**
   ```bash
   git checkout enhancement/aws-cloudtrail
   ```

6. **Watch VS Code:**
   - CONTRIBUTING.md reappears!
   - Magic! ✨

---

## 📚 Key Takeaways

1. **Branches are NOT folders** - they're different versions of the same files
2. **Git stores everything in `.git`** - you stay in one project folder
3. **VS Code shows your current branch** - bottom-left corner
4. **When you switch branches, files change** - Git swaps them automatically
5. **This is professional workflow** - separates features while keeping them connected

---

## ❓ Still Confused?

Try thinking of it like **Microsoft Word's "Track Changes"**:

- **Master branch** = The "final" version
- **Enhancement branch** = The "draft" version with your edits
- **Git** = The magic that lets you switch between versions instantly

You don't need two Word documents in separate folders - Word lets you toggle between views. Git does the same thing, but for entire projects!

---

**Next Step:** Start Phase 0B development on your current branch (`enhancement/aws-cloudtrail`). All new files you create will belong to this branch until you merge it back to master.
