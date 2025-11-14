"""Analyzer for performance antipatterns."""

import ast
from pathlib import Path
from typing import Dict, List, Union

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class PerformanceAnalyzer(BaseAnalyzer):
    """Detects common performance antipatterns and inefficiencies."""

    @property
    def name(self) -> str:
        return "performance"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for performance antipatterns.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of performance-related issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various performance antipatterns
            issues.extend(self._check_n_plus_one_queries(tree, file_path))
            issues.extend(self._check_inefficient_list_comprehensions(tree, file_path))
            issues.extend(self._check_unnecessary_iterations(tree, file_path))
            issues.extend(self._check_inefficient_string_concatenation(tree, file_path))
            issues.extend(self._check_redundant_list_calls(tree, file_path))

        except SyntaxError:
            pass

        return issues

    def _check_n_plus_one_queries(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for N+1 query antipattern in loops."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for database queries inside loops
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func_name = self._get_function_name(child.func)

                        # Common ORM query methods
                        query_methods = [
                            "execute",
                            "query",
                            "filter",
                            "get",
                            "select",
                            "all",
                            "first",
                            "fetchone",
                            "fetchall",
                            "find",
                            "find_one",
                        ]

                        if func_name in query_methods:
                            issue = CodeIssue(
                                category=IssueCategory.PERFORMANCE,
                                level=IssueLevel.WARNING,
                                message=(
                                    f"Potential N+1 query: '{func_name}()' " "called inside a loop"
                                ),
                                file_path=file_path,
                                line_number=(
                                    child.lineno if hasattr(child, "lineno") else node.lineno
                                ),
                                suggestion=(
                                    "Consider using batch queries, joins, or eager loading "
                                    "to fetch all data at once instead of querying in a loop."
                                ),
                                rule_id="P001",
                                metadata={"method": func_name},
                            )
                            issues.append(issue)
                            break  # Only report once per loop

        return issues

    def _check_inefficient_list_comprehensions(
        self, tree: ast.AST, file_path: Path
    ) -> List[CodeIssue]:
        """Check for inefficient list comprehension patterns."""
        issues = []

        for node in ast.walk(tree):
            # Check for list comprehension with filter that could use generator
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # list(filter(...)) or list(map(...))
                if func_name == "list" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Call):
                        inner_func = self._get_function_name(arg.func)
                        if inner_func in ["filter", "map"]:
                            issue = CodeIssue(
                                category=IssueCategory.PERFORMANCE,
                                level=IssueLevel.INFO,
                                message=f"Inefficient pattern: list({inner_func}(...)) found",
                                file_path=file_path,
                                line_number=node.lineno if hasattr(node, "lineno") else 0,
                                suggestion=(
                                    f"Consider using a list comprehension instead of "
                                    f"list({inner_func}(...)) for better readability "
                                    "and potential performance improvement."
                                ),
                                rule_id="P002",
                            )
                            issues.append(issue)

            # Check for nested list comprehensions that build large intermediate lists
            if isinstance(node, ast.ListComp):
                # Count comprehension depth by traversing nested comprehensions
                depth = 1  # Start at 1 for the current comprehension
                current: Union[ast.ListComp, ast.GeneratorExp] = node
                while True:
                    if not (hasattr(current, "generators") and current.generators):
                        break
                    iter_node = current.generators[0].iter
                    if isinstance(iter_node, (ast.ListComp, ast.GeneratorExp)):
                        depth += 1
                        current = iter_node
                    else:
                        break

                if depth > 2:
                    issue = CodeIssue(
                        category=IssueCategory.PERFORMANCE,
                        level=IssueLevel.WARNING,
                        message=f"Deeply nested list comprehension (depth: {depth})",
                        file_path=file_path,
                        line_number=node.lineno if hasattr(node, "lineno") else 0,
                        suggestion=(
                            "Consider using generator expressions or breaking this into "
                            "separate steps for better performance and readability."
                        ),
                        rule_id="P003",
                        metadata={"depth": depth},
                    )
                    issues.append(issue)

        return issues

    def _check_unnecessary_iterations(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for unnecessary iterations over data."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Look for multiple iterations over the same variable
                iterations: Dict[str, List[int]] = {}

                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        if isinstance(child.iter, ast.Name):
                            var_name = child.iter.id
                            if var_name not in iterations:
                                iterations[var_name] = []
                            iterations[var_name].append(child.lineno)

                # Check for variables iterated multiple times
                for var_name, line_numbers in iterations.items():
                    if len(line_numbers) > 1:
                        issue = CodeIssue(
                            category=IssueCategory.PERFORMANCE,
                            level=IssueLevel.INFO,
                            message=(
                                f"Variable '{var_name}' is iterated {len(line_numbers)} times "
                                f"in function '{node.name}'"
                            ),
                            file_path=file_path,
                            line_number=line_numbers[0],
                            suggestion=(
                                "Consider combining multiple iterations into a single pass "
                                "to improve performance."
                            ),
                            rule_id="P004",
                            metadata={"variable": var_name, "count": len(line_numbers)},
                        )
                        issues.append(issue)

        return issues

    def _check_inefficient_string_concatenation(
        self, tree: ast.AST, file_path: Path
    ) -> List[CodeIssue]:
        """Check for inefficient string concatenation in loops."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for string concatenation using += in loops
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.op, ast.Add):
                            # Check if it's operating on a string
                            if isinstance(child.target, ast.Name):
                                issue = CodeIssue(
                                    category=IssueCategory.PERFORMANCE,
                                    level=IssueLevel.INFO,
                                    message=(
                                        f"String concatenation with '+=' in loop "
                                        f"(variable: '{child.target.id}')"
                                    ),
                                    file_path=file_path,
                                    line_number=(
                                        child.lineno if hasattr(child, "lineno") else node.lineno
                                    ),
                                    suggestion=(
                                        "Consider using ''.join() with a list for better "
                                        "performance when concatenating strings in a loop."
                                    ),
                                    rule_id="P005",
                                    metadata={"variable": child.target.id},
                                )
                                issues.append(issue)
                                break  # Only report once per loop

        return issues

    def _check_redundant_list_calls(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for redundant list() calls on already-list objects."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for list(some_list) pattern
                if func_name == "list" and node.args:
                    arg = node.args[0]

                    # Check if argument is a list comprehension (already a list)
                    if isinstance(arg, ast.ListComp):
                        issue = CodeIssue(
                            category=IssueCategory.PERFORMANCE,
                            level=IssueLevel.INFO,
                            message="Redundant list() call on list comprehension",
                            file_path=file_path,
                            line_number=node.lineno if hasattr(node, "lineno") else 0,
                            suggestion=(
                                "List comprehensions already return lists. "
                                "Remove the redundant list() wrapper."
                            ),
                            rule_id="P006",
                        )
                        issues.append(issue)

        return issues

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from a call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""
