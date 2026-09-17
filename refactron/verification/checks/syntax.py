import ast
from typing import Optional
from refactron.verification.engine import BaseCheck, VerificationContext

# Module-level cache for lazy libcst loading
_libcst_module = None

def _get_libcst():
    global _libcst_module
    if _libcst_module is None:
        import libcst as cst
        _libcst_module = cst
    return _libcst_module


class SyntaxVerifier(BaseCheck):
    def _find_dangerous_calls(self, tree: ast.AST) -> int:
        dangerous_calls = {"eval", "exec", "system", "popen"}
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                    count += 1
                elif isinstance(node.func, ast.Attribute) and node.func.attr in dangerous_calls:
                    count += 1
        return count

    def _count_imports(self, tree: ast.AST) -> int:
        count = 0
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

    def verify(self, original: str, transformed: str, context: Optional[VerificationContext] = None) -> bool:
        """
        Verify the syntax of the transformed code.
        Uses shared VerificationContext to avoid redundant AST parsing.
        """
        # If the VerificationEngine already tried to parse it and failed, the syntax implies it's broken
        if context and context.transformed_ast is None and transformed.strip() != "":
            return False
            
        tree = context.transformed_ast if context else None
        
        # Fallback to local parsing for backward compatibility 
        if tree is None:
            try:
                tree = ast.parse(transformed)
            except Exception:
                return False

        # Reuse the single AST for analytical sweeps to save redundant walks
        dangerous = self._find_dangerous_calls(tree)
        if dangerous > 0:
            return False  # Abort on dangerous structural patterns
            
        _ = self._count_imports(tree)
            
        # Optional: libcst parsing could also be cached, but for now we fallback 
        # Lazy libcst loading significantly speeds up the hot loop.
        cst = _get_libcst()
        try:
            cst.parse_module(transformed)
        except Exception:
            return False
                
        return True
