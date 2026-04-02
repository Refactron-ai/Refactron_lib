"""
Day 3 — --dry-run flag for refactron autofix.

Tests verify that:
- generate_diff() produces a proper unified diff (or empty string when unchanged)
- fix_file() in dry_run=True mode never writes bytes to disk
- fix_file() in dry_run=True returns a diff showing proposed changes
- The fixed code returned in dry_run matches what apply would actually write
- fix_file() with dry_run=False does write the fixed content to disk
"""

from pathlib import Path

from refactron.autofix.engine import AutoFixEngine
from refactron.autofix.file_ops import generate_diff
from refactron.autofix.models import FixRiskLevel
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel

# ─── helpers ────────────────────────────────────────────────────────────────


def _trailing_ws_issue(file_path: Path) -> CodeIssue:
    return CodeIssue(
        rule_id="remove_trailing_whitespace",
        message="Trailing whitespace detected",
        file_path=file_path,
        line_number=1,
        category=IssueCategory.STYLE,
        level=IssueLevel.WARNING,
    )


# ─── generate_diff ────────────────────────────────────────────────────────────


def test_generate_diff_produces_unified_diff():
    """generate_diff() must return a unified diff string when content changes."""
    original = "x = 1\n"
    modified = "x = 2\n"
    diff = generate_diff(original, modified, "test.py")
    assert diff, "Diff must be non-empty when content changed"
    assert "@@" in diff, "Diff must contain unified diff chunk markers"


def test_generate_diff_empty_when_no_changes():
    """generate_diff() must return empty string when content is identical."""
    content = "x = 1\n"
    diff = generate_diff(content, content, "test.py")
    assert diff == "", "Diff must be empty string when content is unchanged"


def test_generate_diff_includes_filename():
    """generate_diff() must include the filename in the diff header."""
    diff = generate_diff("a = 1\n", "a = 2\n", "mymodule.py")
    assert "mymodule.py" in diff, "Diff header must include the filename"


# ─── fix_file (dry_run=True) ─────────────────────────────────────────────────


def test_dry_run_writes_no_files(tmp_path):
    """fix_file() with dry_run=True must not modify any file on disk."""
    py_file = tmp_path / "module.py"
    original_content = "x = 1   \ny = 2  \n"
    py_file.write_text(original_content, encoding="utf-8")

    engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)
    engine.fix_file(py_file, [_trailing_ws_issue(py_file)], dry_run=True)

    assert (
        py_file.read_text(encoding="utf-8") == original_content
    ), "dry_run=True must not write any bytes to disk"


def test_dry_run_returns_unified_diff(tmp_path):
    """fix_file() with dry_run=True must return a non-empty diff when changes exist."""
    py_file = tmp_path / "module.py"
    py_file.write_text("x = 1   \ny = 2  \n", encoding="utf-8")

    engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)
    _fixed_code, diff = engine.fix_file(py_file, [_trailing_ws_issue(py_file)], dry_run=True)

    assert (
        diff is not None and diff != ""
    ), "fix_file must return a non-empty diff in dry_run mode when changes exist"


def test_dry_run_returns_none_diff_when_no_changes(tmp_path):
    """fix_file() with dry_run=True must return None diff when nothing changes."""
    py_file = tmp_path / "module.py"
    py_file.write_text("x = 1\ny = 2\n", encoding="utf-8")  # No trailing whitespace

    engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)
    _fixed_code, diff = engine.fix_file(py_file, [_trailing_ws_issue(py_file)], dry_run=True)

    assert (
        diff is None or diff == ""
    ), "fix_file must return None/empty diff when no changes are made"


# ─── fix_file (apply vs dry-run consistency) ─────────────────────────────────


def test_dry_run_diff_matches_what_apply_would_write(tmp_path):
    """The fixed code returned in dry_run must match what apply actually writes."""
    content = "x = 1   \ny = 2  \n"

    # Dry-run path
    dry_file = tmp_path / "dry.py"
    dry_file.write_text(content, encoding="utf-8")
    engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)
    fixed_from_dry, _diff = engine.fix_file(dry_file, [_trailing_ws_issue(dry_file)], dry_run=True)

    # Apply path (separate file, same content)
    apply_file = tmp_path / "apply.py"
    apply_file.write_text(content, encoding="utf-8")
    engine.fix_file(apply_file, [_trailing_ws_issue(apply_file)], dry_run=False)
    applied_content = apply_file.read_text(encoding="utf-8")

    assert (
        fixed_from_dry == applied_content
    ), "dry_run fixed code must exactly match what apply writes to disk"


# ─── fix_file (dry_run=False) ────────────────────────────────────────────────


def test_apply_without_dry_run_does_write_files(tmp_path):
    """fix_file() with dry_run=False must write the fixed content to disk."""
    py_file = tmp_path / "module.py"
    original_content = "x = 1   \ny = 2  \n"
    py_file.write_text(original_content, encoding="utf-8")

    engine = AutoFixEngine(safety_level=FixRiskLevel.SAFE)
    engine.fix_file(py_file, [_trailing_ws_issue(py_file)], dry_run=False)

    written_content = py_file.read_text(encoding="utf-8")
    assert written_content != original_content, "dry_run=False must write the fixed content to disk"
    # Confirm trailing whitespace was removed
    for line in written_content.splitlines():
        assert line == line.rstrip(), f"Line still has trailing whitespace: {line!r}"
