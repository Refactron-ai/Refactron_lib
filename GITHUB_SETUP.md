# 🛠️ GitHub Setup Guide

Complete guide to setting up your Refactron GitHub repository with all features enabled.

## 📋 Part 1: Enable Issues and Discussions (Manual Steps)

### Step 1: Navigate to Repository Settings

1. Go to: **https://github.com/Refactron-ai/Refactron_lib**
2. Click on **"Settings"** tab (top right, next to Insights)

### Step 2: Enable Features

In the **Settings** page:

1. Scroll down to the **"Features"** section
2. **Enable Issues**: ✅ Check the "Issues" checkbox
3. **Enable Discussions**: ✅ Check the "Discussions" checkbox
4. Click **"Set up discussions"** if prompted
5. Click **"Save changes"**

✅ **Done!** Issues and Discussions are now enabled!

---

## 🔐 Part 2: Configure GitHub Secrets for CI/CD

### Why We Need Secrets

GitHub Actions workflows need secure access to:
- **PyPI** - To publish packages automatically
- **Codecov** (optional) - To track code coverage

### Step 1: Get Your PyPI API Token

**⚠️ Important**: You shared your token earlier - **REVOKE IT FIRST!**

1. **Revoke old token**:
   - Go to: https://pypi.org/manage/account/token/
   - Find your current token
   - Click **"Remove"**

2. **Create new token**:
   - Go to: https://pypi.org/manage/account/token/
   - Click **"Add API token"**
   - **Token name**: `Refactron GitHub Actions`
   - **Scope**: Select **"Entire account (all projects)"**
   - Click **"Add token"**
   - **COPY THE TOKEN** (starts with `pypi-`) - you won't see it again!

### Step 2: Add PyPI Token to GitHub

1. Go to your repository: https://github.com/Refactron-ai/Refactron_lib
2. Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Add these secrets:

   **Secret 1: PYPI_API_TOKEN**
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: `pypi-YOUR-NEW-TOKEN-HERE` (paste the token you copied)
   - Click **"Add secret"**

   **Secret 2 (Optional): TEST_PYPI_API_TOKEN**
   - If you want to test on TestPyPI first:
   - Go to: https://test.pypi.org/manage/account/token/
   - Create a token there
   - **Name**: `TEST_PYPI_API_TOKEN`
   - **Value**: Your TestPyPI token
   - Click **"Add secret"**

### Step 3: Add Codecov Token (Optional)

For enhanced coverage reporting:

1. Go to: https://codecov.io/ and sign in with GitHub
2. Add your repository: **Refactron-ai/Refactron_lib**
3. Copy the **Upload Token**
4. In GitHub: **Settings** → **Secrets** → **New repository secret**
   - **Name**: `CODECOV_TOKEN`
   - **Value**: Your Codecov token
   - Click **"Add secret"**

✅ **Done!** Secrets are configured!

---

## 🤖 Part 3: What GitHub Actions Will Do

### 1. **CI Workflow** (runs on every push/PR)

**Triggers**: Every push or pull request to `main` or `develop`

**What it does**:
- ✅ Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Lints code with flake8
- ✅ Checks formatting (Black, isort)
- ✅ Runs security scan (Bandit)
- ✅ Builds distribution packages
- ✅ Tests CLI commands
- ✅ Runs real-world tests

**View runs**: https://github.com/Refactron-ai/Refactron_lib/actions

### 2. **Release Workflow** (runs on version tags)

**Triggers**: When you push a version tag like `v0.2.0`

**What it does**:
- 🏗️ Builds distribution packages
- 🧪 Validates package with twine
- 📦 Publishes to PyPI automatically
- 🎉 Creates GitHub Release with files
- 📝 Generates release notes

**How to use**:
```bash
# Bump version in files:
# - pyproject.toml
# - refactron/__init__.py
# - refactron/cli.py

# Commit changes
git add .
git commit -m "Bump version to 0.2.0"
git push

# Create and push tag
git tag v0.2.0
git push origin v0.2.0

# Workflow automatically publishes! 🚀
```

### 3. **Coverage Workflow** (runs on main branch)

**Triggers**: Push or PR to `main`

**What it does**:
- 📊 Generates HTML coverage report
- 🏷️ Creates coverage badge
- 💬 Comments coverage % on PRs
- ☁️ Uploads to Codecov

### 4. **Dependabot** (runs weekly)

**What it does**:
- 🔄 Checks for dependency updates
- 📦 Creates PRs to update packages
- 🤖 Automatically updates GitHub Actions versions

---

## 📊 Part 4: Add Status Badges to README

Add these badges to the top of your `README.md`:

```markdown
# Refactron

[![CI](https://github.com/Refactron-ai/Refactron_lib/workflows/CI/badge.svg)](https://github.com/Refactron-ai/Refactron_lib/actions)
[![PyPI version](https://badge.fury.io/py/refactron.svg)](https://pypi.org/project/refactron/)
[![Python Version](https://img.shields.io/pypi/pyversions/refactron.svg)](https://pypi.org/project/refactron/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/refactron)](https://pepy.tech/project/refactron)
[![GitHub Stars](https://img.shields.io/github/stars/Refactron-ai/Refactron_lib?style=social)](https://github.com/Refactron-ai/Refactron_lib)
```

**Optional Coverage Badge** (if using Codecov):
```markdown
[![Coverage](https://codecov.io/gh/Refactron-ai/Refactron_lib/branch/main/graph/badge.svg)](https://codecov.io/gh/Refactron-ai/Refactron_lib)
```

---

## 🧪 Part 5: Test GitHub Actions

### Trigger the CI Workflow

The CI workflow should start automatically when you push. Check it:

1. Go to: https://github.com/Refactron-ai/Refactron_lib/actions
2. Look for **"CI"** workflow
3. Click on the latest run
4. Watch it execute! ✨

If you don't see it running:
```bash
# Make a small change and push
echo "# Testing CI" >> README.md
git add README.md
git commit -m "Test CI workflow"
git push
```

### Test the Release Workflow

```bash
# Create a test tag
git tag v0.1.0b2
git push origin v0.1.0b2

# Check: https://github.com/Refactron-ai/Refactron_lib/actions
# The Release workflow should start!
```

---

## 📝 Part 6: Configure Branch Protection (Recommended)

Protect your `main` branch from accidental changes:

1. Go to: **Settings** → **Branches**
2. Click **"Add branch protection rule"**
3. **Branch name pattern**: `main`
4. Enable:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ Select: `test`, `code-quality`, `build`
   - ✅ **Require conversation resolution before merging**
5. Click **"Create"**

Now all changes to `main` must go through PR and pass CI! 🛡️

---

## 🎯 Part 7: Community Features

### Issue Templates

Users can now file issues using structured templates:
- 🐛 **Bug Report**: https://github.com/Refactron-ai/Refactron_lib/issues/new?template=bug_report.md
- ✨ **Feature Request**: https://github.com/Refactron-ai/Refactron_lib/issues/new?template=feature_request.md

### Pull Request Template

All PRs will automatically include a checklist and structure.

### Dependabot PRs

Every week, Dependabot will:
- Check for package updates
- Create PRs automatically
- You review and merge

---

## 🚀 Quick Reference

| Action | Command/Link |
|--------|--------------|
| View Workflows | https://github.com/Refactron-ai/Refactron_lib/actions |
| Create Issue | https://github.com/Refactron-ai/Refactron_lib/issues/new/choose |
| View Releases | https://github.com/Refactron-ai/Refactron_lib/releases |
| Settings | https://github.com/Refactron-ai/Refactron_lib/settings |
| Release New Version | `git tag v0.X.X && git push origin v0.X.X` |

---

## ✅ Setup Checklist

- [ ] Enable Issues on GitHub
- [ ] Enable Discussions on GitHub
- [ ] Revoke old PyPI token
- [ ] Create new PyPI token
- [ ] Add `PYPI_API_TOKEN` to GitHub Secrets
- [ ] Add `CODECOV_TOKEN` to GitHub Secrets (optional)
- [ ] Add status badges to README
- [ ] Enable branch protection (recommended)
- [ ] Test CI workflow by pushing
- [ ] Test Release workflow with a tag (optional)
- [ ] Star your own repository ⭐

---

## 🆘 Troubleshooting

### CI Workflow Failing?

1. Check: https://github.com/Refactron-ai/Refactron_lib/actions
2. Click on the failed workflow
3. Expand the failed step to see error
4. Common issues:
   - Missing dependencies: Update `requirements.txt`
   - Test failures: Fix the tests locally first
   - Linting errors: Run `black refactron tests`

### Release Workflow Not Publishing?

1. Verify `PYPI_API_TOKEN` is set in Secrets
2. Check the workflow run for errors
3. Ensure tag format is `v*.*.*` (e.g., `v0.1.0`)
4. Token must have "Entire account" scope

### Coverage Not Uploading?

1. Add `CODECOV_TOKEN` to GitHub Secrets
2. Sign up at https://codecov.io/
3. Add your repository to Codecov

---

**Need Help?** Open an issue: https://github.com/Refactron-ai/Refactron_lib/issues

**Everything working?** Give the repo a star! ⭐

