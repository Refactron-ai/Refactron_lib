# 🤖 Refactron

**The Intelligent Code Refactoring Transformer**

Refactron is a powerful Python library designed to eliminate technical debt, modernize legacy code, and automate code refactoring with intelligence and safety.

[![CI](https://github.com/Refactron-ai/Refactron_lib/workflows/CI/badge.svg)](https://github.com/Refactron-ai/Refactron_lib/actions)
[![Tests](https://img.shields.io/badge/tests-135%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
[![PyPI version](https://badge.fury.io/py/refactron.svg)](https://pypi.org/project/refactron/)
[![Python Version](https://img.shields.io/pypi/pyversions/refactron.svg)](https://pypi.org/project/refactron/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![GitHub Stars](https://img.shields.io/github/stars/Refactron-ai/Refactron_lib?style=social)](https://github.com/Refactron-ai/Refactron_lib)
[![Downloads](https://pepy.tech/badge/refactron)](https://pepy.tech/project/refactron)

## ✨ Features

### 🔍 **Comprehensive Analysis**
- **Security Scanning** - Detect `eval()`, `exec()`, SQL injection, shell injection, hardcoded secrets
  - **Context-Aware Analysis** - Lower confidence for test files and examples
  - **Confidence Scores** - Each issue rated 0.0-1.0 for detection certainty
  - **Whitelist/Ignore Rules** - Fine-grained control over security checks
  - **False Positive Tracking** - Learn from and filter known false positives
- **Code Smells** - Find magic numbers, long functions, too many parameters, deep nesting
- **Complexity Metrics** - Cyclomatic complexity, maintainability index
- **Type Hints** - Identify missing or incomplete type annotations
- **Dead Code** - Detect unused functions, variables, and unreachable code
- **Dependencies** - Find circular imports, wildcard imports, deprecated modules

### 🔧 **Intelligent Refactoring**
- **Extract Constants** - Replace magic numbers with named constants
- **Reduce Parameters** - Convert parameter lists into configuration objects
- **Simplify Conditionals** - Transform nested `if` statements into guard clauses
- **Add Docstrings** - Generate contextual documentation automatically
- **Before/After Previews** - See exactly what will change
- **Risk Scoring** - Know how safe each refactoring is (0.0 = perfectly safe, 1.0 = high risk)

### 📊 **Rich Reporting**
- Multiple formats: Text, JSON, HTML
- Detailed issue categorization
- Technical debt quantification
- Export for CI/CD integration

## 🚀 Quick Start

### Installation

```bash
pip install refactron
```

### Basic Usage

```python
from refactron import Refactron

# Initialize Refactron
refactron = Refactron()

# Analyze your code
analysis = refactron.analyze("path/to/your/code.py")
print(analysis.report())

# Apply refactoring
result = refactron.refactor("path/to/your/code.py", preview=True)
result.show_diff()
result.apply()
```

### CLI Usage

```bash
# Initialize configuration
refactron init

# Analyze a file or directory
refactron analyze myproject/ --detailed

# Generate a report
refactron report myproject/ --format json -o report.json

# Preview refactoring suggestions
refactron refactor myfile.py --preview

# Filter specific refactoring types
refactron refactor myfile.py --preview -t extract_constant -t add_docstring
```

**Example Output:**
```
🔍 Refactron Analysis

     Analysis Summary     
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric         ┃ Value ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Files Analyzed │     3 │
│ Total Issues   │    50 │
│ 🔴 Critical    │     3 │
│ ❌ Errors      │     0 │
│ ⚡ Warnings    │     8 │
│ ℹ️  Info        │    39 │
└────────────────┴───────┘

⚠️  Found 3 critical issue(s) that need immediate attention!
```

## 🎯 What Makes Refactron Different?

Unlike traditional linters and formatters, Refactron:

- **Holistic Approach**: Combines analysis, refactoring, and optimization in one tool
- **Context-Aware**: Understands code semantics, not just syntax
- **Safe by Default**: Preview changes, risk scoring, and rollback support
- **Intelligent**: Learn from patterns and suggest contextual improvements
- **Business-Focused**: Quantify technical debt in actionable metrics

## 💡 Real-World Examples

We've included practical examples in the `examples/` directory:

- **`flask_api_example.py`** - Common Flask API issues (security, code smells)
- **`data_science_example.py`** - Data science workflow improvements
- **`cli_tool_example.py`** - CLI application best practices

Try them out:
```bash
# Analyze the Flask example
refactron analyze examples/flask_api_example.py --detailed

# Get refactoring suggestions
refactron refactor examples/flask_api_example.py --preview
```

See `examples/DEMO_USAGE.md` for detailed walkthroughs!

## 📚 Documentation

### 🚀 Getting Started
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command cheatsheet and common patterns
- [Tutorial](docs/TUTORIAL.md) - Step-by-step guide with examples
- [Quick Start (Contributors)](CONTRIBUTING_QUICKSTART.md) - Start contributing in 5 minutes

### 📖 Core Documentation
- [Getting Started (Dev)](GETTING_STARTED_DEV.md) - Development setup
- [Architecture](ARCHITECTURE.md) - Technical design and internals
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Security Policy](SECURITY.md) - Vulnerability reporting
- [False Positive Reduction](docs/FALSE_POSITIVE_REDUCTION.md) - Security analyzer features for reducing false positives

### 📊 Project Information
- [Case Study](CASE_STUDY.md) - Real-world testing results
- [Changelog](CHANGELOG.md) - Version history
- [Benchmarks](benchmarks/README.md) - Performance metrics

## 🛠️ Development Status

> **✅ Stable Release**: Refactron v1.0.0 is production-ready and stable. We welcome feedback and contributions!

**Current Metrics:**
- ✅ **135 tests passing** (100% success rate)
- ✅ **84% code coverage** (2,060 statements)
- ✅ **0 critical issues** in production code
- ✅ Real-world validated on 5,800+ lines
- ✅ **Pre-commit hooks** for code quality
- ✅ **Security scanning** with Bandit

### Roadmap

**Phase 1: Foundation** ✅ **COMPLETE**
- [x] Core architecture & CLI
- [x] Configuration system
- [x] Basic analyzers (complexity, code smells)
- [x] Refactoring suggestions with risk scoring
- [x] Before/after code previews

**Phase 2: Advanced Analysis** ✅ **COMPLETE**
- [x] Security vulnerability scanning
- [x] Dependency analysis
- [x] Dead code detection
- [x] Type hint analysis
- [x] Comprehensive test suite (87 tests, 89% coverage)

**Phase 3: Intelligence & Automation** 🚧 **NEXT**
- [ ] AI-powered pattern recognition
- [ ] Auto-fix capabilities
- [ ] Multi-file refactoring
- [ ] Custom rule engine
- [ ] Performance profiling

**Phase 4: Integration & Scale** 📋 **PLANNED**
- [ ] IDE plugins (VS Code, PyCharm)
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Team collaboration features
- [ ] Historical trend analysis

## 🤝 Contributing

We welcome contributions! Please see:
- [Quick Start Guide](CONTRIBUTING_QUICKSTART.md) - Get started in 5 minutes! 🚀
- [Contributing Guide](CONTRIBUTING.md) - Detailed contribution process
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines
- [Getting Started (Dev)](GETTING_STARTED_DEV.md) - Development setup
- [Security Policy](SECURITY.md) - Report vulnerabilities

### Quick Start for Contributors
```bash
# Fork, clone, and setup
git clone https://github.com/YOUR_USERNAME/Refactron_lib.git
cd Refactron_lib
python3 -m venv venv && source venv/bin/activate
pip install -e . && pip install -r requirements-dev.txt
pip install pre-commit && pre-commit install

# Make changes and test
pytest
black refactron tests
flake8 refactron
```

## 🧪 CI/CD Status

Refactron uses GitHub Actions for continuous integration and deployment:
- ✅ Automated testing on Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Code quality checks (Black, isort, flake8, mypy)
- ✅ Pre-commit hooks enforcement
- ✅ Security scanning with Bandit
- ✅ Automated dependency updates via Dependabot
- ✅ 84% test coverage (2,060 statements)

Check our [Actions page](https://github.com/Refactron-ai/Refactron_lib/actions) for live build status!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.


---

**Star ⭐ this repo if you find it helpful!**

