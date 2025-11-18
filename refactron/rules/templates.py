"""Rule template library with common patterns."""

# Common rule templates for quick setup

RULE_TEMPLATES = {
    "no-print-in-production": {
        "name": "no-print-in-production",
        "description": "Disallow print() statements in production code",
        "severity": "warning",
        "pattern": {"type": "function_call", "name": "print"},
        "exclude": ["**/test_*.py", "**/tests/**", "**/*_test.py", "**/examples/**"],
        "message": "Avoid using print() in production code",
        "suggestion": "Use logging instead: logger.info(...)",
    },
    "no-eval": {
        "name": "no-eval",
        "description": "Disallow eval() due to security risks",
        "severity": "critical",
        "pattern": {"type": "function_call", "name": "eval"},
        "message": "Use of eval() is a security risk",
        "suggestion": "Consider safer alternatives like ast.literal_eval() for literals",
    },
    "no-exec": {
        "name": "no-exec",
        "description": "Disallow exec() due to security risks",
        "severity": "critical",
        "pattern": {"type": "function_call", "name": "exec"},
        "message": "Use of exec() is a security risk",
        "suggestion": "Refactor code to avoid dynamic code execution",
    },
    "max-function-length": {
        "name": "max-function-length",
        "description": "Functions should be less than 50 lines",
        "severity": "warning",
        "pattern": {"type": "function_def", "constraints": {"lines": "> 50"}},
        "message": "Function is too long ({{lines}} lines)",
        "suggestion": "Consider extracting methods to improve readability",
    },
    "max-function-params": {
        "name": "max-function-params",
        "description": "Functions should have less than 5 parameters",
        "severity": "warning",
        "pattern": {"type": "function_def", "constraints": {"params": "> 5"}},
        "message": "Function has too many parameters",
        "suggestion": "Consider using a configuration object or dataclass",
    },
    "no-wildcard-import": {
        "name": "no-wildcard-import",
        "description": "Disallow wildcard imports",
        "severity": "warning",
        "pattern": {"type": "import", "name": "*"},
        "message": "Wildcard imports make code harder to understand",
        "suggestion": "Import specific names instead: from module import name1, name2",
    },
    "no-bare-except": {
        "name": "no-bare-except",
        "description": "Disallow bare except clauses",
        "severity": "warning",
        "pattern": {"type": "regex", "regex": r"except\s*:"},
        "message": "Bare except clause catches all exceptions including system exits",
        "suggestion": "Catch specific exceptions: except ValueError:",
    },
    "no-mutable-default": {
        "name": "no-mutable-default",
        "description": "Disallow mutable default arguments",
        "severity": "error",
        "pattern": {"type": "regex", "regex": r"def\s+\w+\([^)]*=\s*\[\s*\]"},
        "message": "Mutable default arguments can cause unexpected behavior",
        "suggestion": "Use None as default and create the list inside the function",
    },
    "require-docstring": {
        "name": "require-docstring",
        "description": "Require docstrings for public functions",
        "severity": "info",
        "pattern": {"type": "function_def"},
        "message": "Public function missing docstring",
        "suggestion": "Add a docstring describing what the function does",
    },
    "no-global-state": {
        "name": "no-global-state",
        "description": "Avoid global variables",
        "severity": "warning",
        "pattern": {"type": "regex", "regex": r"^[A-Z_][A-Z0-9_]*\s*="},
        "exclude": ["**/constants.py", "**/config.py", "**/settings.py"],
        "message": "Global variable detected",
        "suggestion": "Consider using class attributes or dependency injection",
    },
    "no-debug-statements": {
        "name": "no-debug-statements",
        "description": "Disallow debug statements in production",
        "severity": "warning",
        "pattern": {"type": "regex", "regex": r"(import pdb|pdb\.set_trace|breakpoint\(\))"},
        "exclude": ["**/test_*.py", "**/tests/**"],
        "message": "Debug statement found in code",
        "suggestion": "Remove debug statements before committing",
    },
    "no-hardcoded-credentials": {
        "name": "no-hardcoded-credentials",
        "description": "Disallow hardcoded passwords or API keys",
        "severity": "critical",
        "pattern": {
            "type": "regex",
            "regex": r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
        },
        "message": "Hardcoded credential detected",
        "suggestion": "Use environment variables or a secrets manager",
    },
    "no-string-concat-in-loop": {
        "name": "no-string-concat-in-loop",
        "description": "Avoid string concatenation in loops",
        "severity": "warning",
        "pattern": {"type": "regex", "regex": r"for\s+.*:\s*\n\s*.*\+="},
        "message": "String concatenation in loop is inefficient",
        "suggestion": "Use list.append() and ''.join() instead",
    },
}


def get_template(template_name: str) -> dict:
    """
    Get a rule template by name.

    Args:
        template_name: Name of the template

    Returns:
        Template dictionary

    Raises:
        KeyError: If template doesn't exist
    """
    if template_name not in RULE_TEMPLATES:
        raise KeyError(f"Template '{template_name}' not found")
    return RULE_TEMPLATES[template_name].copy()


def list_templates() -> list:
    """
    List all available template names.

    Returns:
        List of template names
    """
    return list(RULE_TEMPLATES.keys())


def get_all_templates() -> dict:
    """
    Get all rule templates.

    Returns:
        Dictionary of all templates
    """
    return RULE_TEMPLATES.copy()


def create_ruleset_from_templates(template_names: list, version: str = "1") -> dict:
    """
    Create a ruleset from template names.

    Args:
        template_names: List of template names to include
        version: Version string for the ruleset

    Returns:
        Ruleset dictionary ready to be saved as YAML

    Raises:
        KeyError: If a template doesn't exist
    """
    rules = []
    for name in template_names:
        rules.append(get_template(name))

    return {"version": version, "rules": rules}


def generate_example_ruleset() -> dict:
    """
    Generate an example ruleset with common rules.

    Returns:
        Example ruleset dictionary
    """
    example_templates = [
        "no-print-in-production",
        "no-eval",
        "no-exec",
        "max-function-length",
        "max-function-params",
        "no-debug-statements",
        "no-hardcoded-credentials",
    ]
    return create_ruleset_from_templates(example_templates)
