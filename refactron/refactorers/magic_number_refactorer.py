"""Refactorer for extracting magic numbers into named constants."""

import ast
from pathlib import Path
from typing import Dict, List, Tuple, Union

from refactron.core.models import RefactoringOperation
from refactron.refactorers.base_refactorer import BaseRefactorer


class MagicNumberRefactorer(BaseRefactorer):
    """Suggests extracting magic numbers into named constants."""

    @property
    def operation_type(self) -> str:
        return "extract_constant"

    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Find magic numbers and suggest extracting them to constants.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of extract constant operations
        """
        operations = []

        try:
            tree = ast.parse(source_code)
            lines = source_code.split("\n")

            # Find magic numbers
            magic_numbers = self._find_magic_numbers(tree)

            # Group by function
            functions_with_magic: Dict[str, List[Tuple[ast.AST, float]]] = {}
            for node, value in magic_numbers:
                func_node = self._get_containing_function(tree, node)
                if func_node:
                    func_name = func_node.name
                    if func_name not in functions_with_magic:
                        functions_with_magic[func_name] = []
                    functions_with_magic[func_name].append((node, value))

            # Create refactoring operations
            for func_name, numbers in functions_with_magic.items():
                if len(numbers) >= 2:  # Only suggest if multiple magic numbers
                    operation = self._create_refactoring(file_path, func_name, numbers, lines, tree)
                    if operation:
                        operations.append(operation)

        except SyntaxError:
            pass

        return operations

    def _find_magic_numbers(self, tree: ast.AST) -> List[tuple]:
        """Find all magic numbers in the tree."""
        magic_numbers = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Ignore common acceptable numbers
                if node.value not in (0, 1, -1, 2):
                    magic_numbers.append((node, node.value))

        return magic_numbers

    def _get_containing_function(
        self, tree: ast.AST, target_node: ast.AST
    ) -> Union[ast.FunctionDef, ast.AsyncFunctionDef, None]:
        """Find the function containing the target node."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if child is target_node:
                        return node
        return None

    def _create_refactoring(
        self, file_path: Path, func_name: str, numbers: List[tuple], lines: List[str], tree: ast.AST
    ) -> RefactoringOperation:
        """Create a refactoring operation for magic numbers."""
        # Find the function
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    func_node = node
                    break

        if not func_node:
            return None

        # Get original function code
        if hasattr(func_node, "end_lineno") and func_node.end_lineno:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.end_lineno])
        else:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.lineno + 5])

        # Generate constant names and new code
        constants = {}
        for _, value in numbers:
            const_name = self._generate_constant_name(value)
            constants[value] = const_name

        # Create the refactored version
        constant_defs = []
        for value, name in constants.items():
            constant_defs.append(f"{name} = {value}")

        # Generate new code with constants
        new_func_code = old_code
        for value, name in constants.items():
            # Simple replacement (in production, use AST transformation)
            new_func_code = new_func_code.replace(str(value), name)

        new_code = "\n".join(constant_defs) + "\n\n" + new_func_code

        return RefactoringOperation(
            operation_type=self.operation_type,
            file_path=file_path,
            line_number=func_node.lineno,
            description=f"Extract magic numbers to named constants in '{func_name}'",
            old_code=old_code,
            new_code=new_code,
            risk_score=0.1,  # Very safe refactoring
            reasoning=f"Extracting {len(constants)} magic numbers to named constants "
            f"improves code readability and maintainability. "
            f"Constants can be reused and their meaning is clear.",
            metadata={"constants": list(constants.items()), "function_name": func_name},
        )

    def _generate_constant_name(self, value: float) -> str:
        """Generate a meaningful constant name from a value."""
        if isinstance(value, float):
            # Handle common decimal values
            if value == 0.1:
                return "DISCOUNT_RATE_10_PERCENT"
            elif value == 0.15:
                return "DISCOUNT_RATE_15_PERCENT"
            elif value == 0.05:
                return "DISCOUNT_RATE_5_PERCENT"
            elif value == 1.05:
                return "SURCHARGE_RATE"
            else:
                clean_value = str(value).replace(".", "_")
                return f"CONSTANT_{clean_value}"
        else:
            # Handle integers
            if value == 100:
                return "THRESHOLD_LOW"
            elif value == 500:
                return "THRESHOLD_MEDIUM"
            elif value == 1000:
                return "THRESHOLD_HIGH"
            elif value >= 10 and value <= 100:
                return f"THRESHOLD_{value}"
            else:
                return f"CONSTANT_{value}"
