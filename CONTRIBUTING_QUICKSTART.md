# Quick Start Guide for Contributors

Welcome to Refactron! This guide will get you up and running in minutes.

## 🚀 Quick Setup (5 minutes)

### 1. Fork and Clone
```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Refactron_lib.git
cd Refactron_lib
```

### 2. Set Up Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks (Optional but Recommended)
```bash
pip install pre-commit
pre-commit install
```

### 4. Verify Installation
```bash
# Run tests
pytest

# Check code quality
black --check refactron tests
flake8 refactron --max-line-length=100

# Try the CLI
refactron --help
```

## 🎯 Making Your First Contribution

### Simple Workflow
```bash
# 1. Create a branch
git checkout -b feature/my-improvement

# 2. Make changes and test
# Edit files...
pytest
black refactron tests
flake8 refactron

# 3. Commit and push
git add .
git commit -m "Add: brief description"
git push origin feature/my-improvement

# 4. Create Pull Request on GitHub
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=refactron --cov-report=html

# Run specific test file
pytest tests/test_analyzers.py

# Run specific test
pytest tests/test_analyzers.py::test_complexity_analyzer
```

## 📝 Code Style

We use:
- **Black** for formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black refactron tests

# Sort imports
isort refactron tests

# Check linting
flake8 refactron --max-line-length=100

# Type check
mypy refactron
```

## 🐛 Common Issues

### Import Errors
```bash
# Reinstall in development mode
pip install -e .
```

### Test Failures
```bash
# Clear cache and rerun
pytest --cache-clear
```

### Pre-commit Hook Failures
```bash
# Run pre-commit on all files
pre-commit run --all-files
```

## 💡 What to Contribute?

Great first contributions:
- 🐛 Fix typos in documentation
- ✨ Add test cases
- 📚 Improve examples
- 🔧 Fix flake8 warnings
- 🎨 Enhance CLI output
- 📝 Add docstrings

Check issues labeled:
- `good first issue`
- `help wanted`
- `documentation`

## 🤝 Getting Help

- 💬 [GitHub Discussions](https://github.com/Refactron-ai/Refactron_lib/discussions)
- 📖 [Full Contributing Guide](CONTRIBUTING.md)
- 🏗️ [Architecture Guide](ARCHITECTURE.md)
- 📚 [Getting Started (Detailed)](GETTING_STARTED_DEV.md)

## 📋 Checklist Before PR

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black refactron tests`)
- [ ] Imports are sorted (`isort refactron tests`)
- [ ] No linting errors (`flake8 refactron`)
- [ ] Added/updated tests for changes
- [ ] Updated documentation if needed
- [ ] PR description explains the change

## 🎉 That's It!

You're ready to contribute! Pick an issue, make changes, and submit a PR.

**Questions?** Don't hesitate to ask in discussions or issues.

---

**Thank you for contributing to Refactron!** 🚀
