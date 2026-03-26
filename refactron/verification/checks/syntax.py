"""SyntaxVerifier — Check 1: syntax validation, CST roundtrip, dangerous calls."""

import ast
import time
from pathlib import Path
from typing import Any, Dict, Set

from refactron.verification.engine import BaseCheck
from refactron.verification.result import CheckResult


class SyntaxVerifier(BaseCheck):
    """Validates that transformed code has valid syntax and no new dangerous calls."""

    name = "syntax"

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        start = time.monotonic()
        details: Dict[str, Any] = {}

        # Step 1: ast.parse
        try:
            ast.parse(transformed, filename=str(file_path))
        except SyntaxError as e:
            return self._fail(
                f"SyntaxError: {e.msg} (line {e.lineno})",
                start,
                details,
            )

        # Step 2: libcst roundtrip
        try:
            import libcst

            tree = libcst.parse_module(transformed)
            roundtripped = tree.code
            libcst.parse_module(roundtripped)
        except Exception as e:
            return self._fail(
                f"CST round-trip failed: {e}",
                start,
                details,
            )

        # Step 3: new dangerous calls
        original_calls = self._find_dangerous_calls(original)
        transformed_calls = self._find_dangerous_calls(transformed)
        new_calls = transformed_calls - original_calls
        if new_calls:
            details["new_dangerous_calls"] = sorted(new_calls)
            return self._fail(
                f"New dangerous call(s) introduced: {', '.join(sorted(new_calls))}",
                start,
                details,
            )

        # Step 4: import count comparison (full reference check is in ImportIntegrityVerifier)
        orig_import_count = self._count_imports(original)
        trans_import_count = self._count_imports(transformed)
        if trans_import_count < orig_import_count:
            details["imports_removed"] = orig_import_count - trans_import_count

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
    def _find_dangerous_calls(code: str) -> Set[str]:
        """Find all calls to eval/exec/os.system in the code."""
        dangerous: Set[str] = set()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return dangerous

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    dangerous.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os"
                        and node.func.attr == "system"
                    ):
                        dangerous.add("os.system")
        return dangerous

    @staticmethod
    def _count_imports(code: str) -> int:
        """Count import statements in code."""
        count = 0
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                count += 1
        return count
