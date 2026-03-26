"""Locked data contracts for the Verification Engine.

These dataclasses are frozen — do not change their fields once locked.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CheckResult:
    """Output from a single verification check."""

    check_name: str
    passed: bool
    blocking_reason: str
    confidence: float
    duration_ms: int
    details: Dict[str, Any]


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
