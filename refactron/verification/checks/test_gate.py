"""TestSuiteGate — Check 3: run relevant tests against transformed code."""

import ast
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from refactron.verification.engine import BaseCheck
from refactron.verification.result import CheckResult


class TestSuiteGate(BaseCheck):
    """Runs pytest on test files that import the changed module."""

    __test__ = False  # Prevent pytest from collecting this as a test class
    name = "test_gate"

    def __init__(
        self,
        project_root: Optional[Path] = None,
        timeout_sec: int = 45,
        pytest_extra_args: Optional[List[str]] = None,
    ):
        """Create the test-suite gate.

        Args:
            project_root: Project root pytest runs from.
            timeout_sec: Subprocess timeout for the pytest run (default 45s).
            pytest_extra_args: Extra arguments appended to the pytest command.
        """
        self.project_root = project_root
        self.timeout_sec = timeout_sec
        self.pytest_extra_args = list(pytest_extra_args or [])
        self._test_file_cache: Optional[Dict[str, List[Path]]] = None
        self._all_test_files: Optional[List[Path]] = None

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        start = time.monotonic()
        details: Dict[str, Any] = {}

        # Step 1-2: find test files that import this module
        test_files = self._find_relevant_tests(file_path)
        if not test_files:
            elapsed = int((time.monotonic() - start) * 1000)
            # No matching tests is not a failure, but it is also not the
            # strong assurance a passing test run gives — the change is
            # simply unverified here, so confidence is reduced rather than
            # left high (which would mask a potential false negative).
            details["note"] = "No tests found importing this module — change not covered by the gate"
            return CheckResult(
                check_name=self.name,
                passed=True,
                blocking_reason="",
                confidence=0.6,
                duration_ms=elapsed,
                details=details,
            )

        details["test_files"] = [str(f) for f in test_files]

        # Step 4-10: swap-and-restore
        backup_path = file_path.with_suffix(".py.refactron_backup")

        try:
            # Backup original
            shutil.copy2(file_path, backup_path)

            # Swap in transformed code
            file_path.write_text(transformed, encoding="utf-8")

            # Delete .pyc cache
            self._clear_pycache(file_path)

            # Run pytest from the project root with the host interpreter so
            # the repo's pyproject.toml / pytest.ini / conftest.py are picked
            # up and the same venv as the host process is used.
            run_cwd = (self.project_root or file_path.parent).resolve()

            # Make the project root importable for edge cases where the layout
            # relies on PYTHONPATH rather than an installed package.
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            existing_pythonpath = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                os.pathsep.join([str(run_cwd), existing_pythonpath])
                if existing_pythonpath
                else str(run_cwd)
            )

            cmd = [sys.executable, "-m", "pytest", "-x", "-q"]
            cmd += self.pytest_extra_args
            cmd += [str(f) for f in test_files]
            result = subprocess.run(
                cmd,
                timeout=self.timeout_sec,
                capture_output=True,
                text=True,
                env=env,
                cwd=str(run_cwd),
            )

            elapsed = int((time.monotonic() - start) * 1000)

            if result.returncode == 0:
                details["tests_passed"] = True
                return CheckResult(
                    check_name=self.name,
                    passed=True,
                    blocking_reason="",
                    confidence=0.9,
                    duration_ms=elapsed,
                    details=details,
                )
            else:
                output = (result.stdout + result.stderr)[:500]
                details["test_output"] = output
                return CheckResult(
                    check_name=self.name,
                    passed=False,
                    blocking_reason=f"Tests failed:\n{output}",
                    confidence=0.0,
                    duration_ms=elapsed,
                    details=details,
                )

        except subprocess.TimeoutExpired:
            elapsed = int((time.monotonic() - start) * 1000)
            return CheckResult(
                check_name=self.name,
                passed=False,
                blocking_reason=f"Test suite gate timed out ({self.timeout_sec}s limit)",
                confidence=0.0,
                duration_ms=elapsed,
                details=details,
            )
        finally:
            # Always restore original
            if backup_path.exists():
                os.replace(str(backup_path), str(file_path))

    def _find_relevant_tests(self, file_path: Path) -> List[Path]:
        """Find test files that import the module at file_path."""
        search_root = self.project_root or file_path.parent
        targets = self._module_targets(file_path)

        if self._test_file_cache is None:
            self._test_file_cache = {}
            self._all_test_files = []

            test_dirs = [d for d in [search_root / "tests", search_root / "test"] if d.is_dir()]
            search_dirs = test_dirs if test_dirs else [search_root]
            excluded_dirs = {".git", ".rag", "__pycache__", "venv", ".venv", "env", "node_modules"}

            for root_dir in search_dirs:
                for py_file in root_dir.rglob("*.py"):
                    if any(excluded in py_file.parts for excluded in excluded_dirs):
                        continue
                    name = py_file.name
                    if name.startswith("test_") or name.endswith("_test.py"):
                        self._all_test_files.append(py_file)

        cache_key = str(file_path)
        if cache_key in self._test_file_cache:
            return self._test_file_cache[cache_key]

        target_file = file_path.resolve()
        test_files: List[Path] = []
        for py_file in self._all_test_files:  # type: ignore
            if py_file == file_path:
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                if self._imports_module(source, targets, target_file, py_file):
                    test_files.append(py_file)
            except Exception:
                continue

        self._test_file_cache[cache_key] = test_files
        return test_files

    def _module_targets(self, file_path: Path) -> set:
        """Qualified module names a test could import to exercise file_path.

        Returns both the project-root-relative dotted path and the
        package-root-relative path (walking up the ``__init__.py`` chain), so
        ``mypkg/submodule/foo.py`` is matched by ``from mypkg.submodule import
        foo`` regardless of where the project is rooted. The bare stem is kept
        as a loose fallback for flat (non-package) layouts.
        """
        path = Path(file_path)
        abs_path = path.resolve()
        targets: set = set()
        if path.name != "__init__.py":
            targets.add(path.stem)

        # Project-root-relative qualified name.
        root = (self.project_root or path.parent)
        try:
            rel = abs_path.relative_to(root.resolve())
            dotted = self._dotted(rel)
            if dotted:
                targets.add(dotted)
        except ValueError:
            pass

        # Package-root-relative qualified name (walk up the __init__.py chain).
        parts: List[str] = [] if path.name == "__init__.py" else [path.stem]
        pkg_dir = abs_path.parent
        while (pkg_dir / "__init__.py").is_file():
            parts.append(pkg_dir.name)
            pkg_dir = pkg_dir.parent
        if parts:
            targets.add(".".join(reversed(parts)))

        return targets

    @staticmethod
    def _dotted(rel_path: Path) -> str:
        """Convert a relative file path to a dotted module name."""
        parts = list(rel_path.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    @staticmethod
    def _imports_module(
        source: str, targets: set, target_file: Path, test_path: Path
    ) -> bool:
        """Whether ``source`` imports the module under verification.

        Absolute imports are matched by qualified name against ``targets``;
        package-relative imports (``from . import x``) are resolved on the
        filesystem and compared directly to ``target_file``.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return False

        imported: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    if TestSuiteGate._relative_import_hits(node, test_path, target_file):
                        return True
                    continue
                base = node.module or ""
                if base:
                    imported.add(base)
                for alias in node.names:
                    imported.add(f"{base}.{alias.name}" if base else alias.name)

        for name in imported:
            for target in targets:
                if name == target or name.startswith(target + "."):
                    return True
        return False

    @staticmethod
    def _relative_import_hits(
        node: ast.ImportFrom, test_path: Path, target_file: Path
    ) -> bool:
        """Resolve a relative import to file paths and test against target."""
        base_dir = test_path.resolve().parent
        for _ in range(node.level - 1):
            base_dir = base_dir.parent
        if node.module:
            base_dir = base_dir.joinpath(*node.module.split("."))

        candidates = [base_dir.with_suffix(".py"), base_dir / "__init__.py"]
        for alias in node.names:
            candidates.append((base_dir / alias.name).with_suffix(".py"))
            candidates.append(base_dir / alias.name / "__init__.py")

        for cand in candidates:
            try:
                if cand.resolve() == target_file:
                    return True
            except OSError:
                continue
        return False

    @staticmethod
    def _clear_pycache(file_path: Path) -> None:
        """Remove .pyc files for this module to force re-import."""
        pycache = file_path.parent / "__pycache__"
        if pycache.exists():
            stem = file_path.stem
            for pyc in pycache.glob(f"{stem}.cpython-*.pyc"):
                try:
                    pyc.unlink()
                except Exception:
                    pass
