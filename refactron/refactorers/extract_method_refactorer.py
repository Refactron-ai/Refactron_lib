"""Refactorer for extracting methods from complex functions."""

import ast
from pathlib import Path
from typing import List, Union

from refactron.core.models import RefactoringOperation
from refactron.refactorers.base_refactorer import BaseRefactorer


class ExtractMethodRefactorer(BaseRefactorer):
    """Suggests extracting methods from overly complex functions."""

    @property
    def operation_type(self) -> str:
        return "extract_method"

    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        """
        Find opportunities to extract methods.

        Args:
            file_path: Path to the file
            source_code: Source code content

        Returns:
            List of extract method operations
        """
        operations = []

        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Look for long functions with multiple logical blocks
                    operations.extend(self._analyze_function(node, file_path, source_code))

        except SyntaxError:
            pass

        return operations

    def _analyze_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path,
        source_code: str,
    ) -> List[RefactoringOperation]:
        """Analyze a function for extract method opportunities."""
        operations = []

        # Simple heuristic: if function has many statements, suggest extraction
        statement_count = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])

        if statement_count > 20:
            # Look for code blocks that could be extracted
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, (ast.For, ast.While, ast.With)):
                    # This could be extracted
                    old_code = self._get_code_snippet(stmt, source_code)
                    new_code = f"def extracted_method_{i}():\n    # Extracted logic\n    pass"

                    operation = RefactoringOperation(
                        operation_type=self.operation_type,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Extract complex block from function '{node.name}'",
                        old_code=old_code,
                        new_code=new_code,
                        risk_score=0.5,
                        reasoning="Function has high statement count. "
                        "Extracting this block would improve readability.",
                    )
                    operations.append(operation)

                    # Only suggest one extraction per function for now
                    break

        return operations

    def _get_code_snippet(self, node: ast.AST, source_code: str) -> str:
        """Extract code snippet for a node."""
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            lines = source_code.split("\n")
            if node.end_lineno:
                return "\n".join(lines[node.lineno - 1 : node.end_lineno])

        return "# Code block"
