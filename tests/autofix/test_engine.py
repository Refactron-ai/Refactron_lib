"""Tests for auto-fix engine."""

from pathlib import Path

import pytest

from refactron.autofix.engine import AutoFixEngine, BaseFixer
from refactron.autofix.models import FixResult, FixRiskLevel
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class TestAutoFixEngine:
    """Test suite for AutoFixEngine."""

    def test_engine_initialization(self):
        """Test engine can be initialized."""
        engine = AutoFixEngine()
        assert engine.safety_level == FixRiskLevel.SAFE
        assert isinstance(engine.fixers, dict)
        assert len(engine.fixers) > 0  # Should have registered fixers

    def test_fixers_registered(self):
        """Test that fixers are properly registered."""
        engine = AutoFixEngine()
        assert "remove_unused_imports" in engine.fixers
        assert "extract_magic_numbers" in engine.fixers
        assert "add_docstrings" in engine.fixers
        assert "remove_dead_code" in engine.fixers
        assert "fix_type_hints" in engine.fixers

    def test_can_fix_with_valid_rule_id(self):
        """Test can_fix returns True for registered fixers."""
        engine = AutoFixEngine()
        issue = CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.WARNING,
            message="Unused import",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="remove_unused_imports",
        )
        assert engine.can_fix(issue) is True

    def test_can_fix_with_invalid_rule_id(self):
        """Test can_fix returns False for unknown rule IDs."""
        engine = AutoFixEngine()
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.INFO,
            message="Test issue",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="unknown_rule_id",
        )
        assert engine.can_fix(issue) is False

    def test_can_fix_with_no_rule_id(self):
        """Test can_fix returns False when rule_id is None."""
        engine = AutoFixEngine()
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.INFO,
            message="Test issue",
            file_path=Path("test.py"),
            line_number=1,
            rule_id=None,
        )
        assert engine.can_fix(issue) is False

    def test_fix_returns_failure_for_unknown_issue(self):
        """Test fix returns failure for unknown issue types."""
        engine = AutoFixEngine()
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.INFO,
            message="Test issue",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="unknown_fixer",
        )
        result = engine.fix(issue, "test code")
        assert result.success is False
        assert "No fixer available" in result.reason

    def test_fix_respects_safety_level(self):
        """Test that high-risk fixes are blocked."""
        # Set safety level to SAFE (0.0)
        engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)

        # Try to fix with a moderate risk fixer (0.2)
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.WARNING,
            message="Magic number",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="extract_magic_numbers",  # This has risk_score=0.2
            metadata={"value": 42},
        )

        code = "x = 42"
        result = engine.fix(issue, code, preview=True)

        # Should be blocked because risk (0.2) > safety (0.0)
        assert result.success is False
        assert "risk level" in result.reason.lower()

    def test_fix_allows_safe_fixes(self):
        """Test that safe fixes are allowed."""
        engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)

        # Use a safe fixer (0.0 risk)
        issue = CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.WARNING,
            message="Unused import",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="remove_unused_imports",
        )

        code = "import os\n\nprint('hello')"
        result = engine.fix(issue, code, preview=True)

        # Should succeed because risk (0.0) <= safety (0.0)
        assert result.success is True

    def test_fix_all(self):
        """Test fixing multiple issues."""
        engine = AutoFixEngine()

        issues = [
            CodeIssue(
                category=IssueCategory.STYLE,
                level=IssueLevel.WARNING,
                message="Unused import",
                file_path=Path("test.py"),
                line_number=1,
                rule_id="remove_unused_imports",
            ),
            CodeIssue(
                category=IssueCategory.DEAD_CODE,
                level=IssueLevel.WARNING,
                message="Dead code",
                file_path=Path("test.py"),
                line_number=3,
                rule_id="remove_dead_code",
            ),
        ]

        code = "import os\n\nprint('unreachable')"
        results = engine.fix_all(issues, code, preview=True)

        assert len(results) == 2
        assert all(isinstance(r, FixResult) for r in results.values())


class TestBaseFixer:
    """Test suite for BaseFixer."""

    def test_fixer_initialization(self):
        """Test fixer can be initialized."""
        fixer = BaseFixer(name="test_fixer", risk_score=0.5)
        assert fixer.name == "test_fixer"
        assert fixer.risk_score == 0.5

    def test_preview_not_implemented(self):
        """Test preview raises NotImplementedError."""
        fixer = BaseFixer(name="test")
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.INFO,
            message="Test",
            file_path=Path("test.py"),
            line_number=1,
        )

        with pytest.raises(NotImplementedError):
            fixer.preview(issue, "code")

    def test_apply_not_implemented(self):
        """Test apply raises NotImplementedError."""
        fixer = BaseFixer(name="test")
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.INFO,
            message="Test",
            file_path=Path("test.py"),
            line_number=1,
        )

        with pytest.raises(NotImplementedError):
            fixer.apply(issue, "code")
