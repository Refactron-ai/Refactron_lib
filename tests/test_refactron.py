"""Basic tests for Refactron core functionality."""

import os
import tempfile
from pathlib import Path

from refactron import Refactron
from refactron.core.config import RefactronConfig
from refactron.core.models import IssueLevel


def test_refactron_initialization() -> None:
    """Test Refactron can be initialized."""
    refactron = Refactron()
    assert refactron is not None
    assert refactron.config is not None


def test_refactron_with_custom_config() -> None:
    """Test Refactron with custom configuration."""
    config = RefactronConfig(max_function_complexity=5)
    refactron = Refactron(config)
    assert refactron.config.max_function_complexity == 5


def test_analyze_simple_file() -> None:
    """Test analyzing a simple Python file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def simple_function():
    '''A simple function.'''
    return 42

def complex_function(a, b, c, d, e, f):
    '''A function with too many parameters.'''
    return a + b + c + d + e + f
"""
        )
        temp_path = f.name

    try:
        refactron = Refactron()
        result = refactron.analyze(temp_path)

        assert result is not None
        assert result.total_files == 1
        assert len(result.file_metrics) == 1

        # Should detect the function with too many parameters
        assert result.total_issues > 0

    finally:
        os.unlink(temp_path)


def test_analyze_complex_file() -> None:
    """Test analyzing a file with complexity issues."""
    complex_code = """
def very_complex_function(x):
    '''A very complex function.'''
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        return "very high"
                    return "high"
                return "medium high"
            return "medium"
        return "low"
    return "negative"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(complex_code)
        temp_path = f.name

    try:
        refactron = Refactron()
        result = refactron.analyze(temp_path)

        # Should detect complexity and nesting issues
        assert result.total_issues > 0

        # Check for warning or error level issues
        warnings = result.issues_by_level(IssueLevel.WARNING)
        errors = result.issues_by_level(IssueLevel.ERROR)
        assert len(warnings) + len(errors) > 0

    finally:
        os.unlink(temp_path)


def test_refactor_preview() -> None:
    """Test refactoring in preview mode."""
    code = """
def simple():
    return 1
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        refactron = Refactron()
        result = refactron.refactor(temp_path, preview=True)

        assert result is not None
        assert result.preview_mode is True
        assert result.applied is False

    finally:
        os.unlink(temp_path)


def test_config_save_load() -> None:
    """Test saving and loading configuration."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Create and save config
        config = RefactronConfig(max_function_complexity=15)
        config.to_file(temp_path)

        # Load config
        loaded_config = RefactronConfig.from_file(temp_path)
        assert loaded_config.max_function_complexity == 15

    finally:
        os.unlink(temp_path)


def test_analyze_directory() -> None:
    """Test analyzing a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create some test files
        (tmppath / "file1.py").write_text("def func1(): pass")
        (tmppath / "file2.py").write_text("def func2(): pass")

        refactron = Refactron()
        result = refactron.analyze(tmppath)

        assert result.total_files == 2


def test_analysis_result_summary() -> None:
    """Test AnalysisResult summary generation."""
    code = """
def bad_function(a, b, c, d, e, f, g):
    if a:
        if b:
            if c:
                if d:
                    return e + f + g
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        refactron = Refactron()
        result = refactron.analyze(temp_path)
        summary = result.summary()

        assert "total_files" in summary
        assert "total_issues" in summary
        assert "critical" in summary
        assert "errors" in summary
        assert "warnings" in summary

    finally:
        os.unlink(temp_path)
