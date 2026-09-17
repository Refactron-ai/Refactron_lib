"""
Symbol Table implementation for semantic analysis.
Maps classes, functions, variables, and their relationships across the codebase.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from refactron.core.inference import InferenceEngine

logger = logging.getLogger(__name__)


class SymbolType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    MODULE = "module"
    IMPORT = "import"


@dataclass
class Symbol:
    name: str
    type: SymbolType
    file_path: str
    line_number: int
    scope: str  # "global", "class:ClassName", "function:func_name"
    definition_node: Any = field(default=None, repr=False)  # AST/Astroid node
    references: List[tuple] = field(default_factory=list)  # List of (file_path, line_number)

    # Type inference data
    inferred_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for caching (excluding the definition node)."""
        return {
            "name": self.name,
            "type": self.type.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "scope": self.scope,
            "references": self.references,
            "inferred_type": self.inferred_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Symbol":
        """Deserialize from dictionary."""
        data["type"] = SymbolType(data["type"])
        return cls(**data)


@dataclass
class SymbolTable:
    # Map: file_path -> { scope -> { name -> Symbol } }
    symbols: Dict[str, Dict[str, Dict[str, Symbol]]] = field(default_factory=dict)
    # Map: global_name -> Symbol (for easy cross-file lookup of exports)
    exports: Dict[str, Symbol] = field(default_factory=dict)
    # Metadata for caching (Map: file_path -> mtime)
    metadata: Dict[str, float] = field(default_factory=dict)

    def remove_file(self, file_path: str) -> None:
        """Remove all symbols associated with a specific file."""
        if file_path not in self.symbols:
            return
            
        for scope, names in self.symbols[file_path].items():
            if scope == "global":
                for name, symbol in list(names.items()):
                    if name in self.exports and self.exports[name].file_path == file_path:
                        del self.exports[name]
                        
        del self.symbols[file_path]
        if file_path in self.metadata:
            del self.metadata[file_path]

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the table."""
        if symbol.file_path not in self.symbols:
            self.symbols[symbol.file_path] = {}

        if symbol.scope not in self.symbols[symbol.file_path]:
            self.symbols[symbol.file_path][symbol.scope] = {}

        self.symbols[symbol.file_path][symbol.scope][symbol.name] = symbol

        # Track global exports (top-level functions and classes)
        if symbol.scope == "global" and symbol.type in (
            SymbolType.CLASS,
            SymbolType.FUNCTION,
            SymbolType.VARIABLE,
        ):
            # Key by module path + name? Or just name for now?
            # Using simple name collision strategy for MVP
            self.exports[symbol.name] = symbol

    def get_symbol(self, file_path: str, name: str, scope: str = "global") -> Optional[Symbol]:
        """Retrieve a symbol."""
        return self.symbols.get(file_path, {}).get(scope, {}).get(name)

    def resolve_reference(
        self, name: str, current_file: str, current_scope: str
    ) -> Optional[Symbol]:
        """
        Attempt to resolve a name to a definition.
        1. Check local scope
        2. Check global scope of current file
        3. Check exports (cross-file)
        """
        # 1. Local scope
        local = self.get_symbol(current_file, name, current_scope)
        if local:
            return local

        # 2. File Global scope
        if current_scope != "global":
            file_global = self.get_symbol(current_file, name, "global")
            if file_global:
                return file_global

        # 3. Cross-file exports (Naive implementation)
        # TODO: Enhance this with proper import resolution
        return self.exports.get(name)


class SymbolTableBuilder:
    """Builds and manages the project-wide symbol table."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.symbol_table = SymbolTable()
        self.cache_dir = cache_dir
        self.inference_engine = InferenceEngine()

    def build_for_project(self, project_root: Path) -> SymbolTable:
        """Scan project and build symbol table."""
        updated = False
        if self.cache_dir:
            cached = self._load_cache()
            if cached:
                self.symbol_table = cached

        all_python_files = list(project_root.rglob("*.py"))
        excluded_dirs = {".git", ".rag", "__pycache__", "venv", ".venv", "env", "node_modules"}
        python_files = [
            f for f in all_python_files if not any(excluded in f.parts for excluded in excluded_dirs)
        ]

        current_file_paths = set()

        for file_path in python_files:
            file_str = str(file_path)
            current_file_paths.add(file_str)
            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                continue

            if file_str in self.symbol_table.metadata and self.symbol_table.metadata[file_str] == mtime:
                continue

            # Need to update this file
            if file_str in self.symbol_table.symbols:
                self.symbol_table.remove_file(file_str)
            
            self._analyze_file(file_path)
            self.symbol_table.metadata[file_str] = mtime
            updated = True

        # Check for deleted files
        deleted_files = set(self.symbol_table.symbols.keys()) - current_file_paths
        for file_str in deleted_files:
            self.symbol_table.remove_file(file_str)
            updated = True

        if getattr(self, "cache_dir", None) and updated:
            try:
                self._save_cache()
            except Exception as e:
                logger.warning(f"Failed to save cache in build_for_project: {e}")

        return self.symbol_table

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file and populate symbols."""
        try:
            # We use astroid for better inference capabilities later
            tree = self.inference_engine.parse_file(str(file_path))

            # Walk the tree
            self._visit_node(tree, str(file_path), "global")

        except Exception as e:
            logger.warning(f"Failed to build symbol table for {file_path}: {e}")

    def _visit_node(self, node: Any, file_path: str, scope: str) -> None:
        """Recursive node visitor."""
        import astroid.nodes as nodes

        new_scope = scope

        if isinstance(node, (nodes.ClassDef, nodes.FunctionDef)):
            # Register the definition itself in the CURRENT scope
            symbol_type = (
                SymbolType.CLASS if isinstance(node, nodes.ClassDef) else SymbolType.FUNCTION
            )
            symbol = Symbol(
                name=node.name,
                type=symbol_type,
                file_path=file_path,
                line_number=node.lineno,
                scope=scope,
                definition_node=node,
            )
            self.symbol_table.add_symbol(symbol)

            # Enter new scope
            prefix = "class" if isinstance(node, nodes.ClassDef) else "function"
            new_scope = f"{prefix}:{node.name}"

        elif isinstance(node, nodes.AssignName):
            # Register variable assignment
            symbol = Symbol(
                name=node.name,
                type=SymbolType.VARIABLE,
                file_path=file_path,
                line_number=node.lineno,
                scope=scope,
                definition_node=node,
            )
            # Try to infer type
            try:
                symbol.inferred_type = self.inference_engine.get_node_type_name(node)
            except Exception:
                pass

            self.symbol_table.add_symbol(symbol)

        # Recurse children
        if hasattr(node, "get_children"):
            for child in node.get_children():
                self._visit_node(child, file_path, new_scope)

    def _save_cache(self) -> None:
        """Save symbol table to cache."""
        if not self.cache_dir:
            return

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / "symbols.json"

            data = {
                "symbols": {
                    f: {
                        s: {n: sym.to_dict() for n, sym in names.items()}
                        for s, names in scopes.items()
                    }
                    for f, scopes in self.symbol_table.symbols.items()
                },
                "exports": {n: sym.to_dict() for n, sym in self.symbol_table.exports.items()},
                "metadata": self.symbol_table.metadata,
            }

            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save symbol table cache: {e}")

    def _load_cache(self) -> Optional[SymbolTable]:
        """Load symbol table from cache."""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / "symbols.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            table = SymbolTable()

            # Reconstruct symbols
            for f_path, scopes in data.get("symbols", {}).items():
                table.symbols[f_path] = {}
                for scope_name, names in scopes.items():
                    table.symbols[f_path][scope_name] = {}
                    for name, sym_data in names.items():
                        table.symbols[f_path][scope_name][name] = Symbol.from_dict(sym_data)

            # Reconstruct exports
            for name, sym_data in data.get("exports", {}).items():
                table.exports[name] = Symbol.from_dict(sym_data)
                
            table.metadata = data.get("metadata", {})

            return table

        except Exception as e:
            logger.warning(f"Failed to load symbol table cache: {e}")
            return None
