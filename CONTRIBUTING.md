# 🤝 Contributing to Refactron

Thank you for your interest in contributing to Refactron! We welcome contributions from the community.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up your development environment** (see below)
4. **Create a branch** for your changes
5. **Make your changes** with tests
6. **Submit a pull request**

See [GETTING_STARTED_DEV.md](GETTING_STARTED_DEV.md) for detailed setup instructions.

---

## 💻 Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or poetry
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/refactron.git
cd Refactron_lib

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests to verify
pytest tests/
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

### Code Quality

```bash
# Format code (if using black)
black refactron/

# Run linter
flake8 refactron/

# Type checking (if using mypy)
mypy refactron/
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
pytest tests/

# Run with coverage
pytest tests/ --cov=refactron --cov-report=html

# Run specific test file
pytest tests/test_analyzers.py

# Run specific test
pytest tests/test_analyzers.py::test_complexity_analyzer
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

1. ✅ All tests pass locally
2. ✅ Code follows style guidelines
3. ✅ New tests added (if applicable)
4. ✅ Documentation updated
5. ✅ Commit messages are clear

### Commit Message Format

Use conventional commits:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

**Examples:**

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
- Refactron version: [e.g., 0.1.0]

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

## 📦 Adding New Analyzers

### Analyzer Template

```python
from pathlib import Path
from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueLevel, IssueCategory

class MyAnalyzer(BaseAnalyzer):
    """Analyzer for detecting X pattern."""

    @property
    def name(self) -> str:
        return "my_analyzer"

    def analyze(self, file_path: Path, code: str) -> list[CodeIssue]:
        """
        Analyze code for X pattern.

        Args:
            file_path: Path to the file being analyzed
            code: Source code to analyze

        Returns:
            List of issues found
        """
        issues = []

        try:
            tree = ast.parse(code)
            # Your analysis logic here
        except SyntaxError:
            return issues

        return issues
```

### Testing Your Analyzer

```python
def test_my_analyzer():
    """Test MyAnalyzer detects X pattern."""
    config = RefactronConfig()
    analyzer = MyAnalyzer(config)

    code = """
    # Code that should trigger the analyzer
    """

    issues = analyzer.analyze(Path("test.py"), code)
    assert len(issues) > 0
```

---

## 🔧 Adding New Refactorers

### Refactorer Template

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

## 📞 Getting Help

- 💬 **Discussions:** GitHub Discussions (coming soon)
- 🐛 **Issues:** GitHub Issues
- 📧 **Email:** maintainers@refactron.dev (if set up)
- 📝 **Documentation:** See [GETTING_STARTED_DEV.md](GETTING_STARTED_DEV.md)

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
