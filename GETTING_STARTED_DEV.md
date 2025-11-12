# Getting Started with Refactron Development

This guide will help you set up your development environment and start working on Refactron.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- A code editor (VS Code, PyCharm, etc.)

## Initial Setup

### 1. Navigate to Project Directory

```bash
cd /Users/omsherikar/Refactron_Lib
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Verify Installation

```bash
# Check CLI is available
refactron --version

# Should output: refactron, version 1.0.0
```

## Run the Demo

```bash
# Run the demonstration script
python3 examples/demo.py
```

You should see a complete demo of Refactron analyzing code!

## Run Tests

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
```

## Try the CLI

### Analyze Code

```bash
# Analyze the example bad code
refactron analyze examples/bad_code_example.py

# Analyze with summary only
refactron analyze examples/bad_code_example.py --summary

# Analyze a directory
refactron analyze refactron/
```

### Generate Reports

```bash
# Generate text report
refactron report examples/bad_code_example.py

# Generate and save report
refactron report examples/ --format text --output report.txt
```

### Initialize Configuration

```bash
# Create a .refactron.yaml config file
refactron init

# Edit the file to customize settings
```

## Development Workflow

### 1. Make Changes

Edit files in the `refactron/` directory. The installation is in "editable" mode, so changes take effect immediately.

### 2. Run Tests

```bash
pytest tests/
```

### 3. Format Code

```bash
# Format with black
black refactron tests

# Sort imports
isort refactron tests
```

### 4. Type Check (Optional)

```bash
mypy refactron
```

### 5. Lint (Optional)

```bash
flake8 refactron tests
```

## Adding a New Analyzer

### 1. Create the Analyzer File

```bash
touch refactron/analyzers/my_analyzer.py
```

### 2. Implement the Analyzer

```python
# refactron/analyzers/my_analyzer.py

from pathlib import Path
from typing import List
import ast

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueLevel, IssueCategory


class MyAnalyzer(BaseAnalyzer):
    """Describe what your analyzer does."""

    @property
    def name(self) -> str:
        return "my_analyzer"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """Analyze code and return issues."""
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

### 3. Register the Analyzer

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

### 4. Add to Default Config

Edit `refactron/core/config.py`:

```python
enabled_analyzers: List[str] = field(default_factory=lambda: [
    "complexity",
    "code_smells",
    "type_hints",
    "modernization",
    "my_analyzer",  # Add your analyzer
])
```

### 5. Write Tests

```python
# tests/test_my_analyzer.py

from refactron.analyzers.my_analyzer import MyAnalyzer
from refactron.core.config import RefactronConfig
from pathlib import Path


def test_my_analyzer():
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

### 6. Run Your Tests

```bash
pytest tests/test_my_analyzer.py -v
```

## Adding a New Refactorer

Similar process to adding an analyzer:

1. Create file in `refactron/refactorers/`
2. Inherit from `BaseRefactorer`
3. Implement `refactor()` method
4. Register in `refactron.py`
5. Write tests

## Project Structure Reference

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

## Debugging Tips

### 1. Use Python Debugger

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

### 2. Print Debug Info

```python
print(f"DEBUG: {variable}")
```

### 3. Run Single Test

```bash
pytest tests/test_refactron.py::test_analyze_simple_file -v
```

### 4. Inspect AST

```python
import ast
code = "def foo(): pass"
tree = ast.parse(code)
print(ast.dump(tree, indent=2))
```

## Common Issues

### Issue: Import Error

**Solution:** Make sure you installed in editable mode:
```bash
pip install -e .
```

### Issue: Tests Fail

**Solution:** Check you have all dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: CLI Not Found

**Solution:** Reinstall package:
```bash
pip uninstall refactron
pip install -e .
```

## Resources

- **Python AST Documentation**: https://docs.python.org/3/library/ast.html
- **LibCST Documentation**: https://libcst.readthedocs.io/
- **Radon Documentation**: https://radon.readthedocs.io/
- **Click Documentation**: https://click.palletsprojects.com/

## Getting Help

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- See [examples/](examples/) for code examples
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review existing analyzers for patterns

## Quick Commands Cheat Sheet

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

# Type check
mypy refactron

# Install package
pip install -e .

# Run specific test
pytest tests/test_refactron.py -v
```

## Next Steps

1. ✅ Set up your environment
2. ✅ Run the demo
3. ✅ Run all tests
4. 🔨 Try adding a simple analyzer
5. 🔨 Write tests for your analyzer
6. 🔨 Read the architecture docs
7. 🔨 Explore the codebase
8. 🚀 Start building!

---

Happy coding! If you have questions, refer to the documentation or open an issue.
