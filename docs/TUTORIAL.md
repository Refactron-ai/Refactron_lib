# Refactron Tutorial: Getting Started

This tutorial will walk you through the basics of using Refactron to analyze and refactor Python code.

## Prerequisites

```bash
pip install refactron
```

## Tutorial Structure

1. [Basic Analysis](#basic-analysis)
2. [Understanding Results](#understanding-results)
3. [Previewing Refactorings](#previewing-refactorings)
4. [Applying Changes](#applying-changes)
5. [Configuration](#configuration)
6. [Advanced Usage](#advanced-usage)

---

## Basic Analysis

Let's start with a simple Python file that has some code smells:

**example.py:**
```python
def calculate_total(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                result = a * 100 + b * 50 + c * 25
                if d > 0:
                    result += d * 10
                    if e > 0:
                        result += e * 5
                        if f > 0:
                            result += f * 1
                return result
    return 0
```

### Running Analysis

```python
from refactron import Refactron

# Initialize Refactron
refactron = Refactron()

# Analyze the file
analysis = refactron.analyze("example.py")

# Print the report
print(analysis.report())
```

### Expected Output

```
🔍 Refactron Analysis

     Analysis Summary     
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric         ┃ Value ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Files Analyzed │     1 │
│ Total Issues   │     5 │
│ 🔴 Critical    │     0 │
│ ❌ Errors      │     0 │
│ ⚡ Warnings    │     3 │
│ ℹ️  Info        │     2 │
└────────────────┴───────┘

Issues found:
1. Too many parameters (6) in function 'calculate_total'
2. Deep nesting (6 levels) detected
3. Magic numbers found: 100, 50, 25, 10, 5, 1
```

---

## Understanding Results

The analysis result contains detailed information about issues:

```python
from refactron import Refactron

refactron = Refactron()
analysis = refactron.analyze("example.py")

# Access issues by category
for issue in analysis.issues:
    print(f"📍 {issue.category.value}")
    print(f"   {issue.message}")
    print(f"   Line {issue.line_number}: {issue.level.value}")
    print(f"   💡 Suggestion: {issue.suggestion}")
    print()
```

### Issue Categories

- **SECURITY**: SQL injection, eval/exec, hardcoded secrets
- **CODE_SMELL**: Magic numbers, long functions, deep nesting
- **COMPLEXITY**: High cyclomatic complexity
- **TYPE_HINT**: Missing type annotations
- **DEAD_CODE**: Unused variables, unreachable code
- **DEPENDENCY**: Circular imports, deprecated modules

---

## Previewing Refactorings

Before making changes, preview what Refactron suggests:

```python
from refactron import Refactron

refactron = Refactron()

# Get refactoring suggestions
result = refactron.refactor("example.py", preview=True)

# Show the diff
result.show_diff()

# Access individual operations
for operation in result.operations:
    print(f"Operation: {operation.operation_type}")
    print(f"Risk Score: {operation.risk_score:.2f}")
    print(f"Description: {operation.description}")
    print(f"\nBefore:\n{operation.old_code}")
    print(f"\nAfter:\n{operation.new_code}")
    print(f"\nReasoning: {operation.reasoning}")
    print("-" * 80)
```

---

## Applying Changes

When you're satisfied with the suggestions, apply them:

```python
from refactron import Refactron

refactron = Refactron()

# Apply refactorings with backup
result = refactron.refactor("example.py", preview=False)

if result.success:
    print("✅ Refactoring applied successfully!")
    print(f"Backup created at: {result.backup_path}")
else:
    print("❌ Refactoring failed")
    for error in result.errors:
        print(f"  - {error}")
```

### Rollback if Needed

```python
from refactron.autofix.file_ops import FileOperations

file_ops = FileOperations()

# Rollback a specific file
file_ops.rollback_file("example.py")

# Or rollback all changes
file_ops.rollback_all()
```

---

## Configuration

Customize Refactron's behavior with a configuration file:

**.refactron.yaml:**
```yaml
enabled_analyzers:
  - complexity
  - code_smell
  - security
  - type_hint
  - dead_code
  - dependency

enabled_refactorers:
  - extract_constant
  - add_docstring
  - simplify_conditionals
  - reduce_parameters

max_function_complexity: 10
max_function_length: 50
max_parameters: 5
```

### Using Configuration

```python
from refactron import Refactron
from refactron.core.config import RefactronConfig

# Load from file
config = RefactronConfig.from_file(".refactron.yaml")

# Or create programmatically
config = RefactronConfig(
    max_function_complexity=10,
    max_parameters=5,
    enabled_analyzers=["complexity", "code_smell"]
)

refactron = Refactron(config)
analysis = refactron.analyze("example.py")
```

---

## Advanced Usage

### Analyze Multiple Files

```python
from pathlib import Path
from refactron import Refactron

refactron = Refactron()

# Analyze a directory
analysis = refactron.analyze("src/")

# Filter by severity
critical_issues = [
    issue for issue in analysis.issues 
    if issue.level.value == "CRITICAL"
]

# Generate JSON report
import json
report_data = {
    "files_analyzed": analysis.summary["files_analyzed"],
    "total_issues": analysis.summary["total_issues"],
    "issues": [
        {
            "file": str(issue.file_path),
            "line": issue.line_number,
            "category": issue.category.value,
            "level": issue.level.value,
            "message": issue.message,
        }
        for issue in analysis.issues
    ]
}

with open("report.json", "w") as f:
    json.dump(report_data, f, indent=2)
```

### Filter Refactoring Types

```python
from refactron import Refactron

refactron = Refactron()

# Only apply specific refactoring types
result = refactron.refactor(
    "example.py",
    preview=True,
    types=["extract_constant", "add_docstring"]
)
```

### Working with the CLI

```bash
# Initialize configuration
refactron init

# Analyze with detailed output
refactron analyze src/ --detailed

# Preview refactorings
refactron refactor example.py --preview

# Apply specific types
refactron refactor example.py -t extract_constant -t add_docstring

# Generate JSON report
refactron report src/ --format json -o report.json
```

---

## Best Practices

1. **Always Preview First**: Review changes before applying
2. **Check Risk Scores**: Higher scores need more careful review
3. **Use Version Control**: Commit before refactoring
4. **Start Small**: Refactor one file at a time initially
5. **Review Diffs**: Understand what changes are being made
6. **Test After**: Run your tests after applying refactorings
7. **Customize Config**: Adjust settings for your project

---

## Common Issues and Solutions

### Issue: Too Many Suggestions

**Solution**: Use configuration to be more selective:
```yaml
max_function_complexity: 15  # More lenient
enabled_refactorers:
  - extract_constant  # Only critical ones
```

### Issue: False Positives

**Solution**: Use ignore comments in code:
```python
def my_function():  # refactron: ignore
    # This function will be skipped
    pass
```

### Issue: Want to Keep Backups

**Solution**: Configure backup retention:
```python
from refactron.autofix.file_ops import FileOperations

file_ops = FileOperations(backup_dir=".refactron_backups")
# Backups will be kept in this directory
```

---

## Next Steps

- Read the [Architecture Guide](../ARCHITECTURE.md)
- Explore [Real-world Examples](../examples/)
- Check out the [API Documentation](../docs/)
- Contribute to [Refactron](../CONTRIBUTING.md)

---

**Happy Refactoring! 🚀**
