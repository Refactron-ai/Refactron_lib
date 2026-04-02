"""
Day 1 — Exception isolation for TaintAnalyzer / CFGBuilder.

Tests verify that:
- A TaintAnalyzer crash on a specific file produces an AnalysisSkipWarning, not an exception
- A CFGBuilder crash (upstream of TaintAnalyzer) is also isolated
- When >10% of files skip semantic analysis, a summary warning is added to the result
- Regular analyzers still run and find issues even when semantic analysis is skipped
"""

from pathlib import Path
from unittest.mock import patch

from refactron import Refactron
from refactron.core.models import AnalysisSkipWarning  # noqa: F401 (import drives the test fail)

# ─── helpers ────────────────────────────────────────────────────────────────


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    f = tmp_path / name
    f.write_text(content)
    return f


# ─── tests ──────────────────────────────────────────────────────────────────


def test_taint_skip_produces_warning_not_crash(tmp_path):
    """TaintAnalyzer.analyze() crashing on a file must produce a SkipWarning, not raise."""
    py_file = _write_py(tmp_path, "sample.py", "x = 1\n")

    with patch(
        "refactron.core.refactron.TaintAnalyzer.analyze",
        side_effect=RuntimeError("Unsupported AST node at line 47"),
    ):
        result = Refactron().analyze(py_file)

    assert not isinstance(result, Exception)
    assert len(result.semantic_skip_warnings) == 1

    warn = result.semantic_skip_warnings[0]
    assert warn.analyzer_name == "taint"
    assert "Unsupported AST node" in warn.reason
    assert warn.file_path == py_file


def test_cfg_build_failure_skip_produces_warning_not_crash(tmp_path):
    """CFGBuilder.build_from_source() crashing is isolated to a SkipWarning."""
    py_file = _write_py(tmp_path, "sample.py", "x = 1\n")

    with patch(
        "refactron.core.refactron.CFGBuilder.build_from_source",
        side_effect=RuntimeError("Unsupported node: MatchAs"),
    ):
        result = Refactron().analyze(py_file)

    assert not isinstance(result, Exception)
    assert len(result.semantic_skip_warnings) == 1

    warn = result.semantic_skip_warnings[0]
    assert warn.analyzer_name == "taint"
    assert "Unsupported node" in warn.reason


def test_skip_rate_over_10pct_shows_summary(tmp_path):
    """When >10% of files have semantic analysis skipped, result.semantic_skip_summary is set."""
    for i in range(10):
        _write_py(tmp_path, f"file_{i}.py", f"x = {i}\n")

    with patch(
        "refactron.core.refactron.TaintAnalyzer.analyze",
        side_effect=RuntimeError("crash"),
    ):
        result = Refactron().analyze(tmp_path)

    # 10/10 = 100% skip rate → summary must be present
    assert result.semantic_skip_summary is not None
    summary = result.semantic_skip_summary
    assert "10" in summary or "100%" in summary


def test_skip_rate_under_threshold_has_no_summary(tmp_path):
    """When only 1 of 20 files skips semantic analysis, no summary is shown (skip_rate <= 10%)."""
    for i in range(20):
        _write_py(tmp_path, f"file_{i}.py", f"x = {i}\n")

    call_count = {"n": 0}

    def maybe_crash(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("one file fails")
        return []  # all others succeed

    with patch("refactron.core.refactron.TaintAnalyzer.analyze", side_effect=maybe_crash):
        result = Refactron().analyze(tmp_path)

    # 1/20 = 5% → below 10% threshold → no summary
    assert result.semantic_skip_summary is None
    # But we should still have the single warning
    assert len(result.semantic_skip_warnings) == 1


def test_healthy_analyzers_unaffected_by_isolation(tmp_path):
    """Regular code-smell / complexity analyzers still run even if semantic analysis fails."""
    # 42 is a magic number → CodeSmellAnalyzer should flag it
    py_file = _write_py(
        tmp_path,
        "sample.py",
        "def compute(x):\n    return x * 42\n",
    )

    with patch(
        "refactron.core.refactron.TaintAnalyzer.analyze",
        side_effect=RuntimeError("crash"),
    ):
        result = Refactron().analyze(py_file)

    # Regular analyzers must still produce issues
    assert result.total_issues > 0

    # Semantic analysis produced a skip warning
    assert len(result.semantic_skip_warnings) == 1
