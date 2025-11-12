"""Tests for false positive reduction features in security analyzer."""

import tempfile
from pathlib import Path

from refactron.analyzers.security_analyzer import SecurityAnalyzer
from refactron.core.config import RefactronConfig
from refactron.core.false_positive_tracker import FalsePositiveTracker


class TestConfidenceScores:
    """Test confidence scoring feature."""

    def test_all_issues_have_confidence_scores(self):
        """Ensure all security issues have confidence scores."""
        config = RefactronConfig()
        analyzer = SecurityAnalyzer(config)

        code = """
import pickle
import random

def dangerous_function(user_input):
    result = eval(user_input)
    exec(user_input)
    return result
"""

        issues = analyzer.analyze(Path("test.py"), code)
        assert len(issues) > 0

        for issue in issues:
            assert hasattr(issue, "confidence")
            assert 0.0 <= issue.confidence <= 1.0

    def test_test_files_have_lower_confidence(self):
        """Test files should get lower confidence scores for certain rules."""
        # Use config without ignoring test files
        config = RefactronConfig(security_ignore_patterns=[])
        analyzer = SecurityAnalyzer(config)

        code = """
def test_eval():
    result = eval("1 + 1")
    assert result == 2
"""

        # Regular file
        regular_issues = analyzer.analyze(Path("myapp/utils.py"), code)
        # Test file
        test_issues = analyzer.analyze(Path("tests/test_utils.py"), code)

        assert len(regular_issues) > 0
        assert len(test_issues) > 0

        # Test files should have lower confidence for eval()
        regular_conf = regular_issues[0].confidence
        test_conf = test_issues[0].confidence
        assert test_conf < regular_conf

    def test_demo_files_have_lower_confidence(self):
        """Demo/example files should get lower confidence scores."""
        # Use config without ignoring files and lower minimum confidence
        config = RefactronConfig(security_ignore_patterns=[], security_min_confidence=0.4)
        analyzer = SecurityAnalyzer(config)

        code = """
import random

def demo_random():
    return random.randint(1, 10)
"""

        regular_issues = analyzer.analyze(Path("myapp/core.py"), code)
        demo_issues = analyzer.analyze(Path("examples/demo.py"), code)

        assert len(regular_issues) > 0
        assert len(demo_issues) > 0

        regular_conf = regular_issues[0].confidence
        demo_conf = demo_issues[0].confidence
        assert demo_conf < regular_conf


class TestContextAwareness:
    """Test context-aware security analysis."""

    def test_ignores_test_files_when_configured(self):
        """Test files should be ignored when configured."""
        config = RefactronConfig(security_ignore_patterns=["**/test_*.py", "**/tests/**/*.py"])
        analyzer = SecurityAnalyzer(config)

        code = """
def test_dangerous():
    eval("1 + 1")
"""

        issues = analyzer.analyze(Path("tests/test_security.py"), code)
        assert len(issues) == 0

    def test_does_not_ignore_non_test_files(self):
        """Non-test files should still be analyzed."""
        config = RefactronConfig(security_ignore_patterns=["**/test_*.py", "**/tests/**/*.py"])
        analyzer = SecurityAnalyzer(config)

        code = """
def dangerous():
    eval("1 + 1")
"""

        issues = analyzer.analyze(Path("myapp/utils.py"), code)
        assert len(issues) > 0

    def test_hardcoded_secrets_lower_confidence_in_tests(self):
        """Hardcoded secrets in test files should have lower confidence."""
        # Use config without ignoring test files
        config = RefactronConfig(security_ignore_patterns=[])
        analyzer = SecurityAnalyzer(config)

        code = """
api_key = "test-api-key-12345"
password = "test-password"
"""

        regular_issues = analyzer.analyze(Path("app/config.py"), code)
        test_issues = analyzer.analyze(Path("tests/test_config.py"), code)

        # Both should detect issues
        assert len(regular_issues) > 0
        assert len(test_issues) > 0

        # Test file secrets should have lower confidence
        for regular_issue in regular_issues:
            if "SEC003" in str(regular_issue.rule_id):
                for test_issue in test_issues:
                    if "SEC003" in str(test_issue.rule_id):
                        assert test_issue.confidence < regular_issue.confidence


class TestWhitelistMechanism:
    """Test rule whitelisting feature."""

    def test_whitelisted_rule_not_reported(self):
        """Whitelisted rules should not be reported."""
        config = RefactronConfig(security_rule_whitelist={"SEC001": ["**/test_*.py"]})
        analyzer = SecurityAnalyzer(config)

        code = """
def test_eval():
    eval("1 + 1")
"""

        issues = analyzer.analyze(Path("tests/test_utils.py"), code)
        assert len(issues) == 0

    def test_non_whitelisted_files_still_reported(self):
        """Non-whitelisted files should still get reports."""
        config = RefactronConfig(security_rule_whitelist={"SEC001": ["**/test_*.py"]})
        analyzer = SecurityAnalyzer(config)

        code = """
def dangerous():
    eval("1 + 1")
"""

        issues = analyzer.analyze(Path("myapp/utils.py"), code)
        assert len(issues) > 0
        assert any("eval" in issue.message for issue in issues)

    def test_multiple_rules_whitelisted(self):
        """Multiple rules can be whitelisted."""
        config = RefactronConfig(
            security_rule_whitelist={
                "SEC001": ["**/test_*.py"],
                "SEC002": ["**/test_*.py"],
                "SEC011": ["**/test_*.py"],
            }
        )
        analyzer = SecurityAnalyzer(config)

        code = """
import pickle
import random

def test_dangerous():
    eval("1 + 1")
"""

        issues = analyzer.analyze(Path("tests/test_utils.py"), code)
        # All whitelisted rules should be filtered out
        assert len([i for i in issues if i.rule_id in ["SEC001", "SEC002", "SEC011"]]) == 0


class TestMinimumConfidenceFilter:
    """Test minimum confidence filtering."""

    def test_filters_low_confidence_issues(self):
        """Issues below minimum confidence should be filtered."""
        config = RefactronConfig(security_min_confidence=0.8)
        analyzer = SecurityAnalyzer(config)

        code = """
def test_function():
    assert x > 0
"""

        issues = analyzer.analyze(Path("tests/test_utils.py"), code)
        # Assert statements have low confidence (0.6), should be filtered
        assert len([i for i in issues if i.rule_id == "SEC008"]) == 0

    def test_keeps_high_confidence_issues(self):
        """Issues above minimum confidence should be kept."""
        config = RefactronConfig(security_min_confidence=0.8)
        analyzer = SecurityAnalyzer(config)

        code = """
import subprocess

def run_command(cmd):
    subprocess.call(cmd, shell=True)
"""

        issues = analyzer.analyze(Path("myapp/utils.py"), code)
        # shell=True has high confidence (0.95), should be kept
        assert len([i for i in issues if i.rule_id == "SEC005"]) > 0

    def test_default_min_confidence(self):
        """Default minimum confidence should be 0.5."""
        config = RefactronConfig()
        assert config.security_min_confidence == 0.5


class TestFalsePositiveTracker:
    """Test false positive tracking system."""

    def test_create_tracker(self):
        """Can create false positive tracker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = FalsePositiveTracker(Path(tmpdir) / "fp.json")
            assert tracker is not None

    def test_mark_false_positive(self):
        """Can mark patterns as false positives."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = FalsePositiveTracker(Path(tmpdir) / "fp.json")
            tracker.mark_false_positive("SEC001", "eval() in test")
            assert tracker.is_false_positive("SEC001", "eval() in test")

    def test_false_positive_persistence(self):
        """False positives should persist across sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "fp.json"

            # First session
            tracker1 = FalsePositiveTracker(storage_path)
            tracker1.mark_false_positive("SEC001", "eval() in test")

            # Second session
            tracker2 = FalsePositiveTracker(storage_path)
            assert tracker2.is_false_positive("SEC001", "eval() in test")

    def test_get_false_positive_patterns(self):
        """Can retrieve all false positive patterns for a rule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = FalsePositiveTracker(Path(tmpdir) / "fp.json")
            tracker.mark_false_positive("SEC001", "pattern1")
            tracker.mark_false_positive("SEC001", "pattern2")
            tracker.mark_false_positive("SEC002", "pattern3")

            patterns = tracker.get_false_positive_patterns("SEC001")
            assert len(patterns) == 2
            assert "pattern1" in patterns
            assert "pattern2" in patterns

    def test_clear_rule(self):
        """Can clear false positives for a specific rule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = FalsePositiveTracker(Path(tmpdir) / "fp.json")
            tracker.mark_false_positive("SEC001", "pattern1")
            tracker.mark_false_positive("SEC002", "pattern2")

            tracker.clear_rule("SEC001")
            assert not tracker.is_false_positive("SEC001", "pattern1")
            assert tracker.is_false_positive("SEC002", "pattern2")

    def test_clear_all(self):
        """Can clear all false positives."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = FalsePositiveTracker(Path(tmpdir) / "fp.json")
            tracker.mark_false_positive("SEC001", "pattern1")
            tracker.mark_false_positive("SEC002", "pattern2")

            tracker.clear_all()
            assert not tracker.is_false_positive("SEC001", "pattern1")
            assert not tracker.is_false_positive("SEC002", "pattern2")


class TestIntegration:
    """Integration tests for false positive reduction features."""

    def test_combined_features(self):
        """Test all features working together."""
        config = RefactronConfig(
            security_ignore_patterns=["**/test_*.py"],
            security_rule_whitelist={"SEC011": ["**/examples/**"]},
            security_min_confidence=0.7,
        )
        analyzer = SecurityAnalyzer(config)

        # Test file with eval - should be ignored
        test_code = """
def test_eval():
    eval("1 + 1")
"""
        test_issues = analyzer.analyze(Path("tests/test_utils.py"), test_code)
        assert len(test_issues) == 0

        # Example file with random - should be whitelisted
        example_code = """
import random

def example():
    return random.randint(1, 10)
"""
        example_issues = analyzer.analyze(Path("examples/demo.py"), example_code)
        # random import should be filtered (whitelisted)
        assert len([i for i in example_issues if i.rule_id == "SEC011"]) == 0

        # Regular file with assert - should be filtered by confidence
        regular_code = """
def validate(x):
    assert x > 0
"""
        regular_issues = analyzer.analyze(Path("myapp/utils.py"), regular_code)
        # Assert has confidence 0.6, below threshold of 0.7
        assert len([i for i in regular_issues if i.rule_id == "SEC008"]) == 0

        # Regular file with shell=True - should be reported
        dangerous_code = """
import subprocess

def run(cmd):
    subprocess.call(cmd, shell=True)
"""
        dangerous_issues = analyzer.analyze(Path("myapp/runner.py"), dangerous_code)
        # shell=True has high confidence, should be reported
        assert len(dangerous_issues) > 0
        assert any(i.rule_id == "SEC005" for i in dangerous_issues)
