"""Tests for concrete fixer implementations."""

from pathlib import Path

from refactron.autofix.fixers import (
    AddDocstringsFixer,
    ExtractMagicNumbersFixer,
    FixTypeHintsFixer,
    RemoveDeadCodeFixer,
    RemoveUnusedImportsFixer,
)
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class TestRemoveUnusedImportsFixer:
    """Tests for RemoveUnusedImportsFixer."""

    def test_removes_unused_import(self):
        """Test that unused imports are removed."""
        fixer = RemoveUnusedImportsFixer()
        code = """import os
import sys
import json

print('hello')
"""
        issue = CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.WARNING,
            message="Unused imports",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="remove_unused_imports",
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert "import os" not in result.fixed
        assert "import sys" not in result.fixed
        assert "import json" not in result.fixed
        assert "print('hello')" in result.fixed

    def test_keeps_used_imports(self):
        """Test that used imports are kept."""
        fixer = RemoveUnusedImportsFixer()
        code = """import os
import sys

print(sys.version)
path = os.getcwd()
"""
        issue = CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.WARNING,
            message="Check imports",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="remove_unused_imports",
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert "import os" in result.fixed
        assert "import sys" in result.fixed

    def test_handles_from_imports(self):
        """Test handling of from imports."""
        fixer = RemoveUnusedImportsFixer()
        code = """from pathlib import Path
from typing import List
from os import getcwd

p = Path('.')
"""
        issue = CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.WARNING,
            message="Unused imports",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="remove_unused_imports",
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert "from pathlib import Path" in result.fixed
        assert "from typing import List" not in result.fixed
        assert "from os import getcwd" not in result.fixed

    def test_low_risk_score(self):
        """Test that fixer has low risk score."""
        fixer = RemoveUnusedImportsFixer()
        assert fixer.risk_score == 0.0


class TestExtractMagicNumbersFixer:
    """Tests for ExtractMagicNumbersFixer."""

    def test_extracts_magic_number(self):
        """Test magic number extraction."""
        fixer = ExtractMagicNumbersFixer()
        code = """def calculate():
    return 42
"""
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.WARNING,
            message="Magic number",
            file_path=Path("test.py"),
            line_number=2,
            rule_id="extract_magic_numbers",
            metadata={"value": 42},
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert "CONSTANT_42" in result.fixed or "42" not in result.fixed.split("\n")[-1]

    def test_risk_score(self):
        """Test that fixer has appropriate risk score."""
        fixer = ExtractMagicNumbersFixer()
        assert fixer.risk_score == 0.2


class TestAddDocstringsFixer:
    """Tests for AddDocstringsFixer."""

    def test_adds_docstring(self):
        """Test docstring addition."""
        fixer = AddDocstringsFixer()
        code = """def hello():
    print('hello')
"""
        issue = CodeIssue(
            category=IssueCategory.MAINTAINABILITY,
            level=IssueLevel.WARNING,
            message="Missing docstring",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="add_docstrings",
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert '"""' in result.fixed

    def test_risk_score(self):
        """Test that fixer has low risk score."""
        fixer = AddDocstringsFixer()
        assert fixer.risk_score == 0.1


class TestRemoveDeadCodeFixer:
    """Tests for RemoveDeadCodeFixer."""

    def test_removes_dead_code(self):
        """Test dead code removal."""
        fixer = RemoveDeadCodeFixer()
        code = """def test():
    return True
    print('unreachable')
"""
        issue = CodeIssue(
            category=IssueCategory.DEAD_CODE,
            level=IssueLevel.WARNING,
            message="Unreachable code",
            file_path=Path("test.py"),
            line_number=3,
            rule_id="remove_dead_code",
        )

        result = fixer.preview(issue, code)
        assert result.success is True
        assert "print('unreachable')" not in result.fixed

    def test_risk_score(self):
        """Test that fixer has low risk score."""
        fixer = RemoveDeadCodeFixer()
        assert fixer.risk_score == 0.1


class TestFixTypeHintsFixer:
    """Tests for FixTypeHintsFixer."""

    def test_not_yet_implemented(self):
        """Test that type hint fixer is placeholder."""
        fixer = FixTypeHintsFixer()
        code = """def add(a, b):
    return a + b
"""
        issue = CodeIssue(
            category=IssueCategory.TYPE_HINTS,
            level=IssueLevel.INFO,
            message="Missing type hints",
            file_path=Path("test.py"),
            line_number=1,
            rule_id="fix_type_hints",
        )

        result = fixer.preview(issue, code)
        assert result.success is False
        assert "not yet implemented" in result.reason.lower()

    def test_higher_risk_score(self):
        """Test that type hint fixer has higher risk score."""
        fixer = FixTypeHintsFixer()
        assert fixer.risk_score == 0.4


class TestFixerIntegration:
    """Integration tests for all fixers."""

    def test_all_fixers_have_names(self):
        """Test that all fixers have valid names."""
        fixers = [
            RemoveUnusedImportsFixer(),
            ExtractMagicNumbersFixer(),
            AddDocstringsFixer(),
            RemoveDeadCodeFixer(),
            FixTypeHintsFixer(),
        ]

        for fixer in fixers:
            assert fixer.name
            assert isinstance(fixer.name, str)
            assert len(fixer.name) > 0

    def test_all_fixers_have_risk_scores(self):
        """Test that all fixers have valid risk scores."""
        fixers = [
            RemoveUnusedImportsFixer(),
            ExtractMagicNumbersFixer(),
            AddDocstringsFixer(),
            RemoveDeadCodeFixer(),
            FixTypeHintsFixer(),
        ]

        for fixer in fixers:
            assert 0.0 <= fixer.risk_score <= 1.0
