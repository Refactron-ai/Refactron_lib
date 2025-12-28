# 🤝 Contributing to Refactron

Thank you for your interest in contributing to Refactron! We welcome contributions from the community.

## 📋 Table of Contents

- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [How to Contribute](#how-to-contribute)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Adding New Components](#adding-new-components)
- [Debugging & Troubleshooting](#debugging--troubleshooting)
- [Getting Help](#getting-help)

---

## 🚀 Quick Start (5 Minutes)

### 1. Fork and Clone
```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Refactron_lib.git
cd Refactron_lib
```

### 2. Set Up Environment (Automated)

**Quick way (recommended):**

```bash
# On macOS/Linux:
bash setup_dev.sh

# On Windows:
setup_dev.bat
```

This script will:
- Create a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Verify the installation
- Run tests to ensure everything works

**Manual way (if you prefer):**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify installation
pytest
refactron --version
```

**You're ready to contribute!** See [Making Your First Contribution](#making-your-first-contribution) below.

---

## 💻 Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- A code editor (VS Code, PyCharm, etc.)

### Detailed Setup Steps

#### 1. Fork and Clone Repository

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/Refactron_lib.git
cd Refactron_lib
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

#### 3. Install in Development Mode

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 4. Verify Installation

```bash
# Check CLI is available
refactron --version
# Should output: refactron, version 1.0.0

# Run the demo
python3 examples/demo.py

# Run all tests
pytest
```

### Project Structure Reference

```
refactron/
├── core/
│   ├── __init__.py
│   ├── refactron.py       # Main orchestrator
│   ├── config.py          # Configuration
│   ├── models.py          # Data models
│   ├── analysis_result.py # Results
│   └── refactor_result.py
├── analyzers/
│   ├── __init__.py
│   ├── base_analyzer.py   # Inherit from this
│   ├── complexity_analyzer.py
│   └── code_smell_analyzer.py
├── refactorers/
│   ├── __init__.py
│   ├── base_refactorer.py # Inherit from this
│   └── extract_method_refactorer.py
└── cli.py                 # CLI commands
```

---

## 🔄 Development Workflow

### Making Your First Contribution

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
git commit -m "feat: brief description"
git push origin feature/my-improvement

# 4. Create Pull Request on GitHub
```

### Standard Workflow

1. **Make Changes**
   - Edit files in the `refactron/` directory
   - The installation is in "editable" mode, so changes take effect immediately

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Format Code**
   ```bash
   # Format with black
   black refactron tests

   # Sort imports
   isort refactron tests
   ```

4. **Type Check (Optional)**
   ```bash
   mypy refactron
   ```

5. **Lint (Optional)**
   ```bash
   flake8 refactron tests
   ```

### Using the CLI During Development

```bash
# Analyze code
refactron analyze examples/bad_code_example.py

# Analyze with summary only
refactron analyze examples/bad_code_example.py --summary

# Analyze a directory
refactron analyze refactron/

# Generate reports
refactron report examples/bad_code_example.py
refactron report examples/ --format text --output report.txt

# Initialize configuration
refactron init
```

---

## 🎯 How to Contribute

### Types of Contributions

We welcome:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📝 **Documentation improvements**
- 🧪 **Test additions**
- 🎨 **Code refactoring**
- 🌐 **Translations**
- 💡 **Ideas and feedback**

### Great First Contributions

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

### Areas We Need Help

1. **New Analyzers**
   - Security patterns
   - Performance anti-patterns
   - Python best practices

2. **New Refactorers**
   - Auto-fix capabilities
   - More code transformations
   - Smart suggestions

3. **IDE Integration**
   - VS Code extension
   - PyCharm plugin
   - Vim/Emacs support

4. **Documentation**
   - Tutorials
   - Examples
   - API documentation

5. **Testing**
   - Edge cases
   - Performance tests
   - Integration tests

---

## 📏 Code Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Write **docstrings** for all public APIs
- Keep functions **small and focused**
- Maximum line length: **100 characters**

### Code Quality Tools

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

### Naming Conventions

- Classes: `PascalCase` (e.g., `CodeSmellAnalyzer`)
- Functions: `snake_case` (e.g., `analyze_code`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_COMPLEXITY`)
- Private: `_leading_underscore` (e.g., `_internal_method`)

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=refactron --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or navigate to htmlcov/index.html in your browser

# Run specific test file
pytest tests/test_analyzers.py

# Run specific test
pytest tests/test_analyzers.py::test_complexity_analyzer

# Clear cache and rerun
pytest --cache-clear
```

### Writing Tests

- **Write tests** for all new features
- **Maintain coverage** above 80%
- Use **descriptive test names**
- Test **edge cases**
- Include **error scenarios**

Example:

```python
def test_analyzer_detects_long_function():
    """Test that ComplexityAnalyzer detects long functions."""
    code = """
    def very_long_function():
        # ... 100+ lines of code
    """

    analyzer = ComplexityAnalyzer(config)
    issues = analyzer.analyze(Path("test.py"), code)

    assert len(issues) > 0
    assert any("long" in issue.message.lower() for issue in issues)
```

### Test Coverage Requirements

- **New features:** Must have 80%+ coverage
- **Bug fixes:** Must include regression test
- **Refactoring:** Coverage should not decrease

---

## 🔄 Pull Request Process

### Before Submitting

- [ ] All tests pass locally (`pytest`)
- [ ] Code is formatted (`black refactron tests`)
- [ ] Imports are sorted (`isort refactron tests`)
- [ ] No linting errors (`flake8 refactron`)
- [ ] Added/updated tests for changes
- [ ] Updated documentation if needed
- [ ] Commit messages are clear

### Commit Message Format

Use clear, human-like phrasing explaining what and why, not how. Keep the subject under 50 characters, in imperative mood.

Format:
```
type(scope): short summary
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

Examples:
```
feat(analyzer): add SQL injection detection
fix(cli): handle empty files gracefully
docs(readme): update installation instructions
test(refactorer): add edge cases for magic numbers
```

### PR Description Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

How was this tested?

## Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Submit PR with clear description
2. CI/CD checks must pass
3. At least one maintainer approval needed
4. Address review comments
5. PR will be merged by maintainer

---

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** - Has it been reported?
2. **Try latest version** - Is it already fixed?
3. **Minimal reproduction** - Can you isolate the issue?

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:

1. Run command '...'
2. Analyze file '...'
3. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment:**

- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Refactron version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

### What Makes a Good Bug Report?

- ✅ Clear title
- ✅ Minimal reproduction
- ✅ Expected vs actual behavior
- ✅ Environment details
- ✅ Error messages/stack traces
- ✅ Sample code (if applicable)

---

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
How should it work?

**Describe alternatives you've considered**
Other approaches?

**Use cases**
When would this be useful?

**Additional context**
Screenshots, examples, etc.
```

### What Makes a Good Feature Request?

- ✅ Clear use case
- ✅ Specific behavior description
- ✅ Examples of usage
- ✅ Consideration of alternatives
- ✅ Willingness to contribute

---

## 📦 Adding New Components

### Adding a New Analyzer

#### 1. Create the Analyzer File

```bash
touch refactron/analyzers/my_analyzer.py
```

#### 2. Implement the Analyzer

```python
# refactron/analyzers/my_analyzer.py

from pathlib import Path
from typing import List
import ast

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueLevel, IssueCategory


class MyAnalyzer(BaseAnalyzer):
    """Analyzer for detecting X pattern."""

    @property
    def name(self) -> str:
        return "my_analyzer"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for X pattern.

        Args:
            file_path: Path to the file being analyzed
            source_code: Source code to analyze

        Returns:
            List of issues found
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Your analysis logic here
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Example: detect functions with specific patterns
                    if len(node.name) < 3:
                        issue = CodeIssue(
                            category=IssueCategory.CODE_SMELL,
                            level=IssueLevel.INFO,
                            message=f"Function name '{node.name}' is too short",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="Use descriptive function names (3+ characters)",
                            rule_id="MY001",
                        )
                        issues.append(issue)

        except SyntaxError:
            pass

        return issues
```

#### 3. Register the Analyzer

Edit `refactron/core/refactron.py`:

```python
from refactron.analyzers.my_analyzer import MyAnalyzer

def _initialize_analyzers(self) -> None:
    """Initialize all enabled analyzers."""
    self.analyzers = []

    # ... existing analyzers ...

    if "my_analyzer" in self.config.enabled_analyzers:
        self.analyzers.append(MyAnalyzer(self.config))
```

#### 4. Add to Default Config

Edit `refactron/core/config.py`:

```python
enabled_analyzers: List[str] = field(default_factory=lambda: [
    "complexity",
    "code_smells",
    "security",
    "my_analyzer",  # Add your analyzer
])
```

#### 5. Write Tests

```python
# tests/test_my_analyzer.py

from refactron.analyzers.my_analyzer import MyAnalyzer
from refactron.core.config import RefactronConfig
from pathlib import Path


def test_my_analyzer():
    """Test MyAnalyzer detects X pattern."""
    config = RefactronConfig()
    analyzer = MyAnalyzer(config)

    code = """
    def f():
        pass
    """

    issues = analyzer.analyze(Path("test.py"), code)
    assert len(issues) > 0
    assert issues[0].message.startswith("Function name")
```

#### 6. Run Your Tests

```bash
pytest tests/test_my_analyzer.py -v
```

### Adding a New Refactorer

Similar process to adding an analyzer:

1. Create file in `refactron/refactorers/`
2. Inherit from `BaseRefactorer`
3. Implement `refactor()` method
4. Register in `refactron.py`
5. Add to config
6. Write tests

Template:

```python
from pathlib import Path
from refactron.refactorers.base_refactorer import BaseRefactorer
from refactron.core.models import RefactoringOperation

class MyRefactorer(BaseRefactorer):
    """Refactorer for applying X transformation."""

    @property
    def operation_type(self) -> str:
        return "my_refactoring"

    def refactor(self, file_path: Path, code: str) -> list[RefactoringOperation]:
        """
        Suggest X refactoring.

        Args:
            file_path: Path to the file
            code: Source code

        Returns:
            List of refactoring operations
        """
        operations = []

        try:
            tree = ast.parse(code)
            # Your refactoring logic here
        except SyntaxError:
            return operations

        return operations
```

---

## 🐛 Debugging & Troubleshooting

### Common Issues

#### Import Errors

**Solution:** Make sure you installed in editable mode:
```bash
pip install -e .
```

#### Test Failures

**Solution:** Check you have all dependencies:
```bash
pip install -r requirements-dev.txt
```

#### CLI Not Found

**Solution:** Reinstall package:
```bash
pip uninstall refactron
pip install -e .
```

#### Pre-commit Hook Failures

**Solution:** Run pre-commit on all files:
```bash
pre-commit run --all-files
```

### Debugging Tips

#### 1. Use Python Debugger

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

#### 2. Print Debug Info

```python
print(f"DEBUG: {variable}")
```

#### 3. Run Single Test

```bash
pytest tests/test_refactron.py::test_analyze_simple_file -v
```

#### 4. Inspect AST

```python
import ast
code = "def foo(): pass"
tree = ast.parse(code)
print(ast.dump(tree, indent=2))
```

### Quick Commands Cheat Sheet

```bash
# Run demo
python3 examples/demo.py

# Run tests
pytest

# Analyze code
refactron analyze <path>

# Generate report
refactron report <path>

# Format code
black refactron tests

# Sort imports
isort refactron tests

# Type check
mypy refactron

# Install package
pip install -e .

# Run specific test
pytest tests/test_refactron.py -v
```

---

## 📞 Getting Help

- 💬 **Discussions:** GitHub Discussions
- 🐛 **Issues:** GitHub Issues
- 📖 **Documentation:** [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- 📚 **Examples:** See [examples/](examples/) for code examples

---

## 📜 Code of Conduct

Please note we have a [Code of Conduct](CODE_OF_CONDUCT.md). Please follow it in all your interactions with the project.

---

## 🙏 Recognition

Contributors will be:

- Listed in release notes
- Mentioned in CHANGELOG.md
- Credited in documentation (for significant contributions)

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Refactron! Together we can make Python code better for everyone.** 🚀
