"""Locked data contracts for the Verification Engine.

These dataclasses are frozen — do not change their fields once locked.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Bumped whenever the JSON shape produced by ``to_json_dict`` changes in a
# way consumers must adapt to. Additive fields do not require a bump.
JSON_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CheckResult:
    """Output from a single verification check."""

    check_name: str
    passed: bool
    blocking_reason: str
    confidence: float
    duration_ms: int
    details: Dict[str, Any]

    def to_json_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict of this check's result."""
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "blocking_reason": self.blocking_reason,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


@dataclass(frozen=True)
class VerificationResult:
    """Aggregated output from the full verification pipeline.

    Field invariants:
    - passed: all checks that ran completed without unexpected exceptions
    - safe_to_apply: passed AND len(checks_failed) == 0
    - confidence_score: geometric mean of passed checks. 0.0 when none pass.
    """

    safe_to_apply: bool
    passed: bool
    checks_run: List[str]
    checks_passed: List[str]
    checks_failed: List[str]
    skipped_checks: List[Tuple[str, str]]
    blocking_reason: Optional[str]
    confidence_score: float
    verification_ms: int
    check_results: List[CheckResult]

    def to_json_dict(self) -> Dict[str, Any]:
        """Return a stable, JSON-serializable dict of the full result.

        The shape is versioned via ``schema_version`` so machine consumers
        (CI gates, bots, parent tools) can evolve safely. Adding new keys is
        backwards-compatible; removing or renaming keys bumps the version.
        """
        return {
            "schema_version": JSON_SCHEMA_VERSION,
            "status": "safe" if self.safe_to_apply else "blocked",
            "safe_to_apply": self.safe_to_apply,
            "passed": self.passed,
            "blocking_reason": self.blocking_reason,
            "confidence_score": self.confidence_score,
            "verification_ms": self.verification_ms,
            "checks_run": list(self.checks_run),
            "checks_passed": list(self.checks_passed),
            "checks_failed": list(self.checks_failed),
            "skipped_checks": [
                {"check_name": name, "reason": reason}
                for name, reason in self.skipped_checks
            ],
            "checks": [cr.to_json_dict() for cr in self.check_results],
        }
