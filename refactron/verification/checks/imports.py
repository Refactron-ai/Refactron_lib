"""ImportIntegrityVerifier — Check 2: import removal, resolution, cycle detection."""

import ast
import importlib.util
import time
from pathlib import Path
from typing import Any, Dict, Set

from refactron.verification.engine import BaseCheck
from refactron.verification.result import CheckResult


class ImportIntegrityVerifier(BaseCheck):
    """Validates import integrity after a transform."""

    name = "import_integrity"

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
        # TODO: Step 4 (cycle detection) deferred — requires project-wide import graph
        #       which is expensive for MVP. Will add in Phase 3 if needed.
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
