"""Analyzer for dead code - unused functions, variables, and imports."""

import ast
from pathlib import Path
from typing import Dict, List, Set, Union

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class DeadCodeAnalyzer(BaseAnalyzer):
    """Detects unused code that can be safely removed."""

    @property
    def name(self) -> str:
        return "dead_code"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze code for unused elements.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of dead code issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various types of dead code
            issues.extend(self._check_unused_functions(tree, file_path))
            issues.extend(self._check_unused_variables(tree, file_path))
            issues.extend(self._check_unreachable_code(tree, file_path))
            issues.extend(self._check_empty_functions(tree, file_path))
            issues.extend(self._check_redundant_conditions(tree, file_path))

        except SyntaxError:
            pass

        return issues

    def _check_unused_functions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect functions that are defined but never called."""
        issues = []

        # Collect all function definitions
        defined_functions: Dict[str, int] = {}  # name -> line_number

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip special methods and private functions
                if not node.name.startswith("_"):
                    defined_functions[node.name] = node.lineno

        # Collect all function calls
        called_functions: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_functions.add(node.func.attr)

        # Find uncalled functions
        for func_name, line_num in defined_functions.items():
            if func_name not in called_functions:
                # Check if it might be exported or used in __all__
                is_exported = self._is_exported(tree, func_name)

                if not is_exported:
                    issue = CodeIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        level=IssueLevel.INFO,
                        message=f"Function '{func_name}' is defined but never called",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=(
                            f"Remove unused function '{func_name}' or export it if it's part "
                            f"of the API"
                        ),
                        rule_id="DEAD001",
                        metadata={"function": func_name},
                    )
                    issues.append(issue)

        return issues

    def _check_unused_variables(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect variables that are assigned but never used."""
        issues = []

        # This is a simplified check - full analysis requires scope tracking
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Track variables in this function
                assigned_vars: Dict[str, int] = {}
                used_vars: Set[str] = set()

                for child in ast.walk(node):
                    # Track assignments
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                assigned_vars[target.id] = child.lineno

                    # Track usages
                    elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        used_vars.add(child.id)

                # Find unused variables
                for var_name, line_num in assigned_vars.items():
                    if var_name not in used_vars and not var_name.startswith("_"):
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.INFO,
                            message=(
                                f"Variable '{var_name}' is assigned but never used in function "
                                f"'{node.name}'"
                            ),
                            file_path=file_path,
                            line_number=line_num,
                            suggestion=(
                                f"Remove unused variable '{var_name}' or use _ if intentionally "
                                f"unused"
                            ),
                            rule_id="DEAD002",
                            metadata={"variable": var_name, "function": node.name},
                        )
                        issues.append(issue)

        return issues

    def _check_unreachable_code(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect code that can never be executed."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for code after return statement
                found_return = False

                for i, stmt in enumerate(node.body):
                    if found_return and i < len(node.body):
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message=f"Unreachable code after return statement in '{node.name}'",
                            file_path=file_path,
                            line_number=stmt.lineno,
                            suggestion="Remove unreachable code or fix control flow logic",
                            rule_id="DEAD003",
                            metadata={"function": node.name},
                        )
                        issues.append(issue)
                        break

                    if isinstance(stmt, ast.Return):
                        found_return = True

            # Check for code after break/continue in loops
            elif isinstance(node, (ast.For, ast.While)):
                self._check_loop_unreachable(node, file_path, issues)

        return issues

    def _check_loop_unreachable(
        self, loop_node: Union[ast.For, ast.While], file_path: Path, issues: List[CodeIssue]
    ) -> None:
        """Check for unreachable code in loops."""
        found_break = False

        for i, stmt in enumerate(loop_node.body):
            if found_break and i < len(loop_node.body):
                issue = CodeIssue(
                    category=IssueCategory.MAINTAINABILITY,
                    level=IssueLevel.WARNING,
                    message="Unreachable code after break statement",
                    file_path=file_path,
                    line_number=stmt.lineno,
                    suggestion="Remove unreachable code or fix loop logic",
                    rule_id="DEAD003",
                )
                issues.append(issue)
                break

            if isinstance(stmt, ast.Break):
                found_break = True

    def _check_empty_functions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect functions that are empty or only contain pass."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip special methods
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                # Check if function body is empty or only has pass/docstring
                is_empty = True
                has_docstring = False

                for stmt in node.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                        # This is a docstring
                        has_docstring = True
                    elif not isinstance(stmt, ast.Pass):
                        is_empty = False
                        break

                if is_empty and not has_docstring:
                    issue = CodeIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        level=IssueLevel.INFO,
                        message=f"Empty function: '{node.name}'",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Remove empty function or implement it. "
                        "If it's a placeholder, add a docstring or TODO comment",
                        rule_id="DEAD004",
                        metadata={"function": node.name},
                    )
                    issues.append(issue)

        return issues

    def _check_redundant_conditions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Detect redundant or always-true/false conditions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check for conditions that are always True or False
                if isinstance(node.test, ast.Constant):
                    if node.test.value is True:
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message="Condition is always True",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=(
                                "Remove the if statement and keep the body, or fix the condition"
                            ),
                            rule_id="DEAD005",
                        )
                        issues.append(issue)

                    elif node.test.value is False:
                        issue = CodeIssue(
                            category=IssueCategory.MAINTAINABILITY,
                            level=IssueLevel.WARNING,
                            message="Condition is always False - this code never executes",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="Remove this dead code or fix the condition",
                            rule_id="DEAD005",
                        )
                        issues.append(issue)

                # Check for redundant comparisons like if x == True:
                elif isinstance(node.test, ast.Compare):
                    if len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq):
                        if len(node.test.comparators) == 1:
                            comparator = node.test.comparators[0]
                            if isinstance(comparator, ast.Constant):
                                if comparator.value is True:
                                    issue = CodeIssue(
                                        category=IssueCategory.STYLE,
                                        level=IssueLevel.INFO,
                                        message="Redundant comparison with True",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        suggestion="Use 'if x:' instead of 'if x == True:'",
                                        rule_id="DEAD006",
                                    )
                                    issues.append(issue)
                                elif comparator.value is False:
                                    issue = CodeIssue(
                                        category=IssueCategory.STYLE,
                                        level=IssueLevel.INFO,
                                        message="Redundant comparison with False",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        suggestion="Use 'if not x:' instead of 'if x == False:'",
                                        rule_id="DEAD006",
                                    )
                                    issues.append(issue)

        return issues

    def _is_exported(self, tree: ast.AST, name: str) -> bool:
        """Check if a name is explicitly exported via __all__."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and elt.value == name:
                                    return True
        return False
