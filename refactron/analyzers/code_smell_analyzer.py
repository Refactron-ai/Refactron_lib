"""Analyzer for code smells and anti-patterns."""

import ast
import copy
from pathlib import Path
from typing import Dict, List, Set

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
            issues.extend(self._check_unused_imports(tree, file_path, source_code))
            issues.extend(self._check_repeated_code_blocks(tree, file_path))

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

    def _check_unused_imports(
        self, tree: ast.AST, file_path: Path, source_code: str
    ) -> List[CodeIssue]:
        """Check for unused imports more accurately."""
        issues = []
        imported_names = {}
        used_names = set()

        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split(".")[0]
                    imported_names[name] = (alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        if alias.name != "*":
                            name = alias.asname if alias.asname else alias.name
                            imported_names[name] = (
                                f"{node.module}.{alias.name}",
                                node.lineno,
                            )

        # Collect all name usages
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Get the base name for attribute access
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # Find unused imports
        for name, (full_name, lineno) in imported_names.items():
            if name not in used_names:
                # Special case: check if it's used in type hints or docstrings
                # This is a simple check - a more comprehensive one would parse type hints
                if name not in source_code:
                    continue

                # Check if it appears anywhere after the import line
                lines = source_code.split("\n")
                import_line = lineno - 1
                found_usage = False
                for i in range(import_line + 1, len(lines)):
                    if name in lines[i]:
                        # Could be a comment or string, but we'll be conservative
                        found_usage = True
                        break

                if not found_usage:
                    issue = CodeIssue(
                        category=IssueCategory.CODE_SMELL,
                        level=IssueLevel.INFO,
                        message=f"Unused import: '{full_name}'",
                        file_path=file_path,
                        line_number=lineno,
                        suggestion=f"Remove unused import '{full_name}'",
                        rule_id="S006",
                        metadata={"import": full_name},
                    )
                    issues.append(issue)

        return issues

    def _check_repeated_code_blocks(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for repeated code blocks within functions."""
        issues = []

        def get_statement_pattern(node: ast.AST) -> str:
            """Get a normalized pattern of a statement for comparison."""
            try:
                # Replace all constant values and names to create a pattern
                class PatternVisitor(ast.NodeTransformer):
                    def visit_Constant(self, node):
                        return ast.Constant(value="CONST")

                    def visit_Name(self, node):
                        if isinstance(node.ctx, ast.Store):
                            # Keep variable names on the left side of assignments
                            return node
                        # Replace variable names on the right side
                        return ast.Name(id="VAR", ctx=node.ctx)

                # Create a copy and transform it
                pattern_node = copy.deepcopy(node)
                pattern_node = PatternVisitor().visit(pattern_node)
                # Use ast.unparse if available (Python 3.9+), otherwise fallback
                if hasattr(ast, "unparse"):
                    result: str = ast.unparse(pattern_node)  # type: ignore[assignment]
                    return result
                else:
                    # Fallback for older Python versions - use ast.dump
                    return ast.dump(pattern_node)
            except Exception:
                return ""

        # Analyze each function
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Collect patterns of statement blocks (3+ consecutive lines)
                statement_blocks: Dict[str, List[int]] = {}

                if len(node.body) < 6:  # Need at least 6 statements for meaningful duplication
                    continue

                # Look for blocks of 3 consecutive statements
                for i in range(len(node.body) - 2):
                    block = []
                    for j in range(3):
                        if i + j < len(node.body):
                            stmt = node.body[i + j]
                            pattern = get_statement_pattern(stmt)
                            if pattern:
                                block.append(pattern)

                    if len(block) == 3:
                        block_sig = "|||".join(block)
                        if block_sig not in statement_blocks:
                            statement_blocks[block_sig] = []
                        statement_blocks[block_sig].append(node.body[i].lineno)

                # Find duplicates
                for block_sig, occurrences in statement_blocks.items():
                    if len(occurrences) > 1:
                        issue = CodeIssue(
                            category=IssueCategory.CODE_SMELL,
                            level=IssueLevel.WARNING,
                            message=(
                                f"Repeated code block found in function '{node.name}' "
                                f"({len(occurrences)} occurrences)"
                            ),
                            file_path=file_path,
                            line_number=occurrences[0],
                            suggestion=(
                                "Consider extracting repeated code into a separate function "
                                "to reduce duplication and improve maintainability."
                            ),
                            rule_id="S007",
                            metadata={"occurrences": len(occurrences), "lines": occurrences},
                        )
                        issues.append(issue)
                        break  # Only report once per function

        return issues
