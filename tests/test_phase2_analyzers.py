"""Tests for Phase 2 analyzers - security, dependency, dead code, type hints."""

from pathlib import Path

from refactron.analyzers.dead_code_analyzer import DeadCodeAnalyzer
from refactron.analyzers.dependency_analyzer import DependencyAnalyzer
from refactron.analyzers.security_analyzer import SecurityAnalyzer
from refactron.analyzers.type_hint_analyzer import TypeHintAnalyzer
from refactron.core.config import RefactronConfig


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer functionality."""

    def test_security_analyzer_name(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)
        assert analyzer.name == "security"

    def test_detects_eval_usage(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
def dangerous_function(user_input):
    result = eval(user_input)
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("eval" in issue.message for issue in issues)
        assert any(issue.level.value == "critical" for issue in issues)

    def test_detects_exec_usage(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
def run_code(code_string):
    exec(code_string)
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("exec" in issue.message for issue in issues)

    def test_detects_hardcoded_secrets(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
api_key = "sk_live_1234567890abcdef"
password = "mysecretpassword"
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2
        assert any(
            "secret" in issue.message.lower() or "password" in issue.message.lower()
            for issue in issues
        )

    def test_detects_sql_injection(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
def get_user(username):
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("SQL injection" in issue.message for issue in issues)

    def test_detects_shell_injection(self):
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import subprocess

def run_command(cmd):
    subprocess.call(cmd, shell=True)
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("shell" in issue.message.lower() for issue in issues)


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer functionality."""

    def test_dependency_analyzer_name(self):
        config = RefactronConfig()
        analyzer = DependencyAnalyzer(config)
        assert analyzer.name == "dependency"

    def test_detects_wildcard_imports(self):
        config = RefactronConfig()
        analyzer = DependencyAnalyzer(config)

        code = """
from os import *
from sys import argv
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("wildcard" in issue.message.lower() for issue in issues)

    def test_detects_unused_imports(self):
        config = RefactronConfig()
        analyzer = DependencyAnalyzer(config)

        code = """
import os
import sys
import json

def main():
    print("Hello")
    return sys.argv
"""

        issues = analyzer.analyze(Path("test.py"), code)
        # Should detect os and json as unused
        assert len(issues) >= 2
        assert any("unused" in issue.message.lower() for issue in issues)

    def test_detects_circular_import_pattern(self):
        config = RefactronConfig()
        analyzer = DependencyAnalyzer(config)

        code = """
def my_function():
    import some_module  # Import inside function
    return some_module.do_something()
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any(
            "circular" in issue.message.lower() or "inside function" in issue.message.lower()
            for issue in issues
        )

    def test_detects_deprecated_modules(self):
        config = RefactronConfig()
        analyzer = DependencyAnalyzer(config)

        code = """
import imp
import optparse
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2
        assert any("deprecated" in issue.message.lower() for issue in issues)


class TestDeadCodeAnalyzer:
    """Test DeadCodeAnalyzer functionality."""

    def test_dead_code_analyzer_name(self):
        config = RefactronConfig()
        analyzer = DeadCodeAnalyzer(config)
        assert analyzer.name == "dead_code"

    def test_detects_unused_functions(self):
        config = RefactronConfig()
        analyzer = DeadCodeAnalyzer(config)

        code = """
def used_function():
    return 42

def unused_function():
    return 100

result = used_function()
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("unused_function" in issue.message for issue in issues)

    def test_detects_unreachable_code(self):
        config = RefactronConfig()
        analyzer = DeadCodeAnalyzer(config)

        code = """
def my_function():
    return 42
    print("This will never execute")
    x = 100
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("unreachable" in issue.message.lower() for issue in issues)

    def test_detects_empty_functions(self):
        config = RefactronConfig()
        analyzer = DeadCodeAnalyzer(config)

        code = """
def empty_function():
    pass

def another_empty():
    pass
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2
        assert any("empty" in issue.message.lower() for issue in issues)

    def test_detects_redundant_conditions(self):
        config = RefactronConfig()
        analyzer = DeadCodeAnalyzer(config)

        code = """
def check_something():
    if True:
        return "always"

    if False:
        return "never"

    x = 5
    if x == True:
        return "redundant"
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2
        assert any(
            "always" in issue.message.lower() or "redundant" in issue.message.lower()
            for issue in issues
        )


class TestTypeHintAnalyzer:
    """Test TypeHintAnalyzer functionality."""

    def test_type_hint_analyzer_name(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)
        assert analyzer.name == "type_hints"

    def test_detects_missing_return_type(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
def calculate(x, y):
    return x + y
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0
        assert any("return type" in issue.message.lower() for issue in issues)

    def test_detects_missing_parameter_types(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
def process_data(data, flag):
    return data if flag else None
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2  # Both parameters missing types
        assert any("parameter" in issue.message.lower() for issue in issues)

    def test_detects_any_usage(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
from typing import Any

def process(data: Any) -> Any:
    return data
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2  # Both parameter and return use Any
        assert any("Any" in issue.message for issue in issues)

    def test_detects_incomplete_generics(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
from typing import List, Dict

def get_items() -> List:
    return []

def get_mapping() -> Dict:
    return {}
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) >= 2
        assert any(
            "incomplete" in issue.message.lower() or "generic" in issue.message.lower()
            for issue in issues
        )

    def test_ignores_private_functions(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
def _private_function(x):
    return x * 2
"""

        issues = analyzer.analyze(Path("test.py"), code)
        # Should not flag private functions
        assert len(issues) == 0

    def test_skips_self_and_cls_parameters(self):
        config = RefactronConfig()
        analyzer = TypeHintAnalyzer(config)

        code = """
class MyClass:
    def method(self, value):
        return value

    @classmethod
    def class_method(cls, value):
        return value
"""

        issues = analyzer.analyze(Path("test.py"), code)
        # Should only flag 'value' parameter, not 'self' or 'cls'
        param_issues = [i for i in issues if "parameter" in i.message.lower()]
        assert all("self" not in i.message and "cls" not in i.message for i in param_issues)


class TestPhase2Integration:
    """Integration tests for Phase 2 analyzers."""

    def test_all_analyzers_work_together(self):
        """Test that all Phase 2 analyzers can run on the same code."""
        config = RefactronConfig()

        analyzers = [
            SecurityAnalyzer(config),
            DependencyAnalyzer(config),
            DeadCodeAnalyzer(config),
            TypeHintAnalyzer(config),
        ]

        code = """
import os
import sys

def process_data(data):
    if True:
        result = eval(data)
        return result

def unused_helper():
    pass
"""

        all_issues = []
        for analyzer in analyzers:
            issues = analyzer.analyze(Path("test.py"), code)
            all_issues.extend(issues)

        # Should detect multiple types of issues
        assert len(all_issues) > 0

        # Check we have issues from different analyzers
        categories = set(issue.category.value for issue in all_issues)
        assert len(categories) > 1  # Multiple categories detected

    def test_analyzers_handle_syntax_errors_gracefully(self):
        """Ensure analyzers don't crash on invalid syntax."""
        config = RefactronConfig()

        analyzers = [
            SecurityAnalyzer(config),
            DependencyAnalyzer(config),
            DeadCodeAnalyzer(config),
            TypeHintAnalyzer(config),
        ]

        invalid_code = "def broken function(:"

        for analyzer in analyzers:
            # Should not raise exception, just return empty or handle gracefully
            issues = analyzer.analyze(Path("test.py"), invalid_code)
            assert isinstance(issues, list)
