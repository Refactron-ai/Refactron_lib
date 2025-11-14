"""Refactorer for simplifying complex conditional statements."""

import ast
from pathlib import Path
from typing import List, Union

from refactron.core.models import RefactoringOperation
from refactron.refactorers.base_refactorer import BaseRefactorer


class SimplifyConditionalsRefactorer(BaseRefactorer):
    """Suggests simplifying deeply nested conditionals."""

    @property
    def operation_type(self) -> str:
        return "simplify_conditionals"

    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Find deeply nested conditionals and suggest simplifications.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of simplification operations
        """
        operations = []

        try:
            tree = ast.parse(source_code)
            lines = source_code.split("\n")

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depth = self._get_max_nesting_depth(node)

                    if depth > 3:  # Deeply nested
                        operation = self._create_simplification(file_path, node, lines, depth)
                        if operation:
                            operations.append(operation)

        except SyntaxError:
            pass

        return operations

    def _get_max_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            depth += 1

        max_child_depth = depth
        for child in ast.iter_child_nodes(node):
            child_depth = self._get_max_nesting_depth(child, depth)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def _create_simplification(
        self,
        file_path: Path,
        func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        lines: List[str],
        depth: int,
    ) -> RefactoringOperation:
        """Create a refactoring operation for conditional simplification."""
        # Get original function code
        if hasattr(func_node, "end_lineno") and func_node.end_lineno:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.end_lineno])
        else:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.lineno + 10])

        # Generate simplified version using early returns
        new_code = self._generate_simplified_version(func_node, old_code)

        return RefactoringOperation(
            operation_type=self.operation_type,
            file_path=file_path,
            line_number=func_node.lineno,
            description=(
                f"Simplify nested conditionals in '{func_node.name}' " f"using early returns"
            ),
            old_code=old_code,
            new_code=new_code,
            risk_score=0.3,  # Moderate risk - changes control flow
            reasoning=(
                f"This function has {depth} levels of nesting. "
                f"Using early returns (guard clauses) reduces nesting and "
                f"improves readability. Each condition is checked upfront, "
                f"making the logic easier to follow."
            ),
            metadata={"original_depth": depth, "function_name": func_node.name},
        )

    def _generate_simplified_version(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], old_code: str
    ) -> str:
        """Generate a simplified version with early returns."""
        # Get function signature
        func_def = old_code.split("\n")[0]

        # For demonstration, create a template for early returns
        params = [arg.arg for arg in func_node.args.args]

        # Generate example with early returns
        new_code = f"""{func_def}
    '''Refactored version using early returns (guard clauses).'''
    # Check invalid conditions first and return early
    if not {params[0] if params else 'condition'}:
        return default_value

    # Each subsequent check is at the same level - no deep nesting
    if not meets_requirement_1():
        return early_result_1

    if not meets_requirement_2():
        return early_result_2

    # Main logic is at top level - easy to read
    result = perform_main_operation()
    return result"""

        return new_code
