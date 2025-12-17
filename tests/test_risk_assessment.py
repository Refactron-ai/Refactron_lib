"""Tests for advanced risk assessment module."""

import ast
import tempfile
from pathlib import Path

import pytest

from refactron.core.risk_assessment import (
    ChangeType,
    RiskAssessor,
    RiskFactors,
    RiskLevel,
)


class TestRiskFactors:
    """Test RiskFactors dataclass."""

    def test_risk_factors_initialization(self):
        """Test creating risk factors with default values."""
        factors = RiskFactors()
        assert factors.impact_scope == 0.0
        assert factors.change_type_risk == 0.0
        assert factors.test_coverage_risk == 0.0
        assert factors.dependency_risk == 0.0
        assert factors.complexity_risk == 0.0
        assert factors.affected_functions == []
        assert factors.affected_files == []
        assert factors.has_tests is False

    def test_risk_factors_to_dict(self):
        """Test converting risk factors to dictionary."""
        factors = RiskFactors(
            impact_scope=0.5,
            change_type_risk=0.3,
            test_coverage_risk=0.8,
            dependency_risk=0.2,
            complexity_risk=0.4,
            affected_functions=["test_func"],
            has_tests=True,
        )

        result = factors.to_dict()
        assert result["impact_scope"] == 0.5
        assert result["change_type_risk"] == 0.3
        assert result["test_coverage_risk"] == 0.8
        assert result["dependency_risk"] == 0.2
        assert result["complexity_risk"] == 0.4
        assert result["affected_functions"] == ["test_func"]
        assert result["has_tests"] is True


class TestRiskAssessor:
    """Test RiskAssessor functionality."""

    def test_risk_assessor_initialization(self):
        """Test creating a risk assessor."""
        assessor = RiskAssessor()
        assert assessor.project_root is not None

    def test_calculate_risk_score_basic(self):
        """Test basic risk score calculation."""
        assessor = RiskAssessor()

        code = """
def simple_function():
    return 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            risk_score, risk_factors = assessor.calculate_risk_score(
                file_path=temp_file,
                source_code=code,
                change_type=ChangeType.RENAMING,
                affected_lines=[1, 2],
            )

            assert 0.0 <= risk_score <= 1.0
            assert isinstance(risk_factors, RiskFactors)
            assert risk_factors.change_type_risk == 0.1  # RENAMING weight
        finally:
            temp_file.unlink()

    def test_calculate_risk_score_api_change(self):
        """Test risk score for API changes."""
        assessor = RiskAssessor()

        code = """
def api_function(param1, param2, param3):
    return param1 + param2 + param3
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            risk_score, risk_factors = assessor.calculate_risk_score(
                file_path=temp_file,
                source_code=code,
                change_type=ChangeType.API_CHANGE,
                affected_lines=[1, 2],
            )

            assert risk_score > 0.3  # API changes are higher risk
            assert risk_factors.change_type_risk == 0.7  # API_CHANGE weight
        finally:
            temp_file.unlink()

    def test_impact_scope_calculation(self):
        """Test impact scope calculation."""
        assessor = RiskAssessor()

        code = """
def func1():
    pass

def func2():
    pass

def func3():
    pass
"""

        # Test affecting one function out of three
        impact = assessor._calculate_impact_scope(
            file_path=Path("test.py"),
            source_code=code,
            affected_lines=[1, 2, 3],
        )

        assert 0.0 <= impact <= 1.0
        # Should have moderate impact (1 of 3 functions)
        assert impact < 0.8

    def test_test_coverage_risk_no_tests(self):
        """Test test coverage risk when no test file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            source_file = tmppath / "module.py"
            source_file.write_text("def test(): pass")

            assessor = RiskAssessor(project_root=tmppath)
            risk = assessor._calculate_test_coverage_risk(source_file)

            # Should be high risk with no test file
            assert risk >= 0.5

    def test_test_coverage_risk_with_tests(self):
        """Test test coverage risk when test file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create source file
            source_file = tmppath / "module.py"
            source_file.write_text("def func(): pass")

            # Create test file
            test_file = tmppath / "test_module.py"
            test_file.write_text("def test_func(): assert True")

            assessor = RiskAssessor(project_root=tmppath)
            risk = assessor._calculate_test_coverage_risk(source_file)

            # Should be lower risk with test file
            assert risk < 0.8

    def test_dependency_risk_calculation(self):
        """Test dependency risk calculation."""
        assessor = RiskAssessor()

        # Code with few dependencies
        simple_code = """
def simple():
    return 1 + 1
"""

        risk_low = assessor._calculate_dependency_risk(
            file_path=Path("test.py"),
            source_code=simple_code,
            affected_lines=[1],
        )

        # Code with many dependencies
        complex_code = """
import os
import sys
import json
import requests
from pathlib import Path

def complex():
    os.path.exists('.')
    sys.exit(0)
    json.loads('{}')
    requests.get('url')
    Path('.').exists()
"""

        risk_high = assessor._calculate_dependency_risk(
            file_path=Path("test.py"),
            source_code=complex_code,
            affected_lines=[1],
        )

        # More dependencies should mean higher risk
        assert risk_high > risk_low

    def test_complexity_risk_calculation(self):
        """Test complexity risk calculation."""
        assessor = RiskAssessor()

        # Simple code
        simple_code = """
def simple():
    return 42
"""

        risk_low = assessor._calculate_complexity_risk(simple_code, affected_lines=None)

        # Complex code with many control structures
        complex_code = """
def complex():
    if x:
        for i in range(10):
            while y:
                try:
                    if z:
                        with open('f') as f:
                            if a:
                                for j in range(5):
                                    pass
                except Exception:
                    pass
"""

        risk_high = assessor._calculate_complexity_risk(complex_code, affected_lines=None)

        # More complexity should mean higher risk
        assert risk_high > risk_low

    def test_weighted_risk_calculation(self):
        """Test weighted overall risk calculation."""
        assessor = RiskAssessor()

        # Create risk factors with known values
        factors = RiskFactors(
            impact_scope=0.5,
            change_type_risk=0.7,  # 30% weight
            test_coverage_risk=0.8,  # 25% weight
            dependency_risk=0.3,  # 20% weight
            complexity_risk=0.4,  # 10% weight
        )

        risk = assessor._calculate_weighted_risk(factors)

        # Should be weighted average
        expected = (0.7 * 0.30) + (0.8 * 0.25) + (0.3 * 0.20) + (0.5 * 0.15) + (0.4 * 0.10)
        assert abs(risk - expected) < 0.01

    def test_get_risk_level(self):
        """Test risk level categorization."""
        assessor = RiskAssessor()

        assert assessor.get_risk_level(0.1) == RiskLevel.SAFE
        assert assessor.get_risk_level(0.4) == RiskLevel.LOW
        assert assessor.get_risk_level(0.6) == RiskLevel.MODERATE
        assert assessor.get_risk_level(0.8) == RiskLevel.HIGH
        assert assessor.get_risk_level(0.95) == RiskLevel.CRITICAL

    def test_change_type_weights(self):
        """Test that change type weights are properly defined."""
        assert RiskAssessor.CHANGE_TYPE_WEIGHTS[ChangeType.RENAMING] == 0.1
        assert RiskAssessor.CHANGE_TYPE_WEIGHTS[ChangeType.EXTRACTION] == 0.3
        assert RiskAssessor.CHANGE_TYPE_WEIGHTS[ChangeType.RESTRUCTURING] == 0.6
        assert RiskAssessor.CHANGE_TYPE_WEIGHTS[ChangeType.API_CHANGE] == 0.7
        assert RiskAssessor.CHANGE_TYPE_WEIGHTS[ChangeType.LOGIC_CHANGE] == 0.8

    def test_count_affected_functions(self):
        """Test counting functions affected by changes."""
        assessor = RiskAssessor()

        code = """
def func1():
    pass

def func2():
    pass

def func3():
    pass
"""

        tree = ast.parse(code)

        # Lines affecting only func1 (lines 1-2)
        affected = assessor._count_affected_functions(tree, [1, 2])
        assert len(affected) == 1
        assert "func1" in affected

        # Lines affecting func1 and func2 (lines 1-5)
        affected = assessor._count_affected_functions(tree, [1, 2, 3, 4, 5])
        assert len(affected) == 2

    def test_count_total_functions(self):
        """Test counting total functions in module."""
        assessor = RiskAssessor()

        code = """
def func1():
    pass

def func2():
    pass

class MyClass:
    def method1(self):
        pass
"""

        tree = ast.parse(code)

        count = assessor._count_total_functions(tree)
        assert count == 3  # func1, func2, method1

    def test_analyze_dependency_impact(self):
        """Test analyzing dependency impact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create source file
            source_file = tmppath / "module.py"
            source_file.write_text("def my_function(): pass")

            # Create file that imports and calls the function
            dependent_file = tmppath / "dependent.py"
            dependent_file.write_text("from module import my_function\nresult = my_function()")

            # Create test file
            test_file = tmppath / "test_module.py"
            test_file.write_text("from module import my_function\nmy_function()")

            assessor = RiskAssessor(project_root=tmppath)
            impact = assessor.analyze_dependency_impact(source_file, "my_function")

            # Should find dependent files in specific categories based on test setup
            # We created dependent.py which imports the module
            assert len(impact["importing_files"]) > 0, "Should find importing files"
            # We created test_module.py which should be detected as a test
            assert len(impact["dependent_tests"]) > 0, "Should find dependent test files"
            # Calling functions should find the dependent file that uses my_function
            assert len(impact["calling_functions"]) > 0, "Should find calling functions"

    def test_find_test_file(self):
        """Test finding corresponding test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create source file
            source_file = tmppath / "module.py"
            source_file.write_text("pass")

            # Create test file with standard naming
            test_file = tmppath / "test_module.py"
            test_file.write_text("pass")

            assessor = RiskAssessor(project_root=tmppath)
            found = assessor._find_test_file(source_file)

            assert found is not None
            assert found.exists()
            assert "test" in found.name

    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        assessor = RiskAssessor()

        invalid_code = "def broken function(:"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_file = Path(f.name)

        try:
            # Should not raise exception
            risk_score, risk_factors = assessor.calculate_risk_score(
                file_path=temp_file,
                source_code=invalid_code,
                change_type=ChangeType.RENAMING,
            )

            # Should return moderate risk for unknown code
            assert 0.0 <= risk_score <= 1.0
        finally:
            temp_file.unlink()


class TestChangeType:
    """Test ChangeType enum."""

    def test_change_type_values(self):
        """Test that change types have correct values."""
        assert ChangeType.RENAMING.value == "renaming"
        assert ChangeType.EXTRACTION.value == "extraction"
        assert ChangeType.RESTRUCTURING.value == "restructuring"
        assert ChangeType.API_CHANGE.value == "api_change"
        assert ChangeType.LOGIC_CHANGE.value == "logic_change"


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_risk_level_values(self):
        """Test that risk levels have correct values."""
        assert RiskLevel.SAFE.value == "safe"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MODERATE.value == "moderate"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
