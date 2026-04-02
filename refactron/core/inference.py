"""
Inference engine wrapping astroid for semantic analysis.
Provides capabilities to infer types, values, and resolve symbols.
"""

from typing import Any, List, Optional

import astroid
from astroid import nodes
from astroid.context import InferenceContext
from astroid.exceptions import InferenceError


class InferenceEngine:
    """
    Wrapper around astroid to provide high-level semantic analysis capabilities.
    """

    @staticmethod
    def parse_string(code: str, module_name: str = "") -> nodes.Module:
        """Parse source code string into an astroid node tree."""
        try:
            return astroid.parse(code, module_name=module_name)
        except Exception as e:
            # Fallback or re-raise with better context if needed
            raise ValueError(f"Failed to parse code with astroid: {e}")

    @staticmethod
    def parse_file(file_path: str) -> nodes.Module:
        """Parse a file into an astroid node tree."""
        builder = astroid.builder.AstroidBuilder(astroid.MANAGER)
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return builder.string_build(code, modname=file_path)

    @staticmethod
    def infer_node(node: nodes.NodeNG, context: Optional[InferenceContext] = None) -> List[Any]:
        """
        Attempt to infer the value/type of a given node.
        Returns a list of potential values (astroid nodes).
        """
        try:
            return list(node.infer(context=context))
        except InferenceError:
            return []

    @staticmethod
    def get_node_type_name(node: nodes.NodeNG) -> str:
        """Get the string representation of the inferred type."""
        inferred = InferenceEngine.infer_node(node)
        if not inferred:
            return "Uninferred"

        # Simple heuristic: take the first inference result
        obj = inferred[0]
        if isinstance(obj, nodes.Const):
            return type(obj.value).__name__
        if isinstance(obj, nodes.ClassDef):
            return str(obj.name)
        if isinstance(obj, nodes.FunctionDef):
            return "function"
        if isinstance(obj, nodes.Module):
            return "module"
        if obj is astroid.Uninferable:
            return "Uninferred"

        return str(getattr(obj, "name", str(type(obj))))

    @staticmethod
    def is_subtype_of(node: nodes.NodeNG, type_name: str) -> bool:
        """Check if node infers to a specific type name (e.g. 'str', 'int', 'MyClass')."""
        inferred_list = InferenceEngine.infer_node(node)
        for obj in inferred_list:
            if obj is astroid.Uninferable:
                continue

            # Check direct type name
            if getattr(obj, "name", "") == type_name:
                return True

            # Check instance class
            if isinstance(obj, nodes.Instance):
                if obj.name == type_name:
                    return True
                # Check ancestry
                for ancestor in obj.ancestors():
                    if ancestor.name == type_name:
                        return True

        return False
