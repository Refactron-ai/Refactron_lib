"""
Demo: Custom Rule Framework

This example demonstrates how to use Refactron's custom rule framework
to define and enforce project-specific coding standards.
"""

from pathlib import Path
from refactron.core.config import RefactronConfig
from refactron.rules import (
    CustomRuleAnalyzer,
    generate_example_ruleset,
    list_templates,
)
import yaml


def demo_basic_usage():
    """Demonstrate basic custom rule usage."""
    print("=" * 60)
    print("Demo 1: Basic Custom Rule Usage")
    print("=" * 60)

    # Create a simple custom rule
    yaml_content = """
version: 1
rules:
  - name: "no-print"
    description: "Disallow print statements"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    message: "Avoid using print() in production code"
    suggestion: "Use logging.info() instead"
"""

    # Initialize analyzer
    config = RefactronConfig()
    analyzer = CustomRuleAnalyzer(config)
    analyzer.load_rules_from_string(yaml_content)

    # Analyze some code
    code = """
def my_function():
    print("Hello, world!")
    x = 42
    print(f"The answer is {x}")
    return x
"""

    issues = analyzer.analyze(Path("example.py"), code)

    print(f"\nAnalyzed code:\n{code}")
    print(f"\nFound {len(issues)} issue(s):")
    for issue in issues:
        print(f"  Line {issue.line_number}: {issue.message}")
        if issue.suggestion:
            print(f"    Suggestion: {issue.suggestion}")


def demo_templates():
    """Demonstrate using rule templates."""
    print("\n" + "=" * 60)
    print("Demo 2: Using Rule Templates")
    print("=" * 60)

    # List available templates
    templates = list_templates()
    print(f"\nAvailable templates ({len(templates)} total):")
    for i, template in enumerate(templates[:5], 1):
        print(f"  {i}. {template}")
    print(f"  ... and {len(templates) - 5} more")

    # Generate an example ruleset
    ruleset = generate_example_ruleset()
    print(f"\nExample ruleset with {len(ruleset['rules'])} rules:")
    for rule in ruleset["rules"][:3]:
        print(f"  - {rule['name']}: {rule['description']}")
    print(f"  ... and {len(ruleset['rules']) - 3} more")


def demo_function_constraints():
    """Demonstrate function constraint rules."""
    print("\n" + "=" * 60)
    print("Demo 3: Function Constraints")
    print("=" * 60)

    yaml_content = """
version: 1
rules:
  - name: "max-function-length"
    description: "Functions should be less than 10 lines"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        lines: "> 10"
    message: "Function has {{lines}} lines (max: 10)"
    suggestion: "Consider extracting smaller functions"

  - name: "max-params"
    description: "Functions should have less than 4 parameters"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        params: "> 3"
    message: "Function has too many parameters"
    suggestion: "Use a configuration object"
"""

    config = RefactronConfig()
    analyzer = CustomRuleAnalyzer(config)
    analyzer.load_rules_from_string(yaml_content)

    code = """
def short_function():
    return 42

def long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    return sum([x, y, z, a, b, c, d, e, f, g])

def too_many_params(a, b, c, d, e):
    return a + b + c + d + e
"""

    issues = analyzer.analyze(Path("example.py"), code)

    print(f"\nFound {len(issues)} issue(s):")
    for issue in issues:
        print(f"  Line {issue.line_number}: {issue.message}")


def demo_regex_patterns():
    """Demonstrate regex pattern matching."""
    print("\n" + "=" * 60)
    print("Demo 4: Regex Pattern Matching")
    print("=" * 60)

    yaml_content = """
version: 1
rules:
  - name: "no-bare-except"
    description: "Disallow bare except clauses"
    severity: "warning"
    pattern:
      type: "regex"
      regex: "except\\\\s*:"
    message: "Bare except catches all exceptions"
    suggestion: "Catch specific exceptions instead"
"""

    config = RefactronConfig()
    analyzer = CustomRuleAnalyzer(config)
    analyzer.load_rules_from_string(yaml_content)

    code = """
try:
    risky_operation()
except:
    pass

try:
    another_operation()
except ValueError:
    handle_error()
"""

    issues = analyzer.analyze(Path("example.py"), code)

    print(f"\nFound {len(issues)} issue(s):")
    for issue in issues:
        print(f"  Line {issue.line_number}: {issue.message}")


def demo_file_filtering():
    """Demonstrate file include/exclude patterns."""
    print("\n" + "=" * 60)
    print("Demo 5: File Filtering")
    print("=" * 60)

    yaml_content = """
version: 1
rules:
  - name: "no-print"
    description: "No print in production"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    exclude:
      - "test_*.py"
      - "**/tests/**"
    message: "No print in production code"
"""

    config = RefactronConfig()
    analyzer = CustomRuleAnalyzer(config)
    analyzer.load_rules_from_string(yaml_content)

    code = 'print("hello")'

    # Should find issue in production file
    issues1 = analyzer.analyze(Path("myapp.py"), code)
    print(f"\nAnalyzing myapp.py: Found {len(issues1)} issue(s)")

    # Should not find issue in test file
    issues2 = analyzer.analyze(Path("test_myapp.py"), code)
    print(f"Analyzing test_myapp.py: Found {len(issues2)} issue(s) (excluded)")


def demo_create_custom_ruleset():
    """Demonstrate creating a custom ruleset file."""
    print("\n" + "=" * 60)
    print("Demo 6: Creating a Custom Ruleset File")
    print("=" * 60)

    ruleset = {
        "version": "1",
        "rules": [
            {
                "name": "use-logging",
                "description": "Use logging instead of print",
                "severity": "warning",
                "pattern": {"type": "function_call", "name": "print"},
                "exclude": ["**/test_*.py"],
                "message": "Use logging.info() instead of print()",
                "suggestion": "import logging; logger.info('message')",
            },
            {
                "name": "max-complexity",
                "description": "Keep functions simple",
                "severity": "warning",
                "pattern": {"type": "function_def", "constraints": {"lines": "> 50"}},
                "message": "Function is too complex ({{lines}} lines)",
                "suggestion": "Extract smaller functions",
            },
        ],
    }

    # Print as YAML
    print("\nCustom ruleset YAML:")
    print("-" * 60)
    print(yaml.dump(ruleset, default_flow_style=False))
    print("-" * 60)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("Refactron Custom Rule Framework Demo")
    print("=" * 60)

    demo_basic_usage()
    demo_templates()
    demo_function_constraints()
    demo_regex_patterns()
    demo_file_filtering()
    demo_create_custom_ruleset()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Read docs/CUSTOM_RULES.md for detailed documentation")
    print("  2. Check .refactron-rules.example.yaml for examples")
    print("  3. Create your own .refactron-rules.yaml file")
    print("  4. Run: refactron analyze --help")


if __name__ == "__main__":
    main()
