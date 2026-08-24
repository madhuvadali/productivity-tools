# One-time git setup

This folder has been scaffolded but is not yet a git repository and has no GitHub remote. Run these steps once, from VS Code's integrated terminal (PowerShell), with this folder open as your workspace.

Delete this file once you're done — it's just setup notes, not part of the tool collection.

## 1. Initialize git locally

```powershell
cd "C:\Users\IITGN\OneDrive - iitgn.ac.in\00 Work\myCode\productivity-tools"
git init
git add .
git commit -m "Initial scaffold: repo structure and template"
```

## 2. Create the GitHub repository

**Option A — GitHub CLI** (if you have `gh` installed and are logged in: check with `gh auth status`):

```powershell
gh repo create productivity-tools --private --source=. --remote=origin --push
```

That single command creates the private repo on GitHub, wires it up as `origin`, and pushes — you're done after this, skip Option B and step 3.

**Option B — GitHub website** (no CLI needed):

1. Go to https://github.com/new
2. Repository name: `productivity-tools`
3. Visibility: **Private**
4. Do NOT initialize with a README, .gitignore, or license (you already have these locally) — leave those unchecked
5. Click "Create repository"
6. Copy the remote URL it shows you (looks like `https://github.com/yourusername/productivity-tools.git`)

## 3. Connect and push (only needed if you used Option B)

```powershell
git branch -M main
git remote add origin https://github.com/yourusername/productivity-tools.git
git push -u origin main
```

(Replace the URL with the one GitHub gave you.)

## Note on OneDrive

This folder lives inside OneDrive, which syncs independently of git. That's generally fine, but avoid having OneDrive and a `git pull`/checkout touch the same files at the exact same moment — if you ever see OneDrive conflict copies (`filename-yourname's PC.ext`), it's OneDrive's sync fighting with a git operation, not a problem with the repo itself. If this bothers you, you can right-click the folder in OneDrive later and choose "Always keep on this device" plus avoid opening it on two OneDrive-synced machines at once while a git operation is mid-flight.

## Going forward

Whenever you finish work on a tool:

```powershell
git add .
git commit -m "describe what changed"
git push
```
