"""Analyzer for code smells and anti-patterns."""

import ast
from pathlib import Path
from typing import List, Set

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class CodeSmellAnalyzer(BaseAnalyzer):
    """Detects common code smells and anti-patterns."""

    @property
    def name(self) -> str:
        return "code_smells"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for smells and anti-patterns.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of detected code smell issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various code smells
            issues.extend(self._check_too_many_parameters(tree, file_path))
            issues.extend(self._check_nested_depth(tree, file_path, source_code))
            issues.extend(self._check_duplicate_code(tree, file_path))
            issues.extend(self._check_magic_numbers(tree, file_path))
            issues.extend(self._check_missing_docstrings(tree, file_path))

        except SyntaxError as e:
            issue = CodeIssue(
                category=IssueCategory.CODE_SMELL,
                level=IssueLevel.ERROR,
                message=f"Syntax error: {str(e)}",
                file_path=file_path,
                line_number=getattr(e, "lineno", 1),
            )
            issues.append(issue)

        return issues

    def _check_too_many_parameters(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for functions with too many parameters."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args)

                if param_count > self.config.max_parameters:
                    issue = CodeIssue(
                        category=IssueCategory.CODE_SMELL,
                        level=IssueLevel.WARNING,
                        message=f"Function '{node.name}' has too many parameters ({param_count})",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=(
                            f"Consider using a configuration object or breaking down the function. "
                            f"Current: {param_count} parameters, "
                            f"recommended: ≤ {self.config.max_parameters}"
                        ),
                        rule_id="S001",
                        metadata={"parameter_count": param_count},
                    )
                    issues.append(issue)

        return issues

    def _check_nested_depth(
        self,
        tree: ast.AST,
        file_path: Path,
        source_code: str,
    ) -> List[CodeIssue]:
        """Check for deeply nested code structures."""
        issues = []
        max_depth = 4

        def get_nesting_depth(node: ast.AST, depth: int = 0) -> int:
            """Calculate maximum nesting depth."""
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth += 1

            max_child_depth = depth
            for child in ast.iter_child_nodes(node):
                child_depth = get_nesting_depth(child, depth)
                max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = get_nesting_depth(node)

                if depth > max_depth:
                    issue = CodeIssue(
                        category=IssueCategory.CODE_SMELL,
                        level=IssueLevel.WARNING,
                        message=f"Function '{node.name}' has deep nesting (depth: {depth})",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider extracting nested logic into separate functions "
                        "or using early returns to reduce nesting.",
                        rule_id="S002",
                        metadata={"nesting_depth": depth},
                    )
                    issues.append(issue)

        return issues

    def _check_duplicate_code(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for potential duplicate code."""
        issues = []

        # Simple heuristic: look for multiple functions with similar names
        function_names: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.append(node.name)

        # Check for functions with numbered suffixes (potential duplication)
        base_names: Set[str] = set()
        for name in function_names:
            if name[-1].isdigit():
                base_name = name.rstrip("0123456789")
                if base_name in base_names:
                    # Found potential duplication
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith(base_name):
                                issue = CodeIssue(
                                    category=IssueCategory.CODE_SMELL,
                                    level=IssueLevel.INFO,
                                    message=f"Potential duplicate function: '{node.name}'",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    suggestion=(
                                        "Consider consolidating similar functions or using "
                                        "parameters."
                                    ),
                                    rule_id="S003",
                                )
                                issues.append(issue)
                                break
                base_names.add(base_name)

        return issues

    def _check_magic_numbers(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for magic numbers (unexplained numeric constants)."""
        issues = []

        for node in ast.walk(tree):
            # Use ast.Constant for Python 3.8+ (ast.Num is deprecated)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Ignore common acceptable numbers
                if node.value not in (0, 1, -1, 2):
                    issue = CodeIssue(
                        category=IssueCategory.CODE_SMELL,
                        level=IssueLevel.INFO,
                        message=f"Magic number found: {node.value}",
                        file_path=file_path,
                        line_number=node.lineno if hasattr(node, "lineno") else 0,
                        suggestion="Consider extracting this number into a named constant.",
                        rule_id="S004",
                        metadata={"value": node.value},
                    )
                    issues.append(issue)

        return issues

    def _check_missing_docstrings(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for missing docstrings in functions and classes."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private functions (starting with _)
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue

                docstring = ast.get_docstring(node)
                if not docstring:
                    entity_type = "Class" if isinstance(node, ast.ClassDef) else "Function"
                    issue = CodeIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        level=IssueLevel.INFO,
                        message=f"{entity_type} '{node.name}' is missing a docstring",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=(
                            f"Add a docstring to explain what this {entity_type.lower()} does."
                        ),
                        rule_id="S005",
                    )
                    issues.append(issue)

        return issues
