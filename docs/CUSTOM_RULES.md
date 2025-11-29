# Custom Rule Framework Guide

## Overview

Refactron's Custom Rule Framework allows you to define your own code analysis rules using a simple YAML-based DSL (Domain Specific Language). This enables you to enforce project-specific coding standards, detect custom anti-patterns, and implement organization-wide best practices.

## Quick Start

### 1. Create a Rules File

Create a `.refactron-rules.yaml` file in your project root:

```yaml
version: 1
rules:
  - name: "no-print-in-production"
    description: "Disallow print() statements in production code"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    exclude:
      - "**/test_*.py"
      - "**/tests/**"
    message: "Avoid using print() in production code"
    suggestion: "Use logging instead: logger.info(...)"
```

### 2. Use the Custom Rule Analyzer

```python
from pathlib import Path
from refactron.core.config import RefactronConfig
from refactron.rules import CustomRuleAnalyzer

# Initialize the analyzer
config = RefactronConfig()
analyzer = CustomRuleAnalyzer(config)

# Analyze a file
source_code = Path("myfile.py").read_text()
issues = analyzer.analyze(Path("myfile.py"), source_code)

# Print issues
for issue in issues:
    print(f"{issue.file_path}:{issue.line_number} - {issue.message}")
```

## Rule Definition Reference

### Rule Structure

Each rule consists of the following fields:

```yaml
- name: "rule-identifier"          # Required: Unique rule ID (lowercase, hyphens, underscores)
  description: "Rule description"  # Required: Human-readable description
  severity: "warning"              # Required: info, warning, error, or critical
  pattern:                         # Required: Pattern to match
    type: "pattern_type"           # See pattern types below
    # ... pattern-specific fields
  message: "Issue message"         # Required: Message shown when rule matches
  suggestion: "Fix suggestion"     # Optional: How to fix the issue
  exclude:                         # Optional: File patterns to exclude
    - "**/test_*.py"
  include:                         # Optional: File patterns to include
    - "src/**"
  enabled: true                    # Optional: Enable/disable rule (default: true)
```

### Pattern Types

#### 1. Function Call Pattern

Detects function calls by name.

```yaml
pattern:
  type: "function_call"
  name: "print"  # Function name to match
```

Example matches:
- `print("hello")`
- `result = print(x)`

#### 2. Class Definition Pattern

Detects class definitions.

```yaml
pattern:
  type: "class_def"
  name: "MyClass"  # Optional: specific class name, or omit to match all classes
  constraints:     # Optional
    # Add constraints here
```

Example matches:
- `class MyClass:`
- `class MyClass(BaseClass):`

#### 3. Function Definition Pattern

Detects function definitions with optional constraints.

```yaml
pattern:
  type: "function_def"
  name: "process_data"  # Optional: specific function name
  constraints:
    lines: "> 50"       # Functions longer than 50 lines
    params: "> 5"       # Functions with more than 5 parameters
```

Constraint operators:
- `"> N"` - Greater than N
- `"< N"` - Less than N
- `N` - Exactly N

Example matches:
- `def long_function(a, b, c, d, e, f):`
- `def process_data():`

#### 4. Import Pattern

Detects import statements.

```yaml
pattern:
  type: "import"
  name: "os.system"  # Optional: specific import to match
```

Example matches:
- `import os`
- `from os import system`
- `from package import module`

#### 5. Attribute Access Pattern

Detects attribute access.

```yaml
pattern:
  type: "attribute"
  name: "DEBUG"  # Attribute name to match
```

Example matches:
- `config.DEBUG`
- `self.DEBUG`

#### 6. Regex Pattern

Matches code using regular expressions.

```yaml
pattern:
  type: "regex"
  regex: "except\\s*:"  # Regex pattern
```

Example matches:
- `except:`
- `except :`

**Note:** Remember to escape backslashes in YAML strings!

### Severity Levels

- **`info`**: Informational - suggestions for improvement
- **`warning`**: Potential issues that should be reviewed
- **`error`**: Issues that should be fixed
- **`critical`**: Serious issues requiring immediate attention

### File Patterns

Both `exclude` and `include` support glob patterns:

- `*.py` - All Python files in current directory
- `**/*.py` - All Python files recursively
- `test_*.py` - Files starting with "test_"
- `**/tests/**` - All files in any "tests" directory
- `src/**` - All files under "src" directory

## Rule Templates

Refactron includes pre-built rule templates for common scenarios:

```python
from refactron.rules import get_template, list_templates, generate_example_ruleset

# List all available templates
templates = list_templates()
print(templates)

# Get a specific template
no_eval_rule = get_template("no-eval")

# Generate an example ruleset
example_ruleset = generate_example_ruleset()
```

### Available Templates

1. **`no-print-in-production`** - Disallow print() in production code
2. **`no-eval`** - Disallow eval() due to security risks
3. **`no-exec`** - Disallow exec() due to security risks
4. **`max-function-length`** - Limit function length to 50 lines
5. **`max-function-params`** - Limit function parameters to 5
6. **`no-wildcard-import`** - Disallow `from module import *`
7. **`no-bare-except`** - Disallow bare `except:` clauses
8. **`no-mutable-default`** - Disallow mutable default arguments
9. **`require-docstring`** - Require docstrings for public functions
10. **`no-global-state`** - Avoid global variables
11. **`no-debug-statements`** - Disallow debug statements
12. **`no-hardcoded-credentials`** - Disallow hardcoded passwords/keys
13. **`no-string-concat-in-loop`** - Avoid string concatenation in loops

## Examples

### Example 1: Enforce Logging Instead of Print

```yaml
version: 1
rules:
  - name: "use-logging"
    description: "Use logging instead of print for production code"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    exclude:
      - "**/test_*.py"
      - "**/examples/**"
    message: "Use logging.info() instead of print()"
    suggestion: "import logging; logger.info('message')"
```

### Example 2: Limit Function Complexity

```yaml
version: 1
rules:
  - name: "max-function-lines"
    description: "Keep functions under 50 lines"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        lines: "> 50"
    message: "Function has {{lines}} lines (max: 50)"
    suggestion: "Consider extracting smaller functions"

  - name: "max-params"
    description: "Keep parameter count low"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        params: "> 5"
    message: "Function has too many parameters"
    suggestion: "Use a configuration object or dataclass"
```

### Example 3: Enforce Security Best Practices

```yaml
version: 1
rules:
  - name: "no-dangerous-functions"
    description: "Disallow dangerous functions"
    severity: "critical"
    pattern:
      type: "function_call"
      name: "eval"
    message: "eval() is a security risk"
    suggestion: "Use ast.literal_eval() for safe evaluation"

  - name: "no-shell-injection"
    description: "Avoid shell=True in subprocess"
    severity: "critical"
    pattern:
      type: "regex"
      regex: "subprocess\\\\.(call|run|Popen).*shell=True"
    message: "Using shell=True can lead to shell injection"
    suggestion: "Pass command as a list instead"
```

### Example 4: Project-Specific Patterns

```yaml
version: 1
rules:
  - name: "use-company-logger"
    description: "Use company logging framework"
    severity: "error"
    pattern:
      type: "import"
      name: "logging"
    include:
      - "src/**"
    message: "Use company.logging instead of standard logging"
    suggestion: "from company import logging"

  - name: "no-deprecated-api"
    description: "Don't use deprecated API"
    severity: "error"
    pattern:
      type: "function_call"
      name: "old_api_call"
    message: "old_api_call() is deprecated"
    suggestion: "Use new_api_call() instead"
```

## Integration with Refactron

### Programmatic Usage

```python
from pathlib import Path
from refactron.core.config import RefactronConfig
from refactron.rules import CustomRuleAnalyzer

# Load rules from file
config = RefactronConfig()
analyzer = CustomRuleAnalyzer(config, rules_file=Path(".refactron-rules.yaml"))

# Or load from string
yaml_content = """
version: 1
rules:
  - name: "test-rule"
    description: "Test"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "test"
    message: "Test message"
"""
analyzer.load_rules_from_string(yaml_content)

# Analyze code
issues = analyzer.analyze(Path("myfile.py"), source_code)
```

### Creating Rules from Templates

```python
from refactron.rules import create_ruleset_from_templates
import yaml

# Create a ruleset from templates
ruleset = create_ruleset_from_templates([
    "no-eval",
    "no-exec",
    "max-function-length",
    "no-debug-statements"
])

# Save to file
with open(".refactron-rules.yaml", "w") as f:
    yaml.dump(ruleset, f, default_flow_style=False)
```

## Best Practices

1. **Start Simple**: Begin with a few essential rules and add more over time
2. **Use Descriptive Names**: Make rule names clear and consistent (e.g., `no-*`, `max-*`, `require-*`)
3. **Provide Good Messages**: Include helpful error messages and suggestions
4. **Test Your Rules**: Test custom rules on representative code samples
5. **Use Exclude Patterns**: Exclude test files and examples where appropriate
6. **Document Your Rules**: Keep a separate document explaining why each rule exists
7. **Version Your Rules**: Keep your rules file in version control
8. **Review Regularly**: Periodically review and update rules based on team feedback

## Troubleshooting

### Rule Not Matching

1. Check pattern type matches the code construct
2. Verify file is not excluded by exclude patterns
3. Test regex patterns in a regex tester
4. Ensure rule is enabled

### Invalid YAML

1. Use proper indentation (2 spaces)
2. Quote strings with special characters
3. Escape backslashes in regex patterns
4. Validate YAML syntax with an online validator

### Performance Issues

1. Use specific patterns instead of broad regex
2. Limit the scope with include patterns
3. Disable unused rules
4. Break complex rules into simpler ones

## Advanced Topics

### Message Template Variables

Use `{{variable}}` in messages to include context:

```yaml
message: "Function has {{lines}} lines and {{params}} parameters"
```

Available variables depend on the pattern type:
- Function calls: `function_name`
- Class definitions: `class_name`
- Function definitions: `function_name`, `lines`, `params` (if using constraints)
- Imports: `module`
- Attributes: `attribute`

### Combining Rules

Create comprehensive rule sets by combining multiple patterns:

```yaml
version: 1
rules:
  # Security rules
  - name: "no-eval"
    # ... eval rule
  
  - name: "no-exec"
    # ... exec rule
  
  # Code quality rules
  - name: "max-function-length"
    # ... length rule
  
  - name: "require-docstrings"
    # ... docstring rule
```

## Reference

### Complete Example

See `.refactron-rules.example.yaml` in the project root for a complete example with all pattern types.

### API Reference

- `CustomRuleAnalyzer`: Main analyzer class
- `RuleLoader`: Loads and validates rules
- `PatternMatcher`: Matches patterns in code
- `CustomRule`, `RuleSet`: Data models
- Template functions: `get_template()`, `list_templates()`, etc.

## Support

For issues or questions about custom rules:

1. Check the example file: `.refactron-rules.example.yaml`
2. Review the test file: `tests/test_custom_rules.py`
3. Open an issue on GitHub

## Next Steps

- Review the example file: `.refactron-rules.example.yaml`
- See the test file: `tests/test_custom_rules.py` for advanced usage
- Check the demo: `examples/custom_rules_demo.py` for interactive examples
