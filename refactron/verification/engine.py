"""VerificationEngine — pipeline orchestrator for verification checks."""

import math
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from refactron.verification.result import CheckResult, VerificationResult

if TYPE_CHECKING:
    from refactron.core.config import VerificationConfig


class BaseCheck(ABC):
    """Abstract base class for all verification checks."""

    name: str

    @abstractmethod
    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        """Run this check and return a CheckResult."""
        ...


class VerificationEngine:
    """Orchestrates verification checks, short-circuiting by default."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        checks: Optional[List[BaseCheck]] = None,
        config: Optional["VerificationConfig"] = None,
    ):
        """Build a verification pipeline.

        Args:
            project_root: Project root, used by import and test-gate checks.
            checks: Explicit check list — bypasses ``config`` entirely.
            config: VerificationConfig controlling which checks run, in what
                order, and with what test-gate timeout / pytest args. When
                None, defaults reproduce the historical behaviour.
        """
        from refactron.core.config import VerificationConfig

        self.project_root = project_root
        self.config = config or VerificationConfig()
        self.checks: List[BaseCheck]
        if checks is not None:
            self.checks = checks
        else:
            self.checks = self._build_checks(self.config, project_root)

    @staticmethod
    def _build_checks(
        config: "VerificationConfig", project_root: Optional[Path]
    ) -> List[BaseCheck]:
        """Instantiate the configured checks, in the configured order."""
        from refactron.verification.checks.imports import ImportIntegrityVerifier
        from refactron.verification.checks.syntax import SyntaxVerifier
        from refactron.verification.checks.test_gate import TestSuiteGate

        factories = {
            "syntax": lambda: SyntaxVerifier(),
            "import_integrity": lambda: ImportIntegrityVerifier(
                project_root=project_root
            ),
            "test_gate": lambda: TestSuiteGate(
                project_root=project_root,
                timeout_sec=config.test_gate_timeout_sec,
                pytest_extra_args=config.pytest_extra_args,
            ),
        }
        checks: List[BaseCheck] = []
        for name in config.enabled_checks:
            factory = factories.get(name)
            if factory is None:
                raise ValueError(
                    f"Unknown verification check: {name!r}. "
                    f"Valid checks: {sorted(factories)}"
                )
            checks.append(factory())
        return checks

    def verify(
        self,
        original: str,
        transformed: str,
        file_path: Path,
        short_circuit: Optional[bool] = None,
    ) -> VerificationResult:
        """Run the verification checks in order and aggregate the results.

        Args:
            original: Source code before the transform.
            transformed: Source code after the transform.
            file_path: Path of the file within the project.
            short_circuit: When True, stop after the first failing check and
                record the rest in ``skipped_checks`` — fastest, but hides
                stacked problems. When False, run every check so the caller
                sees all failure categories in a single run; nothing is
                skipped. ``blocking_reason`` is always the first failure.
                When None (default), the engine's configured value is used.
        """
        if short_circuit is None:
            short_circuit = self.config.short_circuit
        start = time.monotonic()
        check_results: List[CheckResult] = []
        checks_run: List[str] = []
        checks_passed: List[str] = []
        checks_failed: List[str] = []
        skipped_checks: List[tuple] = []
        blocking_reason: Optional[str] = None
        passed = True

        for i, check in enumerate(self.checks):
            try:
                cr = check.verify(original, transformed, file_path)
            except Exception as exc:
                cr = CheckResult(
                    check_name=check.name,
                    passed=False,
                    blocking_reason=f"Check raised exception: {exc}",
                    confidence=0.0,
                    duration_ms=0,
                    details={"exception": str(exc)},
                )
                passed = False

            check_results.append(cr)
            checks_run.append(check.name)

            if cr.passed:
                checks_passed.append(check.name)
            else:
                checks_failed.append(check.name)
                if blocking_reason is None:
                    blocking_reason = cr.blocking_reason
                if short_circuit:
                    # Skip remaining checks and stop the pipeline.
                    for remaining in self.checks[i + 1 :]:
                        skipped_checks.append(
                            (remaining.name, f"Short-circuited after {check.name} failed")
                        )
                    break
                # short_circuit=False: keep going so every failure surfaces.

        elapsed_ms = int((time.monotonic() - start) * 1000)
        confidence = self._compute_confidence(check_results)
        safe = passed and len(checks_failed) == 0

        return VerificationResult(
            safe_to_apply=safe,
            passed=passed,
            checks_run=checks_run,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            skipped_checks=skipped_checks,
            blocking_reason=blocking_reason,
            confidence_score=confidence,
            verification_ms=elapsed_ms,
            check_results=check_results,
        )

    @staticmethod
    def _compute_confidence(results: List[CheckResult]) -> float:
        """Geometric mean of passed checks' confidence. 0.0 if none passed."""
        passed = [r.confidence for r in results if r.passed]
        if not passed:
            return 0.0
        return float(math.prod(passed) ** (1.0 / len(passed)))
