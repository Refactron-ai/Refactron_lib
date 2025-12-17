"""Advanced risk assessment for refactoring operations."""

import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ChangeType(Enum):
    """Type of refactoring change."""

    RENAMING = "renaming"  # Simple renaming - lowest risk
    EXTRACTION = "extraction"  # Extracting code to new location
    RESTRUCTURING = "restructuring"  # Major structural changes
    API_CHANGE = "api_change"  # Changes to function signatures
    LOGIC_CHANGE = "logic_change"  # Changes to control flow or logic


class RiskLevel(Enum):
    """Risk level categories."""

    SAFE = "safe"  # 0.0 - 0.3
    LOW = "low"  # 0.3 - 0.5
    MODERATE = "moderate"  # 0.5 - 0.7
    HIGH = "high"  # 0.7 - 0.9
    CRITICAL = "critical"  # 0.9 - 1.0


@dataclass
class RiskFactors:
    """Individual risk factors for a refactoring operation."""

    impact_scope: float = 0.0  # 0.0-1.0: How many parts of code affected
    change_type_risk: float = 0.0  # 0.0-1.0: Risk based on change type
    test_coverage_risk: float = 0.0  # 0.0-1.0: Risk from low test coverage
    dependency_risk: float = 0.0  # 0.0-1.0: Risk from breaking dependencies
    complexity_risk: float = 0.0  # 0.0-1.0: Risk from code complexity

    # Metadata for detailed analysis
    affected_functions: List[str] = field(default_factory=list)
    affected_files: List[Path] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    has_tests: bool = False
    test_file_exists: bool = False

    def to_dict(self) -> Dict:
        """Convert risk factors to dictionary."""
        return {
            "impact_scope": round(self.impact_scope, 3),
            "change_type_risk": round(self.change_type_risk, 3),
            "test_coverage_risk": round(self.test_coverage_risk, 3),
            "dependency_risk": round(self.dependency_risk, 3),
            "complexity_risk": round(self.complexity_risk, 3),
            "affected_functions": self.affected_functions,
            "affected_files": [str(f) for f in self.affected_files],
            "dependencies": self.dependencies,
            "has_tests": self.has_tests,
            "test_file_exists": self.test_file_exists,
        }


class RiskAssessor:
    """Advanced risk assessment for refactoring operations."""

    CHANGE_TYPE_WEIGHTS = {
        ChangeType.RENAMING: 0.1,
        ChangeType.EXTRACTION: 0.3,
        ChangeType.RESTRUCTURING: 0.6,
        ChangeType.API_CHANGE: 0.7,
        ChangeType.LOGIC_CHANGE: 0.8,
    }

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize risk assessor.

        Args:
            project_root: Root directory of the project for dependency analysis
        """
        self.project_root = project_root or Path.cwd()

    def calculate_risk_score(
        self,
        file_path: Path,
        source_code: str,
        change_type: ChangeType,
        affected_lines: Optional[List[int]] = None,
        operation_description: str = "",
    ) -> tuple[float, RiskFactors]:
        """Calculate comprehensive risk score for a refactoring operation.

        Args:
            file_path: Path to file being refactored
            source_code: Current source code
            change_type: Type of change being made
            affected_lines: Lines of code being changed
            operation_description: Description of the operation

        Returns:
            Tuple of (overall_risk_score, detailed_risk_factors)
        """
        risk_factors = RiskFactors()

        # Calculate individual risk factors
        risk_factors.impact_scope = self._calculate_impact_scope(
            file_path, source_code, affected_lines
        )
        risk_factors.change_type_risk = self.CHANGE_TYPE_WEIGHTS.get(change_type, 0.5)
        risk_factors.test_coverage_risk = self._calculate_test_coverage_risk(file_path)
        risk_factors.dependency_risk = self._calculate_dependency_risk(
            file_path, source_code, affected_lines
        )
        risk_factors.complexity_risk = self._calculate_complexity_risk(source_code, affected_lines)

        # Calculate weighted overall risk score
        overall_risk = self._calculate_weighted_risk(risk_factors)

        return overall_risk, risk_factors

    def _calculate_impact_scope(
        self,
        file_path: Path,
        source_code: str,
        affected_lines: Optional[List[int]] = None,
    ) -> float:
        """Calculate how much of the code is affected by the change.

        Returns:
            0.0-1.0 where 1.0 means high impact
        """
        try:
            tree = ast.parse(source_code)
            total_lines = len(source_code.split("\n"))

            if affected_lines:
                # Calculate percentage of file affected
                affected_percentage = len(affected_lines) / max(total_lines, 1)

                # Count affected functions/classes
                affected_funcs = self._count_affected_functions(tree, affected_lines)
                total_funcs = self._count_total_functions(tree)

                if total_funcs > 0:
                    func_percentage = len(affected_funcs) / total_funcs
                    # Weight function impact higher than line impact
                    impact = (affected_percentage * 0.3) + (func_percentage * 0.7)
                else:
                    LINE_IMPACT_WEIGHT = 0.3
                    FUNCTION_IMPACT_WEIGHT = 0.7
                    impact = (affected_percentage * LINE_IMPACT_WEIGHT) + (
                        func_percentage * FUNCTION_IMPACT_WEIGHT
                    )

                return min(impact, 1.0)
            else:
                # If no specific lines provided, assume moderate impact
                return 0.5

        except SyntaxError:
            return 0.5  # Unknown, assume moderate risk

    def _count_affected_functions(self, tree: ast.AST, affected_lines: List[int]) -> List[str]:
        """Count and list functions affected by the change."""
        affected = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function overlaps with affected lines
                func_start = node.lineno
                func_end = getattr(node, "end_lineno", func_start + 10)

                if any(func_start <= line <= func_end for line in affected_lines):
                    affected.append(node.name)

        return affected

    def _count_total_functions(self, tree: ast.AST) -> int:
        """Count total number of functions in the module."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                count += 1
        return count

    def _calculate_test_coverage_risk(self, file_path: Path) -> float:
        """Calculate risk based on test coverage.

        Returns:
            0.0-1.0 where 1.0 means high risk (no tests)
        """
        # Check if corresponding test file exists
        test_file = self._find_test_file(file_path)

        if test_file and test_file.exists():
            # Test file exists - lower risk
            # Check if tests are comprehensive by looking at file size
            try:
                test_size = test_file.stat().st_size
                source_size = file_path.stat().st_size

                if test_size >= source_size * 0.5:
                    # Good test coverage
                    return 0.1
                elif test_size >= source_size * 0.2:
                    # Moderate test coverage
                    return 0.3
                else:
                    # Minimal tests
                    return 0.6
            except Exception:
                return 0.5
        else:
            # No test file found - higher risk
            return 0.8

    def _find_test_file(self, file_path: Path) -> Optional[Path]:
        """Find corresponding test file for a source file."""
        # Common test patterns
        file_name = file_path.stem
        file_dir = file_path.parent

        # Look for test files in common locations
        test_patterns = [
            file_dir / f"test_{file_name}.py",
            file_dir / f"{file_name}_test.py",
            file_dir.parent / "tests" / f"test_{file_name}.py",
            self.project_root / "tests" / f"test_{file_name}.py",
        ]

        for test_path in test_patterns:
            if test_path.exists():
                return test_path

        return None

    def _calculate_dependency_risk(
        self,
        file_path: Path,
        source_code: str,
        affected_lines: Optional[List[int]] = None,
    ) -> float:
        """Calculate risk based on dependencies that might break.

        Returns:
            0.0-1.0 where 1.0 means high risk (many dependencies)
        """
        try:
            tree = ast.parse(source_code)

            # Count imports (external dependencies)
            import_count = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1

            # Count function calls (internal dependencies)
            call_count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_count += 1

            # Calculate dependency risk based on counts
            # More dependencies = higher risk
            total_deps = import_count + (call_count * 0.1)  # Weight imports more

            if total_deps < 5:
                return 0.1
            elif total_deps < 15:
                return 0.3
            elif total_deps < 30:
                return 0.5
            else:
                return 0.7

        except SyntaxError:
            return 0.5  # Unknown, assume moderate risk

    def _calculate_complexity_risk(
        self,
        source_code: str,
        affected_lines: Optional[List[int]] = None,
    ) -> float:
        """Calculate risk based on code complexity.

        Returns:
            0.0-1.0 where 1.0 means high risk (very complex code)
        """
        try:
            tree = ast.parse(source_code)

            # Count complexity indicators
            complexity_score = 0

            for node in ast.walk(tree):
                # Control flow increases complexity
                if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                    complexity_score += 1
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    complexity_score += 2
                elif isinstance(node, ast.Lambda):
                    complexity_score += 1

            # Normalize to 0-1 range
            # Assume 50+ control flow statements is very complex
            normalized = min(complexity_score / 50.0, 1.0)

            return normalized

        except SyntaxError:
            return 0.5  # Unknown, assume moderate risk

    def _calculate_weighted_risk(self, risk_factors: RiskFactors) -> float:
        """Calculate overall risk score using weighted factors.

        Weights:
        - Change type: 30% (most important)
        - Test coverage: 25%
        - Dependency: 20%
        - Impact scope: 15%
        - Complexity: 10%
        """
        weights = {
            "change_type": 0.30,
            "test_coverage": 0.25,
            "dependency": 0.20,
            "impact_scope": 0.15,
            "complexity": 0.10,
        }

        overall_risk = (
            risk_factors.change_type_risk * weights["change_type"]
            + risk_factors.test_coverage_risk * weights["test_coverage"]
            + risk_factors.dependency_risk * weights["dependency"]
            + risk_factors.impact_scope * weights["impact_scope"]
            + risk_factors.complexity_risk * weights["complexity"]
        )

        return round(overall_risk, 3)

    def get_risk_level(self, risk_score: float) -> RiskLevel:
        """Get risk level category from score."""
        if risk_score < 0.3:
            return RiskLevel.SAFE
        elif risk_score < 0.5:
            return RiskLevel.LOW
        elif risk_score < 0.7:
            return RiskLevel.MODERATE
        elif risk_score < 0.9:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def analyze_dependency_impact(
        self, file_path: Path, function_name: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Analyze what breaks if this refactoring is applied.

        Args:
            file_path: File being refactored
            function_name: Specific function being changed (optional)

        Returns:
            Dictionary with potential breakage points
        """
        impact = {
            "importing_files": [],
            "calling_functions": [],
            "dependent_tests": [],
        }

        # Find files that import this module
        if self.project_root.exists():
            for py_file in self.project_root.rglob("*.py"):
                if py_file == file_path:
                    continue

                try:
                    content = py_file.read_text()
                    # Simple check for imports
                    if file_path.stem in content:
                        impact["importing_files"].append(
                            str(py_file.relative_to(self.project_root))
                        )

                    # Check for function calls if specified
                    if function_name and f"{function_name}(" in content:
                        impact["calling_functions"].append(
                            str(py_file.relative_to(self.project_root))
                        )

                except Exception:
                    continue

        # Find dependent test files
        test_file = self._find_test_file(file_path)
        if test_file:
            impact["dependent_tests"].append(str(test_file))

        return impact
