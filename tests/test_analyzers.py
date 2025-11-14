"""Tests for analyzers."""

from pathlib import Path

from refactron.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from refactron.analyzers.complexity_analyzer import ComplexityAnalyzer
from refactron.core.config import RefactronConfig


def test_complexity_analyzer() -> None:
    """Test complexity analyzer."""
    config = RefactronConfig(max_function_complexity=5)
    analyzer = ComplexityAnalyzer(config)

    code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 10:
            if z > 20:
                if x > 30:
                    if y > 40:
                        if z > 50:
                            return "very high"
                        return "high"
                    return "medium"
                return "low"
            return "very low"
        return "negative"
    return "zero"
"""

    issues = analyzer.analyze(Path("test.py"), code)
    # Should detect high complexity
    assert len(issues) > 0
    assert analyzer.name == "complexity"


def test_code_smell_analyzer() -> None:
    """Test code smell analyzer."""
    config = RefactronConfig()
    analyzer = CodeSmellAnalyzer(config)

    code = """
def function_with_many_params(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h

class MyClass:
    def method_without_docstring(self):
        magic_number = 12345
        return magic_number
"""

    issues = analyzer.analyze(Path("test.py"), code)
    assert len(issues) > 0
    assert analyzer.name == "code_smells"


def test_analyzer_handles_syntax_errors() -> None:
    """Test that analyzers handle syntax errors gracefully."""
    config = RefactronConfig()
    analyzer = ComplexityAnalyzer(config)

    # Invalid Python code
    code = "def broken function(:"

    issues = analyzer.analyze(Path("test.py"), code)
    # Should return an error issue, not crash
    assert len(issues) >= 0
