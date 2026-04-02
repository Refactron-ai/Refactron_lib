"""VerificationEngine — pipeline orchestrator for verification checks."""

import math
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from refactron.verification.result import CheckResult, VerificationResult


class BaseCheck(ABC):
    """Abstract base class for all verification checks."""

    name: str

    @abstractmethod
    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        """Run this check and return a CheckResult."""
        ...


class VerificationEngine:
    """Orchestrates verification checks in a short-circuit pipeline."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        checks: Optional[List[BaseCheck]] = None,
    ):
        self.project_root = project_root
        self.checks: List[BaseCheck]
        if checks is not None:
            self.checks = checks
        else:
            from refactron.verification.checks.imports import ImportIntegrityVerifier
            from refactron.verification.checks.syntax import SyntaxVerifier
            from refactron.verification.checks.test_gate import TestSuiteGate

            self.checks = [
                SyntaxVerifier(),
                ImportIntegrityVerifier(),
                TestSuiteGate(project_root=project_root),
            ]

    def verify(self, original: str, transformed: str, file_path: Path) -> VerificationResult:
        """Run all checks in order, short-circuiting on first failure."""
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
                # Short-circuit: skip remaining checks
                for remaining in self.checks[i + 1 :]:
                    skipped_checks.append(
                        (remaining.name, f"Short-circuited after {check.name} failed")
                    )
                break

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
