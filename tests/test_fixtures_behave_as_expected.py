"""
Day 4 — Verify that the test fixtures contain the expected issues.

These fixtures are the ground truth for the Verification Engine (Days 6-15).
Each fixture is designed to trigger specific analyzer rule_ids so the
engine can prove it blocks bad transforms and allows safe ones.
"""

from pathlib import Path

import pytest

from refactron.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from refactron.analyzers.complexity_analyzer import ComplexityAnalyzer
from refactron.analyzers.dead_code_analyzer import DeadCodeAnalyzer
from refactron.analyzers.dependency_analyzer import DependencyAnalyzer
from refactron.core.config import RefactronConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def config() -> RefactronConfig:
    return RefactronConfig()


# ─── fixture_clean.py ────────────────────────────────────────────────────────


def test_clean_fixture_has_zero_issues(config):
    """fixture_clean.py must produce zero issues from code-smell & dead-code analyzers."""
    source = (FIXTURES_DIR / "fixture_clean.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_clean.py"

    smell_issues = CodeSmellAnalyzer(config).analyze(path, source)
    dead_issues = DeadCodeAnalyzer(config).analyze(path, source)

    all_issues = smell_issues + dead_issues
    assert (
        len(all_issues) == 0
    ), f"fixture_clean.py must have zero issues, got {len(all_issues)}: " + ", ".join(
        str(i) for i in all_issues
    )


# ─── fixture_safe_extract.py ─────────────────────────────────────────────────


def test_safe_fixture_has_magic_number_issue(config):
    """fixture_safe_extract.py must trigger at least one magic-number issue (S004)."""
    source = (FIXTURES_DIR / "fixture_safe_extract.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_safe_extract.py"

    issues = CodeSmellAnalyzer(config).analyze(path, source)
    magic_issues = [i for i in issues if i.rule_id == "S004"]
    assert len(magic_issues) >= 1, "Expected at least one magic number issue (S004)"


def test_safe_fixture_has_unused_import(config):
    """fixture_safe_extract.py must trigger at least one unused-import issue (DEP001)."""
    source = (FIXTURES_DIR / "fixture_safe_extract.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_safe_extract.py"

    issues = DependencyAnalyzer(config).analyze(path, source)
    unused = [i for i in issues if i.rule_id == "DEP001"]
    assert len(unused) >= 1, "Expected at least one unused import issue (DEP001)"


def test_safe_fixture_has_long_function(config):
    """fixture_safe_extract.py must trigger a function-too-long issue (C002)."""
    source = (FIXTURES_DIR / "fixture_safe_extract.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_safe_extract.py"

    issues = ComplexityAnalyzer(config).analyze(path, source)
    long_func = [i for i in issues if i.rule_id == "C002"]
    assert len(long_func) >= 1, "Expected at least one long function issue (C002)"


# ─── fixture_bad_extract.py ──────────────────────────────────────────────────


def test_bad_extract_fixture_contains_known_issues(config):
    """fixture_bad_extract.py must trigger at least one issue."""
    source = (FIXTURES_DIR / "fixture_bad_extract.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_bad_extract.py"

    smell_issues = CodeSmellAnalyzer(config).analyze(path, source)
    dead_issues = DeadCodeAnalyzer(config).analyze(path, source)

    all_issues = smell_issues + dead_issues
    assert len(all_issues) >= 1, "fixture_bad_extract.py must have at least one issue"


# ─── fixture_import_break.py ─────────────────────────────────────────────────


def test_import_break_fixture_has_unused_import(config):
    """fixture_import_break.py must have an import the autofix would try to remove."""
    source = (FIXTURES_DIR / "fixture_import_break.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_import_break.py"

    issues = DependencyAnalyzer(config).analyze(path, source)
    unused = [i for i in issues if i.rule_id == "DEP001"]
    assert len(unused) >= 1, "Expected at least one unused-import to trigger autofix"


# ─── fixture_test_break.py ───────────────────────────────────────────────────


def test_test_break_fixture_has_issues(config):
    """fixture_test_break.py must have at least one issue."""
    source = (FIXTURES_DIR / "fixture_test_break.py").read_text(encoding="utf-8")
    path = FIXTURES_DIR / "fixture_test_break.py"

    smell_issues = CodeSmellAnalyzer(config).analyze(path, source)
    dep_issues = DependencyAnalyzer(config).analyze(path, source)

    all_issues = smell_issues + dep_issues
    assert len(all_issues) >= 1, "fixture_test_break.py must have at least one issue"


def test_test_break_test_actually_passes():
    """fixture_test_break_test.py must pass when run against the unmodified fixture."""
    import subprocess

    test_file = FIXTURES_DIR / "fixture_test_break_test.py"
    result = subprocess.run(
        ["python3", "-m", "pytest", str(test_file), "-x", "--no-header", "-q"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"fixture_test_break_test.py must pass against unmodified fixture.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
