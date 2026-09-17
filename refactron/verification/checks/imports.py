"""ImportIntegrityVerifier — Check 2: import removal, resolution, cycle detection."""

import ast
import importlib.util
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from refactron.verification.engine import BaseCheck
from refactron.verification.result import CheckResult

# Guardrails for project-wide import-graph construction (Step 4: cycle
# detection). The graph is intentionally bounded — cycle detection is a
# best-effort confidence boost, never a correctness guarantee, so when a
# limit is hit we skip the check rather than block a transform.
_MAX_GRAPH_FILES = 2000
_GRAPH_TIME_BUDGET_S = 5.0
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}


class ImportIntegrityVerifier(BaseCheck):
    """Validates import integrity after a transform.

    Steps 1-3 (removed-but-used imports, new-import resolvability) work on the
    single file. Step 4 (cycle detection) builds a bounded project-wide import
    graph and reports cycles *introduced* by the transform.

    Complexity limits for Step 4:
      - At most ``_MAX_GRAPH_FILES`` (2000) files are scanned.
      - Graph construction is abandoned after ``_GRAPH_TIME_BUDGET_S`` (5s).
      - The graph is cached for the lifetime of this verifier instance.
      - Only intra-project (first-party) imports become edges; third-party
        and stdlib imports are ignored.
    When any limit is hit, or no ``project_root`` was supplied, cycle
    detection is silently skipped — never blocking.
    """

    name = "import_integrity"

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root
        # Base import graph (module -> set of imported project modules),
        # cached per resolved project root for the verifier's lifetime.
        self._graph_cache: Dict[str, Optional[Dict[str, Set[str]]]] = {}

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        start = time.monotonic()
        details: Dict[str, Any] = {}

        orig_imports = self._extract_import_names(original)
        trans_imports = self._extract_import_names(transformed)

        # Step 1-2: removed imports still referenced
        removed = orig_imports - trans_imports
        if removed:
            still_used = self._find_references(transformed, removed)
            if still_used:
                names = ", ".join(sorted(still_used))
                details["removed_but_used"] = sorted(still_used)
                return self._fail(
                    f"Import(s) removed but still used: {names}",
                    start,
                    details,
                )

        # Step 3: new imports resolvable
        added = trans_imports - orig_imports
        if added:
            orig_modules = self._extract_module_names(original)
            trans_modules = self._extract_module_names(transformed)
            new_modules = trans_modules - orig_modules
            for mod in new_modules:
                top_level = mod.split(".")[0]
                if importlib.util.find_spec(top_level) is None:
                    details["unresolvable_import"] = mod
                    return self._fail(
                        f"New import '{mod}' cannot be resolved",
                        start,
                        details,
                    )

        # Step 4: cycle detection — report cycles introduced by the transform.
        cycle = self._detect_new_cycle(original, transformed, file_path, details)
        if cycle is not None:
            details["import_cycle"] = cycle
            return self._fail(
                "Transform introduces an import cycle: " + " -> ".join(cycle),
                start,
                details,
            )

        elapsed = int((time.monotonic() - start) * 1000)
        return CheckResult(
            check_name=self.name,
            passed=True,
            blocking_reason="",
            confidence=1.0,
            duration_ms=elapsed,
            details=details,
        )

    def _fail(self, reason: str, start: float, details: Dict[str, Any]) -> CheckResult:
        elapsed = int((time.monotonic() - start) * 1000)
        return CheckResult(
            check_name=self.name,
            passed=False,
            blocking_reason=reason,
            confidence=0.0,
            duration_ms=elapsed,
            details=details,
        )

    # ----- Step 4: import-cycle detection ---------------------------------

    def _detect_new_cycle(
        self,
        original: str,
        transformed: str,
        file_path: Path,
        details: Dict[str, Any],
    ) -> Optional[List[str]]:
        """Return a cycle path the transform introduces, or None.

        A cycle is reported only when it runs through the changed module and
        did *not* exist before the transform — pre-existing cycles are left
        for a dedicated lint pass, not this verifier.
        """
        if self.project_root is None:
            details["cycle_check"] = "skipped: no project_root"
            return None

        root = self.project_root.resolve()
        changed_mod = self._module_name(file_path, root)
        if changed_mod is None:
            details["cycle_check"] = "skipped: file outside project_root"
            return None

        base_graph = self._build_base_graph(root)
        if base_graph is None:
            details["cycle_check"] = "skipped: graph budget exceeded"
            return None

        is_pkg = Path(file_path).name == "__init__.py"
        orig_edges = self._module_edges(original, changed_mod, is_pkg, root)
        trans_edges = self._module_edges(transformed, changed_mod, is_pkg, root)
        if orig_edges == trans_edges:
            details["cycle_check"] = "ran: no project import edges changed"
            return None

        graph_trans = dict(base_graph)
        graph_trans[changed_mod] = trans_edges
        cyc_trans = self._find_cycle_through(graph_trans, changed_mod)
        if cyc_trans is None:
            details["cycle_check"] = "ran: no cycle"
            return None

        graph_orig = dict(base_graph)
        graph_orig[changed_mod] = orig_edges
        if self._find_cycle_through(graph_orig, changed_mod) is not None:
            # Cycle already existed; the transform did not introduce it.
            details["cycle_check"] = "ran: pre-existing cycle (not introduced)"
            return None

        details["cycle_check"] = "ran: new cycle detected"
        return cyc_trans

    def _build_base_graph(self, root: Path) -> Optional[Dict[str, Set[str]]]:
        """Build (and cache) the project's module import graph.

        Returns None if a guardrail (file count / time budget) is hit.
        """
        key = str(root)
        if key in self._graph_cache:
            return self._graph_cache[key]

        graph: Dict[str, Set[str]] = {}
        deadline = time.monotonic() + _GRAPH_TIME_BUDGET_S
        scanned = 0
        for path in root.rglob("*.py"):
            if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            scanned += 1
            if scanned > _MAX_GRAPH_FILES or time.monotonic() > deadline:
                self._graph_cache[key] = None
                return None
            module_name = self._module_name(path, root)
            if module_name is None:
                continue
            try:
                code = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            is_pkg = path.name == "__init__.py"
            graph[module_name] = self._module_edges(code, module_name, is_pkg, root)

        self._graph_cache[key] = graph
        return graph

    @staticmethod
    def _module_name(file_path: Path, root: Path) -> Optional[str]:
        """Map a file path to its dotted module name relative to ``root``."""
        try:
            rel = Path(file_path).resolve().relative_to(root)
        except ValueError:
            return None
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else None

    @classmethod
    def _module_edges(
        cls, code: str, module_name: str, is_pkg: bool, root: Path
    ) -> Set[str]:
        """Intra-project modules imported by ``code`` (graph out-edges)."""
        edges: Set[str] = set()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return edges

        # The package a relative import resolves against.
        if is_pkg:
            package = module_name
        elif "." in module_name:
            package = module_name.rsplit(".", 1)[0]
        else:
            package = ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = cls._resolve(alias.name, root)
                    if target and target != module_name:
                        edges.add(target)
            elif isinstance(node, ast.ImportFrom):
                base = cls._relative_base(node.level, package)
                if node.level and node.module:
                    base = f"{base}.{node.module}" if base else node.module
                elif node.level == 0:
                    base = node.module or ""
                if base:
                    resolved = cls._resolve(base, root)
                    if resolved and resolved != module_name:
                        edges.add(resolved)
                # `from pkg import sub` may import a submodule, not a name.
                for alias in node.names:
                    candidate = f"{base}.{alias.name}" if base else alias.name
                    resolved = cls._resolve(candidate, root)
                    if resolved and resolved != module_name:
                        edges.add(resolved)
        return edges

    @staticmethod
    def _relative_base(level: int, package: str) -> str:
        """Resolve the package a relative import (``level`` dots) points at."""
        if level <= 0:
            return package
        parts = package.split(".") if package else []
        # level 1 == current package, level 2 == its parent, ...
        keep = len(parts) - (level - 1)
        if keep < 0:
            return ""
        return ".".join(parts[:keep])

    @staticmethod
    def _resolve(dotted: str, root: Path) -> Optional[str]:
        """Return ``dotted`` if it names a file/package under ``root``."""
        if not dotted:
            return None
        parts = dotted.split(".")
        as_module = root.joinpath(*parts).with_suffix(".py")
        as_package = root.joinpath(*parts, "__init__.py")
        if as_module.is_file() or as_package.is_file():
            return dotted
        return None

    @staticmethod
    def _find_cycle_through(
        graph: Dict[str, Set[str]], start: str
    ) -> Optional[List[str]]:
        """Return a cycle ``start -> ... -> start``, or None.

        A cycle exists iff ``start`` is reachable from one of its own
        successors. Uses bounded BFS per successor — O(V+E) each.
        """
        for first in sorted(graph.get(start, set())):
            parent: Dict[str, Optional[str]] = {first: None}
            queue: List[str] = [first]
            while queue:
                node = queue.pop(0)
                if node == start:
                    chain: List[str] = []
                    cur: Optional[str] = node
                    while cur is not None:
                        chain.append(cur)
                        cur = parent[cur]
                    chain.reverse()
                    return [start] + chain
                for nxt in sorted(graph.get(node, set())):
                    if nxt not in parent:
                        parent[nxt] = node
                        queue.append(nxt)
        return None

    @staticmethod
    def _extract_import_names(code: str) -> Set[str]:
        """Extract all locally-bound names from import statements."""
        names: Set[str] = set()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return names
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        return names

    @staticmethod
    def _extract_module_names(code: str) -> Set[str]:
        """Extract actual module paths from import statements."""
        modules: Set[str] = set()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return modules
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        return modules

    @staticmethod
    def _find_references(code: str, names: Set[str]) -> Set[str]:
        """Find which of the given names are still referenced in code body."""
        referenced: Set[str] = set()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return referenced

        for node in ast.walk(tree):
            # Skip import nodes themselves
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name) and node.id in names:
                referenced.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in names:
                    referenced.add(node.value.id)
        return referenced
