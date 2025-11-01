# Refactron Quick Reference

## Installation

```bash
pip install refactron
```

## Basic Commands

### CLI

```bash
# Initialize config
refactron init

# Analyze file/directory
refactron analyze <path>
refactron analyze <path> --detailed

# Preview refactoring
refactron refactor <path> --preview

# Apply refactoring
refactron refactor <path>

# Generate report
refactron report <path> --format json -o report.json
```

### Python API

```python
from refactron import Refactron

# Initialize
refactron = Refactron()

# Analyze
analysis = refactron.analyze("file.py")
print(analysis.report())

# Refactor
result = refactron.refactor("file.py", preview=True)
result.show_diff()
```

## Configuration File (.refactron.yaml)

```yaml
# Analyzers to run
enabled_analyzers:
  - complexity
  - code_smell
  - security
  - type_hint
  - dead_code
  - dependency

# Refactorers to use
enabled_refactorers:
  - extract_constant
  - add_docstring
  - simplify_conditionals
  - reduce_parameters

# Thresholds
max_function_complexity: 10
max_function_length: 50
max_parameters: 5
max_nesting_depth: 3
```

## Common Patterns

### Analyze and Generate Report

```python
from refactron import Refactron

refactron = Refactron()
analysis = refactron.analyze("src/")

# Print summary
print(f"Files: {analysis.summary['files_analyzed']}")
print(f"Issues: {analysis.summary['total_issues']}")

# Access issues
for issue in analysis.issues:
    print(f"{issue.level.value}: {issue.message} at line {issue.line_number}")
```

### Filter by Severity

```python
critical = [i for i in analysis.issues if i.level.value == "CRITICAL"]
errors = [i for i in analysis.issues if i.level.value == "ERROR"]
warnings = [i for i in analysis.issues if i.level.value == "WARNING"]
```

### Preview Specific Refactorings

```python
result = refactron.refactor(
    "file.py",
    preview=True,
    types=["extract_constant", "add_docstring"]
)
```

### Apply with Backup

```python
result = refactron.refactor("file.py", preview=False)
if result.success:
    print(f"✅ Success! Backup: {result.backup_path}")
else:
    print(f"❌ Failed: {result.errors}")
```

### Rollback Changes

```python
from refactron.autofix.file_ops import FileOperations

file_ops = FileOperations()
file_ops.rollback_file("file.py")  # Rollback one file
file_ops.rollback_all()            # Rollback all
```

## Issue Categories

| Category   | Examples |
|------------|----------|
| SECURITY   | SQL injection, eval/exec, hardcoded secrets |
| CODE_SMELL | Magic numbers, long functions, deep nesting |
| COMPLEXITY | High cyclomatic complexity |
| TYPE_HINT  | Missing type annotations |
| DEAD_CODE  | Unused variables, unreachable code |
| DEPENDENCY | Circular imports, deprecated modules |

## Risk Scores

| Score | Level    | Description |
|-------|----------|-------------|
| 0.0   | Safe     | Formatting, imports |
| 0.1-0.2 | Low    | Documentation, constants |
| 0.3-0.5 | Moderate | Logic changes, refactoring |
| 0.6-1.0 | High   | Complex transformations |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success, no issues |
| 1    | Issues found |
| 2    | Error during execution |

## Environment Variables

```bash
# Disable color output
export REFACTRON_NO_COLOR=1

# Set log level
export REFACTRON_LOG_LEVEL=DEBUG
```

## Useful Flags

```bash
# Analysis
--detailed          # Show detailed analysis
--summary           # Show summary only
--config FILE       # Use custom config

# Refactoring
--preview           # Preview changes
--type TYPE         # Filter by type (can use multiple)
--no-backup         # Don't create backups
--risk-level LEVEL  # safe|low|moderate|high
```

## Common Issues

### Too Many Issues
**Solution**: Adjust thresholds in config
```yaml
max_function_complexity: 15  # More lenient
```

### Performance Issues
**Solution**: Analyze smaller chunks
```bash
refactron analyze src/module1/
refactron analyze src/module2/
```

### False Positives
**Solution**: Use ignore comments
```python
def my_function():  # refactron: ignore
    pass
```

## Getting Help

```bash
refactron --help
refactron analyze --help
refactron refactor --help
```

## Resources

- 📚 [Full Documentation](https://refactron-ai.github.io/Refactron_lib/)
- 🚀 [Tutorial](TUTORIAL.md)
- 🏗️ [Architecture](../ARCHITECTURE.md)
- 🤝 [Contributing](../CONTRIBUTING.md)
- 🔒 [Security](../SECURITY.md)

---

**Need more help?** Check out our [GitHub Discussions](https://github.com/Refactron-ai/Refactron_lib/discussions)
