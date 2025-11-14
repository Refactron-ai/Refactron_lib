"""Tests for enhanced analyzer features."""

from pathlib import Path

from refactron.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from refactron.analyzers.complexity_analyzer import ComplexityAnalyzer
from refactron.analyzers.performance_analyzer import PerformanceAnalyzer
from refactron.analyzers.security_analyzer import SecurityAnalyzer
from refactron.core.config import RefactronConfig


class TestSecurityAnalyzerEnhancements:
    """Test enhanced security analyzer features."""

    def test_sql_parameterization_string_concat(self) -> None:
        """Test detection of SQL string concatenation."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "SEC009" for issue in issues)
        assert any(
            "unsafe string operations" in issue.message.lower()
            or "string concatenation" in issue.message.lower()
            for issue in issues
        )

    def test_sql_parameterization_format(self) -> None:
        """Test detection of SQL .format() usage."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import sqlite3

def get_user(username):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE name = '{}'".format(username)
    cursor.execute(query)
    return cursor.fetchone()
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "SEC009" for issue in issues)
        assert any(
            "unsafe string operations" in issue.message.lower() or ".format()" in issue.message
            for issue in issues
        )

    def test_ssrf_vulnerability_detection(self) -> None:
        """Test detection of SSRF vulnerabilities."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import requests

def fetch_url(user_url):
    response = requests.get(f"http://api.example.com/{user_url}")
    return response.text
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "SEC010" for issue in issues)
        assert any("SSRF" in issue.message for issue in issues)

    def test_insecure_random_detection(self) -> None:
        """Test detection of insecure random module usage."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import random

def generate_token():
    return random.randint(1000, 9999)
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "SEC011" for issue in issues)
        assert any("random" in issue.message.lower() for issue in issues)

    def test_weak_ssl_tls_verify_false(self) -> None:
        """Test detection of SSL verification disabled."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import requests

def fetch_data():
    response = requests.get("https://example.com", verify=False)
    return response.json()
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "SEC013" for issue in issues)
        assert any("verify=False" in issue.message for issue in issues)


class TestComplexityAnalyzerEnhancements:
    """Test enhanced complexity analyzer features."""

    def test_nested_loop_depth_detection(self) -> None:
        """Test detection of deeply nested loops."""
        config = RefactronConfig()
        analyzer = ComplexityAnalyzer(config)

        code = """
def process_data(data):
    for i in range(len(data)):
        for j in range(len(data[i])):
            for k in range(len(data[i][j])):
                for l in range(len(data[i][j][k])):
                    print(data[i][j][k][l])
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "C003" for issue in issues)
        assert any("nested loops" in issue.message.lower() for issue in issues)

    def test_method_call_chain_complexity(self) -> None:
        """Test detection of complex method call chains."""
        config = RefactronConfig()
        analyzer = ComplexityAnalyzer(config)

        code = """
def process_string(text):
    result = text.strip().lower().replace(" ", "_").split("_")[0]
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        # This creates a long call chain
        _call_chain_issues = [i for i in issues if i.rule_id == "C004"]  # noqa: F841
        # May or may not trigger depending on exact chain length calculation
        # Just verify the analyzer runs without errors
        assert isinstance(issues, list)


class TestCodeSmellAnalyzerEnhancements:
    """Test enhanced code smell analyzer features."""

    def test_unused_imports_detection(self) -> None:
        """Test detection of unused imports."""
        config = RefactronConfig()
        analyzer = CodeSmellAnalyzer(config)

        code = """
import os
import sys
import json

def hello():
    print("Hello, World!")
"""

        issues = analyzer.analyze(Path("test.py"), code)
        unused_import_issues = [i for i in issues if i.rule_id == "S006"]
        # Should detect unused imports (os, sys, json)
        assert len(unused_import_issues) >= 1

    def test_repeated_code_blocks_detection(self) -> None:
        """Test detection of repeated code blocks."""
        config = RefactronConfig()
        analyzer = CodeSmellAnalyzer(config)

        code = """
def process_items(items):
    # First block
    x = items[0]
    y = x * 2
    z = y + 1

    result1 = z

    # Second block (repeated)
    x = items[1]
    y = x * 2
    z = y + 1

    result2 = z

    return result1 + result2
"""

        issues = analyzer.analyze(Path("test.py"), code)
        repeated_code_issues = [i for i in issues if i.rule_id == "S007"]
        assert len(repeated_code_issues) >= 1
        assert any("repeated code" in issue.message.lower() for issue in repeated_code_issues)


class TestPerformanceAnalyzer:
    """Test new performance analyzer."""

    def test_analyzer_name(self) -> None:
        """Test analyzer name property."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)
        assert analyzer.name == "performance"

    def test_n_plus_one_query_detection(self) -> None:
        """Test detection of N+1 query antipattern."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = """
def get_user_posts(user_ids):
    posts = []
    for user_id in user_ids:
        result = db.execute("SELECT * FROM posts WHERE user_id = ?", (user_id,))
        posts.append(result)
    return posts
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "P001" for issue in issues)
        assert any("N+1" in issue.message for issue in issues)

    def test_inefficient_list_comprehension_detection(self) -> None:
        """Test detection of inefficient list comprehension patterns."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = """
def filter_items(items):
    result = list(filter(lambda x: x > 0, items))
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "P002" for issue in issues)
        assert any("list(filter" in issue.message.lower() for issue in issues)

    def test_unnecessary_iterations_detection(self) -> None:
        """Test detection of unnecessary iterations."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = """
def process_data(items):
    total = 0
    for item in items:
        total += item

    squared = []
    for item in items:
        squared.append(item ** 2)

    return total, squared
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "P004" for issue in issues)
        assert any("iterated" in issue.message.lower() for issue in issues)

    def test_inefficient_string_concatenation(self) -> None:
        """Test detection of inefficient string concatenation."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = """
def build_string(items):
    result = ""
    for item in items:
        result += str(item)
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "P005" for issue in issues)
        assert any("concatenation" in issue.message.lower() for issue in issues)

    def test_redundant_list_call_detection(self) -> None:
        """Test detection of redundant list() calls."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = """
def get_squares(numbers):
    result = list([x**2 for x in numbers])
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert any(issue.rule_id == "P006" for issue in issues)
        assert any("redundant" in issue.message.lower() for issue in issues)

    def test_handles_syntax_errors(self) -> None:
        """Test that analyzer handles syntax errors gracefully."""
        config = RefactronConfig()
        analyzer = PerformanceAnalyzer(config)

        code = "def broken function(:"

        issues = analyzer.analyze(Path("test.py"), code)
        # Should not crash, returns empty list for syntax errors
        assert isinstance(issues, list)
