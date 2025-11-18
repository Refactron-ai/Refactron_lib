"""Tests for custom rule framework."""

import tempfile
from pathlib import Path

import pytest

from refactron.core.config import RefactronConfig
from refactron.core.models import IssueLevel
from refactron.rules.analyzer import CustomRuleAnalyzer
from refactron.rules.loader import RuleLoader, RuleValidationError
from refactron.rules.matcher import PatternMatcher
from refactron.rules.models import (
    CustomRule,
    PatternConfig,
    PatternType,
    RuleSeverity,
    RuleSet,
)
from refactron.rules.templates import (
    create_ruleset_from_templates,
    generate_example_ruleset,
    get_template,
    list_templates,
)


class TestRuleModels:
    """Test rule data models."""

    def test_pattern_config_from_dict(self):
        """Test PatternConfig creation from dictionary."""
        data = {"type": "function_call", "name": "print"}
        pattern = PatternConfig.from_dict(data)

        assert pattern.type == PatternType.FUNCTION_CALL
        assert pattern.name == "print"

    def test_custom_rule_from_dict(self):
        """Test CustomRule creation from dictionary."""
        data = {
            "name": "no-print",
            "description": "No print statements",
            "severity": "warning",
            "pattern": {"type": "function_call", "name": "print"},
            "message": "Don't use print",
        }
        rule = CustomRule.from_dict(data)

        assert rule.name == "no-print"
        assert rule.severity == RuleSeverity.WARNING
        assert rule.pattern.type == PatternType.FUNCTION_CALL

    def test_ruleset_from_dict(self):
        """Test RuleSet creation from dictionary."""
        data = {
            "version": "1",
            "rules": [
                {
                    "name": "rule1",
                    "description": "Test rule",
                    "severity": "info",
                    "pattern": {"type": "function_call", "name": "test"},
                    "message": "Test message",
                }
            ],
        }
        ruleset = RuleSet.from_dict(data)

        assert ruleset.version == "1"
        assert len(ruleset.rules) == 1
        assert ruleset.rules[0].name == "rule1"


class TestRuleLoader:
    """Test rule loading and validation."""

    def test_load_valid_rules_from_string(self):
        """Test loading valid rules from YAML string."""
        yaml_content = """
version: 1
rules:
  - name: "no-print"
    description: "No print statements"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    message: "Don't use print"
"""
        loader = RuleLoader()
        ruleset = loader.load_from_string(yaml_content)

        assert len(ruleset.rules) == 1
        assert ruleset.rules[0].name == "no-print"

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        loader = RuleLoader()
        with pytest.raises(RuleValidationError, match="Invalid YAML"):
            loader.load_from_string("invalid: yaml: content:")

    def test_validate_rule_name(self):
        """Test rule name validation."""
        yaml_content = """
version: 1
rules:
  - name: "Invalid Name!"
    description: "Test"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "test"
    message: "Test"
"""
        loader = RuleLoader()
        with pytest.raises(RuleValidationError, match="Invalid rule name"):
            loader.load_from_string(yaml_content)

    def test_validate_missing_description(self):
        """Test validation of missing description."""
        yaml_content = """
version: 1
rules:
  - name: "test-rule"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "test"
    message: "Test"
"""
        loader = RuleLoader()
        with pytest.raises(RuleValidationError, match="requires a description"):
            loader.load_from_string(yaml_content)

    def test_validate_invalid_regex(self):
        """Test validation of invalid regex pattern."""
        yaml_content = """
version: 1
rules:
  - name: "test-rule"
    description: "Test"
    severity: "warning"
    pattern:
      type: "regex"
      regex: "(?P<invalid"
    message: "Test"
"""
        loader = RuleLoader()
        with pytest.raises(RuleValidationError, match="invalid regex pattern"):
            loader.load_from_string(yaml_content)

    def test_load_from_file(self):
        """Test loading rules from a file."""
        yaml_content = """
version: 1
rules:
  - name: "no-eval"
    description: "No eval"
    severity: "error"
    pattern:
      type: "function_call"
      name: "eval"
    message: "Don't use eval"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_file = Path(f.name)

        try:
            loader = RuleLoader()
            ruleset = loader.load_from_file(temp_file)
            assert len(ruleset.rules) == 1
            assert ruleset.rules[0].name == "no-eval"
        finally:
            temp_file.unlink()

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = RuleLoader()
        with pytest.raises(RuleValidationError, match="not found"):
            loader.load_from_file(Path("/nonexistent/file.yaml"))


class TestPatternMatcher:
    """Test pattern matching."""

    def test_match_function_call(self):
        """Test matching function calls."""
        rule_data = {
            "name": "no-print",
            "description": "No print",
            "severity": "warning",
            "pattern": {"type": "function_call", "name": "print"},
            "message": "Don't use print",
        }
        rule = CustomRule.from_dict(rule_data)

        code = """
def test():
    print("hello")
    x = 1
    print("world")
"""
        matcher = PatternMatcher()
        matches = matcher.match(rule, Path("test.py"), code)

        assert len(matches) == 2
        assert matches[0].line_number == 3
        assert matches[1].line_number == 5

    def test_match_class_def(self):
        """Test matching class definitions."""
        rule_data = {
            "name": "check-class",
            "description": "Check class",
            "severity": "info",
            "pattern": {"type": "class_def", "name": "MyClass"},
            "message": "Found class",
        }
        rule = CustomRule.from_dict(rule_data)

        code = """
class MyClass:
    pass

class OtherClass:
    pass
"""
        matcher = PatternMatcher()
        matches = matcher.match(rule, Path("test.py"), code)

        assert len(matches) == 1
        assert matches[0].context["class_name"] == "MyClass"

    def test_match_function_def_with_constraints(self):
        """Test matching function definitions with constraints."""
        rule_data = {
            "name": "long-function",
            "description": "Long function",
            "severity": "warning",
            "pattern": {"type": "function_def", "constraints": {"lines": "> 5"}},
            "message": "Function too long",
        }
        rule = CustomRule.from_dict(rule_data)

        code = """
def short_func():
    return 1

def long_func():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    return x + y + z
"""
        matcher = PatternMatcher()
        matches = matcher.match(rule, Path("test.py"), code)

        assert len(matches) == 1
        assert matches[0].context["function_name"] == "long_func"
        assert matches[0].context["lines"] > 5

    def test_match_regex(self):
        """Test regex pattern matching."""
        rule_data = {
            "name": "no-bare-except",
            "description": "No bare except",
            "severity": "warning",
            "pattern": {"type": "regex", "regex": r"except\s*:"},
            "message": "Use specific exception",
        }
        rule = CustomRule.from_dict(rule_data)

        code = """
try:
    risky_operation()
except:
    pass
"""
        matcher = PatternMatcher()
        matches = matcher.match(rule, Path("test.py"), code)

        assert len(matches) == 1
        assert "except:" in matches[0].code_snippet

    def test_exclude_patterns(self):
        """Test file exclusion patterns."""
        rule_data = {
            "name": "no-print",
            "description": "No print",
            "severity": "warning",
            "pattern": {"type": "function_call", "name": "print"},
            "message": "Don't use print",
            "exclude": ["test_*.py", "**/test_*.py"],
        }
        rule = CustomRule.from_dict(rule_data)

        code = 'print("hello")'
        matcher = PatternMatcher()

        # Should match in regular file
        matches = matcher.match(rule, Path("myfile.py"), code)
        assert len(matches) == 1

        # Should not match in test file (simple pattern)
        matches = matcher.match(rule, Path("test_myfile.py"), code)
        assert len(matches) == 0

        # Should not match in test file (nested pattern)
        matches = matcher.match(rule, Path("tests/test_myfile.py"), code)
        assert len(matches) == 0

    def test_include_patterns(self):
        """Test file inclusion patterns."""
        rule_data = {
            "name": "check-src",
            "description": "Check src files",
            "severity": "info",
            "pattern": {"type": "function_call", "name": "test"},
            "message": "Test function found",
            "include": ["src/**", "**/src/**"],
        }
        rule = CustomRule.from_dict(rule_data)

        code = "test()"
        matcher = PatternMatcher()

        # Should match in src file
        matches = matcher.match(rule, Path("src/myfile.py"), code)
        assert len(matches) == 1

        # Should match in nested src file
        matches = matcher.match(rule, Path("project/src/myfile.py"), code)
        assert len(matches) == 1

        # Should not match outside src
        matches = matcher.match(rule, Path("lib/myfile.py"), code)
        assert len(matches) == 0


class TestCustomRuleAnalyzer:
    """Test the custom rule analyzer."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        config = RefactronConfig()
        analyzer = CustomRuleAnalyzer(config)

        assert analyzer.name == "custom_rules"
        assert isinstance(analyzer.loader, RuleLoader)
        assert isinstance(analyzer.matcher, PatternMatcher)

    def test_load_rules_from_string(self):
        """Test loading rules from string."""
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
        config = RefactronConfig()
        analyzer = CustomRuleAnalyzer(config)
        analyzer.load_rules_from_string(yaml_content)

        assert len(analyzer.custom_rules) == 1

    def test_analyze_with_custom_rules(self):
        """Test analyzing code with custom rules."""
        yaml_content = """
version: 1
rules:
  - name: "no-print"
    description: "No print"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    message: "Avoid using print()"
"""
        config = RefactronConfig()
        analyzer = CustomRuleAnalyzer(config)
        analyzer.load_rules_from_string(yaml_content)

        code = """
def my_function():
    print("Hello, world!")
    return 42
"""
        issues = analyzer.analyze(Path("test.py"), code)

        assert len(issues) == 1
        assert issues[0].message == "Avoid using print()"
        assert issues[0].level == IssueLevel.WARNING
        assert issues[0].rule_id == "no-print"
        assert issues[0].line_number == 3

    def test_message_template_substitution(self):
        """Test message template variable substitution."""
        yaml_content = """
version: 1
rules:
  - name: "long-function"
    description: "Check function length"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        lines: "> 3"
    message: "Function has {{lines}} lines"
"""
        config = RefactronConfig()
        analyzer = CustomRuleAnalyzer(config)
        analyzer.load_rules_from_string(yaml_content)

        code = """
def long_function():
    x = 1
    y = 2
    z = 3
    return x + y + z
"""
        issues = analyzer.analyze(Path("test.py"), code)

        assert len(issues) == 1
        assert "lines" in issues[0].message
        # The actual number should be substituted

    def test_disabled_rule_not_applied(self):
        """Test that disabled rules are not applied."""
        yaml_content = """
version: 1
rules:
  - name: "no-print"
    description: "No print"
    severity: "warning"
    pattern:
      type: "function_call"
      name: "print"
    message: "No print"
    enabled: false
"""
        config = RefactronConfig()
        analyzer = CustomRuleAnalyzer(config)
        analyzer.load_rules_from_string(yaml_content)

        code = 'print("hello")'
        issues = analyzer.analyze(Path("test.py"), code)

        assert len(issues) == 0


class TestRuleTemplates:
    """Test rule templates."""

    def test_get_template(self):
        """Test getting a specific template."""
        template = get_template("no-print-in-production")

        assert template["name"] == "no-print-in-production"
        assert template["severity"] == "warning"
        assert template["pattern"]["type"] == "function_call"

    def test_list_templates(self):
        """Test listing all templates."""
        templates = list_templates()

        assert len(templates) > 0
        assert "no-print-in-production" in templates
        assert "no-eval" in templates

    def test_create_ruleset_from_templates(self):
        """Test creating a ruleset from templates."""
        ruleset = create_ruleset_from_templates(["no-eval", "no-exec"])

        assert ruleset["version"] == "1"
        assert len(ruleset["rules"]) == 2
        assert ruleset["rules"][0]["name"] == "no-eval"
        assert ruleset["rules"][1]["name"] == "no-exec"

    def test_generate_example_ruleset(self):
        """Test generating an example ruleset."""
        ruleset = generate_example_ruleset()

        assert "version" in ruleset
        assert "rules" in ruleset
        assert len(ruleset["rules"]) > 0

    def test_template_not_found(self):
        """Test getting a non-existent template."""
        with pytest.raises(KeyError):
            get_template("nonexistent-template")


class TestIntegration:
    """Integration tests for custom rules."""

    def test_end_to_end_rule_execution(self):
        """Test complete workflow from loading to analysis."""
        # Create a temporary rules file
        yaml_content = """
version: 1
rules:
  - name: "no-eval"
    description: "No eval"
    severity: "critical"
    pattern:
      type: "function_call"
      name: "eval"
    message: "eval() is dangerous"
    suggestion: "Use ast.literal_eval()"

  - name: "max-params"
    description: "Max params"
    severity: "warning"
    pattern:
      type: "function_def"
      constraints:
        params: "> 3"
    message: "Too many parameters"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_file = Path(f.name)

        try:
            config = RefactronConfig()
            analyzer = CustomRuleAnalyzer(config)
            analyzer.load_rules(temp_file)

            code = """
def bad_function(a, b, c, d, e):
    result = eval("2 + 2")
    return result
"""
            issues = analyzer.analyze(Path("test.py"), code)

            # Should find both issues
            assert len(issues) == 2

            # Check that we found the eval issue
            eval_issues = [i for i in issues if i.rule_id == "no-eval"]
            assert len(eval_issues) == 1
            assert eval_issues[0].level == IssueLevel.CRITICAL

            # Check that we found the parameter issue
            param_issues = [i for i in issues if i.rule_id == "max-params"]
            assert len(param_issues) == 1

        finally:
            temp_file.unlink()
