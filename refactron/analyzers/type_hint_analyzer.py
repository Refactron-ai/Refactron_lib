"""Analyzer for type hints and type annotations."""

import ast
from pathlib import Path
from typing import List

from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel


class TypeHintAnalyzer(BaseAnalyzer):
    """Analyzes type hint usage and suggests improvements."""

    @property
    def name(self) -> str:
        return "type_hints"

    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        """
        Analyze type hints in code.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of type hint issues
        """
        issues = []

        try:
            tree = ast.parse(source_code)

            # Check for various type hint issues
            issues.extend(self._check_missing_return_type(tree, file_path))
            issues.extend(self._check_missing_parameter_types(tree, file_path))
            issues.extend(self._check_missing_attribute_types(tree, file_path))
            issues.extend(self._check_any_usage(tree, file_path))
            issues.extend(self._check_incomplete_types(tree, file_path))

        except SyntaxError:
            pass

        return issues

    def _check_missing_return_type(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for functions missing return type annotations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions, special methods, and __init__
                if node.name.startswith("_") and not node.name == "__init__":
                    continue

                # Skip if it's a property decorator (often obvious return type)
                is_property = any(
                    isinstance(dec, ast.Name) and dec.id == "property"
                    for dec in node.decorator_list
                )

                if not node.returns and not is_property:
                    # Check if function actually returns something
                    has_return = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return) and child.value is not None:
                            has_return = True
                            break

                    if has_return or node.name != "__init__":
                        issue = CodeIssue(
                            category=IssueCategory.TYPE_HINTS,
                            level=IssueLevel.INFO,
                            message=f"Function '{node.name}' missing return type annotation",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=(
                                f"Add return type annotation: def {node.name}(...) -> ReturnType:"
                            ),
                            rule_id="TYPE001",
                            metadata={"function": node.name},
                        )
                        issues.append(issue)

        return issues

    def _check_missing_parameter_types(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for function parameters missing type annotations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions
                if node.name.startswith("_") and not node.name == "__init__":
                    continue

                # Check each parameter
                for arg in node.args.args:
                    # Skip 'self' and 'cls'
                    if arg.arg in ("self", "cls"):
                        continue

                    if not arg.annotation:
                        issue = CodeIssue(
                            category=IssueCategory.TYPE_HINTS,
                            level=IssueLevel.INFO,
                            message=(
                                f"Parameter '{arg.arg}' in function '{node.name}' missing type "
                                f"annotation"
                            ),
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=f"Add type annotation: {arg.arg}: TypeName",
                            rule_id="TYPE002",
                            metadata={"parameter": arg.arg, "function": node.name},
                        )
                        issues.append(issue)

        return issues

    def _check_missing_attribute_types(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for class attributes missing type annotations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check class-level attributes
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        # This is an annotated assignment - good!
                        continue
                    elif isinstance(item, ast.Assign):
                        # Assignment without annotation
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                # Skip if it looks like a constant (ALL_CAPS)
                                if not target.id.isupper():
                                    issue = CodeIssue(
                                        category=IssueCategory.TYPE_HINTS,
                                        level=IssueLevel.INFO,
                                        message=(
                                            f"Class attribute '{target.id}' in '{node.name}' "
                                            f"missing type annotation"
                                        ),
                                        file_path=file_path,
                                        line_number=item.lineno,
                                        suggestion=(
                                            f"Add type annotation: {target.id}: TypeName = value"
                                        ),
                                        rule_id="TYPE003",
                                        metadata={"attribute": target.id, "class": node.name},
                                    )
                                    issues.append(issue)

        return issues

    def _check_any_usage(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for usage of 'Any' type which defeats type checking."""
        issues: List[CodeIssue] = []

        # Check if typing.Any is imported
        has_any_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "typing":
                    for alias in node.names:
                        if alias.name == "Any":
                            has_any_import = True
                            break

        if not has_any_import:
            return issues

        # Find usages of Any
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check return type
                if node.returns and self._contains_any(node.returns):
                    issue = CodeIssue(
                        category=IssueCategory.TYPE_HINTS,
                        level=IssueLevel.INFO,
                        message=f"Function '{node.name}' uses 'Any' return type",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion=(
                            "Consider using a more specific type instead of Any for better type "
                            "safety"
                        ),
                        rule_id="TYPE004",
                        metadata={"function": node.name},
                    )
                    issues.append(issue)

                # Check parameter types
                for arg in node.args.args:
                    if arg.annotation and self._contains_any(arg.annotation):
                        issue = CodeIssue(
                            category=IssueCategory.TYPE_HINTS,
                            level=IssueLevel.INFO,
                            message=(
                                f"Parameter '{arg.arg}' in function '{node.name}' uses 'Any' type"
                            ),
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion="Consider using a more specific type instead of Any",
                            rule_id="TYPE004",
                            metadata={"parameter": arg.arg, "function": node.name},
                        )
                        issues.append(issue)

        return issues

    def _check_incomplete_types(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for incomplete generic types (List without element type, etc.)."""
        issues = []

        incomplete_patterns = {
            "List": "List without element type - use List[ElementType]",
            "Dict": "Dict without key/value types - use Dict[KeyType, ValueType]",
            "Set": "Set without element type - use Set[ElementType]",
            "Tuple": "Tuple without element types - use Tuple[Type1, Type2, ...]",
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check return type
                if node.returns:
                    incomplete = self._find_incomplete_generics(node.returns, incomplete_patterns)
                    for generic_type, suggestion in incomplete:
                        issue = CodeIssue(
                            category=IssueCategory.TYPE_HINTS,
                            level=IssueLevel.INFO,
                            message=f"Incomplete generic type in return: {generic_type}",
                            file_path=file_path,
                            line_number=node.lineno,
                            suggestion=suggestion,
                            rule_id="TYPE005",
                            metadata={"function": node.name, "type": generic_type},
                        )
                        issues.append(issue)

                # Check parameter types
                for arg in node.args.args:
                    if arg.annotation:
                        incomplete = self._find_incomplete_generics(
                            arg.annotation, incomplete_patterns
                        )
                        for generic_type, suggestion in incomplete:
                            issue = CodeIssue(
                                category=IssueCategory.TYPE_HINTS,
                                level=IssueLevel.INFO,
                                message=(
                                    f"Incomplete generic type for parameter '{arg.arg}': "
                                    f"{generic_type}"
                                ),
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion=suggestion,
                                rule_id="TYPE005",
                                metadata={
                                    "parameter": arg.arg,
                                    "function": node.name,
                                    "type": generic_type,
                                },
                            )
                            issues.append(issue)

        return issues

    def _contains_any(self, node: ast.AST) -> bool:
        """Check if a type annotation contains 'Any'."""
        if isinstance(node, ast.Name) and node.id == "Any":
            return True

        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id == "Any":
                return True

        return False

    def _find_incomplete_generics(self, node: ast.AST, patterns: dict) -> List[tuple]:
        """Find incomplete generic types in annotation."""
        incomplete = []

        if isinstance(node, ast.Name):
            if node.id in patterns:
                incomplete.append((node.id, patterns[node.id]))

        elif isinstance(node, ast.Subscript):
            # This is a generic with parameters - good!
            pass

        return incomplete
