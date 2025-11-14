"""Refactorer for adding docstrings to functions and classes."""

import ast
from pathlib import Path
from typing import List, Union

from refactron.core.models import RefactoringOperation
from refactron.refactorers.base_refactorer import BaseRefactorer


class AddDocstringRefactorer(BaseRefactorer):
    """Suggests adding docstrings to undocumented functions and classes."""

    @property
    def operation_type(self) -> str:
        return "add_docstring"

    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Find functions/classes without docstrings and suggest adding them.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of add docstring operations
        """
        operations = []

        try:
            tree = ast.parse(source_code)
            lines = source_code.split("\n")

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip private functions/classes
                    if node.name.startswith("_") and not node.name.startswith("__"):
                        continue

                    docstring = ast.get_docstring(node)
                    if not docstring:
                        operation = self._create_docstring_addition(file_path, node, lines)
                        if operation:
                            operations.append(operation)

        except SyntaxError:
            pass

        return operations

    def _create_docstring_addition(
        self,
        file_path: Path,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
        lines: List[str],
    ) -> RefactoringOperation:
        """Create a refactoring operation for adding a docstring."""
        entity_type = "Class" if isinstance(node, ast.ClassDef) else "Function"

        # Get original code
        if hasattr(node, "end_lineno") and node.end_lineno:
            old_code = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        else:
            old_code = "\n".join(lines[node.lineno - 1 : min(node.lineno + 10, len(lines))])

        # Generate version with docstring
        new_code = self._generate_with_docstring(node, lines)

        return RefactoringOperation(
            operation_type=self.operation_type,
            file_path=file_path,
            line_number=node.lineno,
            description=f"Add docstring to {entity_type.lower()} '{node.name}'",
            old_code=old_code,
            new_code=new_code,
            risk_score=0.0,  # Very safe - only adding documentation
            reasoning=f"Adding a docstring improves code documentation and helps other "
            f"developers understand what this {entity_type.lower()} does. "
            f"Good docstrings include a brief description, parameters (Args), "
            f"and return values (Returns).",
            metadata={"entity_type": entity_type, "entity_name": node.name},
        )

    def _generate_with_docstring(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], lines: List[str]
    ) -> str:
        """Generate code with an appropriate docstring."""
        if isinstance(node, ast.ClassDef):
            return self._generate_class_with_docstring(node, lines)
        else:
            return self._generate_function_with_docstring(node, lines)

    def _generate_class_with_docstring(self, node: ast.ClassDef, lines: List[str]) -> str:
        """Generate class code with docstring."""
        class_def = lines[node.lineno - 1]
        indent = len(class_def) - len(class_def.lstrip())
        indent_str = " " * (indent + 4)

        docstring = f"{class_def}\n{indent_str}'''{self._generate_class_description(node)}\n"

        # Add attributes if we can detect them
        has_init = any(isinstance(n, ast.FunctionDef) and n.name == "__init__" for n in node.body)

        if has_init:
            docstring += f"{indent_str}\n{indent_str}Attributes:\n"
            docstring += f"{indent_str}    attribute1: Description of attribute1\n"
            docstring += f"{indent_str}    attribute2: Description of attribute2\n"

        docstring += f"{indent_str}'''\n"

        # Add rest of class body
        if hasattr(node, "end_lineno") and node.end_lineno:
            rest_of_class = "\n".join(lines[node.lineno : node.end_lineno])
            return docstring + rest_of_class
        else:
            return docstring + f"{indent_str}pass"

    def _generate_function_with_docstring(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], lines: List[str]
    ) -> str:
        """Generate function code with docstring."""
        func_def = lines[node.lineno - 1]
        indent = len(func_def) - len(func_def.lstrip())
        indent_str = " " * (indent + 4)

        # Generate docstring
        description = self._generate_function_description(node)
        params = [arg.arg for arg in node.args.args]

        docstring = f"{func_def}\n{indent_str}'''\n{indent_str}{description}\n"

        # Add Args section if there are parameters
        if params:
            docstring += f"{indent_str}\n{indent_str}Args:\n"
            for param in params:
                param_desc = self._generate_param_description(param)
                docstring += f"{indent_str}    {param}: {param_desc}\n"

        # Add Returns section
        has_return = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))

        if has_return:
            docstring += f"{indent_str}\n{indent_str}Returns:\n"
            docstring += f"{indent_str}    {self._generate_return_description(node)}\n"

        docstring += f"{indent_str}'''\n"

        # Add function body
        if hasattr(node, "end_lineno") and node.end_lineno:
            # Get body lines
            body_start = node.lineno  # Line after def
            rest_of_function = "\n".join(lines[body_start : node.end_lineno])
            return docstring + rest_of_function
        else:
            return docstring + f"{indent_str}pass"

    def _generate_class_description(self, node: ast.ClassDef) -> str:
        """Generate a description for a class."""
        name_words = self._split_camel_case(node.name)
        return f"{' '.join(name_words)} class."

    def _generate_function_description(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Generate a description for a function."""
        name_words = node.name.replace("_", " ")

        # Make it more descriptive based on common patterns
        if node.name.startswith("get_"):
            return f"Get {name_words[4:]}."
        elif node.name.startswith("set_"):
            return f"Set {name_words[4:]}."
        elif node.name.startswith("is_") or node.name.startswith("has_"):
            return f"Check if {name_words[3:]}."
        elif node.name.startswith("calculate_"):
            return f"Calculate {name_words[10:]}."
        elif node.name.startswith("process_"):
            return f"Process {name_words[8:]}."
        else:
            return f"{name_words.capitalize()}."

    def _generate_param_description(self, param_name: str) -> str:
        """Generate a description for a parameter."""
        # Common parameter patterns
        if param_name in ["self", "cls"]:
            return "Class instance" if param_name == "self" else "Class reference"

        name_lower = param_name.lower()
        if "path" in name_lower or "file" in name_lower:
            return "Path to the file"
        elif "name" in name_lower:
            return "Name of the entity"
        elif "id" in name_lower:
            return "Unique identifier"
        elif "count" in name_lower or "num" in name_lower:
            return "Number of items"
        elif "data" in name_lower:
            return "Data to process"
        elif "config" in name_lower:
            return "Configuration object"
        else:
            return f"The {param_name.replace('_', ' ')}"

    def _generate_return_description(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Generate a description for the return value."""
        # Try to infer from function name
        if node.name.startswith("is_") or node.name.startswith("has_"):
            return "True if condition is met, False otherwise"
        elif node.name.startswith("get_"):
            return f"The requested {node.name[4:].replace('_', ' ')}"
        elif node.name.startswith("calculate_"):
            return f"The calculated {node.name[10:].replace('_', ' ')}"
        else:
            return "The result of the operation"

    def _split_camel_case(self, name: str) -> List[str]:
        """Split CamelCase into words."""
        import re

        words = re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", name)).split()
        return [w.lower() for w in words if w]
