# GitHub Configuration

This directory contains GitHub-specific configuration files for Refactron.

## 📁 Directory Structure

```
.github/
├── workflows/           # GitHub Actions CI/CD workflows
│   ├── ci.yml          # Main CI pipeline (tests, linting, builds)
│   ├── release.yml     # Automated releases to PyPI
│   └── coverage.yml    # Code coverage reporting
├── ISSUE_TEMPLATE/     # Issue templates
│   ├── bug_report.md   # Bug report template
│   └── feature_request.md  # Feature request template
├── PULL_REQUEST_TEMPLATE.md  # PR template
└── dependabot.yml      # Dependency update automation
```

## 🤖 GitHub Actions Workflows

### 1. CI Workflow (`ci.yml`)
**Triggers**: Push/PR to `main` or `develop`

**Jobs**:
- **Test**: Runs tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Code Quality**: Checks formatting (Black, isort)
- **Security**: Runs Bandit security scanner
- **Build**: Builds distribution packages
- **Integration Test**: Tests CLI commands and real-world scenarios

**Status Badge**: 
```markdown
[![CI](https://github.com/Refactron-ai/Refactron_lib/workflows/CI/badge.svg)](https://github.com/Refactron-ai/Refactron_lib/actions)
```

### 2. Release Workflow (`release.yml`)
**Triggers**: Push tags matching `v*.*.*` (e.g., v0.1.0, v1.0.0)

**Jobs**:
- Builds distribution packages
- Publishes to Test PyPI (optional)
- Publishes to PyPI
- Creates GitHub Release with artifacts

**How to Use**:
```bash
# Create and push a tag
git tag v0.2.0
git push origin v0.2.0

# Workflow automatically publishes to PyPI
```

**Requirements**:
- Set `PYPI_API_TOKEN` secret in GitHub settings
- Optionally set `TEST_PYPI_API_TOKEN` for test releases

### 3. Coverage Workflow (`coverage.yml`)
**Triggers**: Push/PR to `main`

**Jobs**:
- Generates HTML coverage report
- Creates coverage badge
- Comments coverage % on PRs
- Uploads coverage to Codecov

**Status Badge**:
```markdown
[![Coverage](https://codecov.io/gh/Refactron-ai/Refactron_lib/branch/main/graph/badge.svg)](https://codecov.io/gh/Refactron-ai/Refactron_lib)
```

## 🔧 Dependabot

Automatically creates PRs to update dependencies:
- **Python packages**: Weekly updates
- **GitHub Actions**: Weekly updates

## 📝 Issue Templates

### Bug Report
- Structured bug reporting
- Includes environment details
- Reproduction steps
- Code samples

### Feature Request
- Problem description
- Proposed solution
- Example usage
- Benefits analysis

## 🔀 Pull Request Template

Ensures all PRs include:
- Description of changes
- Type of change
- Related issues
- Testing checklist
- Code quality checklist

## 🔐 Required Secrets

To use all workflows, configure these secrets in GitHub Settings → Secrets:

| Secret Name | Purpose | Required For |
|-------------|---------|--------------|
| `PYPI_API_TOKEN` | PyPI publishing | Release workflow |
| `TEST_PYPI_API_TOKEN` | Test PyPI publishing | Release workflow (optional) |
| `CODECOV_TOKEN` | Upload to Codecov | Coverage workflow (optional) |

## 📊 Adding Status Badges

Add these to your main README.md:

```markdown
[![CI](https://github.com/Refactron-ai/Refactron_lib/workflows/CI/badge.svg)](https://github.com/Refactron-ai/Refactron_lib/actions)
[![Coverage](https://codecov.io/gh/Refactron-ai/Refactron_lib/branch/main/graph/badge.svg)](https://codecov.io/gh/Refactron-ai/Refactron_lib)
[![PyPI version](https://badge.fury.io/py/refactron.svg)](https://pypi.org/project/refactron/)
[![Python Version](https://img.shields.io/pypi/pyversions/refactron.svg)](https://pypi.org/project/refactron/)
```

## 🚀 Workflow Status

You can view all workflow runs at:
https://github.com/Refactron-ai/Refactron_lib/actions

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Issue Templates Guide](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)

