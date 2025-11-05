"""Analyzer for code complexity metrics."""

import ast
from pathlib import Path
from typing import List

from radon.complexity import cc_visit
from radon.metrics import mi_visit

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzes code complexity using cyclomatic complexity and other metrics."""

    @property
    def name(self) -> str:
        return "complexity"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze complexity of the source code.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of complexity-related issues
        """
        issues = []

        try:
            # Cyclomatic complexity
            complexity_results = cc_visit(source_code)

            for result in complexity_results:
                if result.complexity > self.config.max_function_complexity:
                    level = self._get_complexity_level(result.complexity)

                    issue = CodeIssue(
                        category=IssueCategory.COMPLEXITY,
                        level=level,
                        message=(
                            f"Function '{result.name}' has high complexity ({result.complexity})"
                        ),
                        file_path=file_path,
                        line_number=result.lineno,
                        suggestion=(
                            f"Consider breaking this function into smaller functions. "
                            f"Current complexity: {result.complexity}, "
                            f"recommended: ≤ {self.config.max_function_complexity}"
                        ),
                        rule_id="C001",
                        metadata={"complexity": result.complexity, "type": "cyclomatic"},
                    )
                    issues.append(issue)

            # Maintainability index
            try:
                mi_score = mi_visit(source_code, multi=True)
                if mi_score < 20:
                    issue = CodeIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        level=IssueLevel.WARNING,
                        message=f"Low maintainability index: {mi_score:.1f}",
                        file_path=file_path,
                        line_number=1,
                        suggestion="Consider refactoring to improve maintainability. "
                        "Score < 20 indicates difficult to maintain code.",
                        rule_id="M001",
                        metadata={"maintainability_index": mi_score},
                    )
                    issues.append(issue)
            except Exception:
                pass  # MI calculation can fail on some code

            # Function length check
            try:
                tree = ast.parse(source_code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_length = self._get_function_length(node, source_code)

                        if func_length > self.config.max_function_length:
                            issue = CodeIssue(
                                category=IssueCategory.COMPLEXITY,
                                level=IssueLevel.WARNING,
                                message=(
                                    f"Function '{node.name}' is too long ({func_length} lines)"
                                ),
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=(
                                    f"Consider breaking this function into smaller functions. "
                                    f"Current length: {func_length} lines, "
                                    f"recommended: ≤ {self.config.max_function_length} lines"
                                ),
                                rule_id="C002",
                                metadata={"length": func_length},
                            )
                            issues.append(issue)
            except SyntaxError:
                pass

        except Exception as e:
            # If analysis fails, create an error issue
            issue = CodeIssue(
                category=IssueCategory.COMPLEXITY,
                level=IssueLevel.ERROR,
                message=f"Failed to analyze complexity: {str(e)}",
                file_path=file_path,
                line_number=1,
            )
            issues.append(issue)

        return issues

    def _get_complexity_level(self, complexity: int) -> IssueLevel:
        """Determine issue level based on complexity score."""
        if complexity > 20:
            return IssueLevel.CRITICAL
        elif complexity > 15:
            return IssueLevel.ERROR
        elif complexity > self.config.max_function_complexity:
            return IssueLevel.WARNING
        return IssueLevel.INFO

    def _get_function_length(self, node: ast.FunctionDef, source_code: str) -> int:
        """Calculate the number of lines in a function."""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno - node.lineno + 1

        # Fallback: count lines in the function body
        return len(node.body)
