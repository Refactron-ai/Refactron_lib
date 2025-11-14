"""Refactorer for reducing function parameters using configuration objects."""

import ast
from pathlib import Path
from typing import List, Union

from refactron.core.models import RefactoringOperation
from refactron.refactorers.base_refactorer import BaseRefactorer


class ReduceParametersRefactorer(BaseRefactorer):
    """Suggests using configuration objects for functions with many parameters."""

    @property
    def operation_type(self) -> str:
        return "reduce_parameters"

    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Find functions with too many parameters and suggest config objects.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of parameter reduction operations
        """
        operations = []

        try:
            tree = ast.parse(source_code)
            lines = source_code.split("\n")

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    param_count = len(node.args.args)

                    if param_count > self.config.max_parameters:
                        operation = self._create_parameter_reduction(
                            file_path, node, lines, param_count
                        )
                        if operation:
                            operations.append(operation)

        except SyntaxError:
            pass

        return operations

    def _create_parameter_reduction(
        self,
        file_path: Path,
        func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        lines: List[str],
        param_count: int,
    ) -> RefactoringOperation:
        """Create a refactoring operation for parameter reduction."""
        # Get original function code
        if hasattr(func_node, "end_lineno") and func_node.end_lineno:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.end_lineno])
        else:
            old_code = "\n".join(lines[func_node.lineno - 1 : func_node.lineno + 5])

        # Generate refactored version with config object
        new_code = self._generate_with_config_object(func_node, old_code)

        return RefactoringOperation(
            operation_type=self.operation_type,
            file_path=file_path,
            line_number=func_node.lineno,
            description=(
                f"Replace {param_count} parameters with a configuration object in "
                f"'{func_node.name}'"
            ),
            old_code=old_code,
            new_code=new_code,
            risk_score=0.4,  # Moderate risk - API change
            reasoning=(
                f"This function has {param_count} parameters (limit: "
                f"{self.config.max_parameters}). "
                f"Using a configuration object (dataclass or dict) reduces cognitive load, "
                f"makes the function easier to test, and allows adding new parameters "
                f"without changing the function signature."
            ),
            metadata={
                "parameter_count": param_count,
                "function_name": func_node.name,
                "parameters": [arg.arg for arg in func_node.args.args],
            },
        )

    def _generate_with_config_object(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], old_code: str
    ) -> str:
        """Generate version using a configuration object."""
        func_name = func_node.name
        params = [arg.arg for arg in func_node.args.args]

        # Create config class name
        config_class = f"{func_name.title().replace('_', '')}Config"

        # Generate new code with dataclass
        new_code = f"""from dataclasses import dataclass

@dataclass
class {config_class}:
    '''Configuration for {func_name} function.'''
"""

        # Add fields
        for param in params:
            # Try to infer type from parameter name
            param_type = self._infer_type(param)
            new_code += f"    {param}: {param_type}\n"

        # Generate new function signature
        new_code += f"""

def {func_name}(config: {config_class}):
    '''
    Refactored version using configuration object.

    Args:
        config: Configuration containing all parameters

    Returns:
        Same as before
    '''
    # Access parameters from config
"""

        # Show how to access each parameter
        for param in params:
            new_code += f"    {param} = config.{param}\n"

        new_code += """

    # Your existing logic here
    result = perform_calculation()
    return result

# Usage example:
# config = {}(
#     {}
# )
# result = {}(config)""".format(
            config_class,
            ",\n#     ".join([f"{p}=value" for p in params]),
            func_name,
        )

        return new_code

    def _infer_type(self, param_name: str) -> str:
        """Infer type hint from parameter name."""
        name_lower = param_name.lower()

        if "count" in name_lower or "number" in name_lower or "id" in name_lower:
            return "int"
        elif "price" in name_lower or "rate" in name_lower or "amount" in name_lower:
            return "float"
        elif "name" in name_lower or "text" in name_lower or "message" in name_lower:
            return "str"
        elif "is_" in name_lower or "has_" in name_lower or "enabled" in name_lower:
            return "bool"
        else:
            return "Any  # Specify appropriate type"
