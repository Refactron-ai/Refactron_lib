"""Contract tests for VerificationResult and CheckResult."""

import pytest

from refactron.verification.result import CheckResult, VerificationResult


class TestCheckResult:
    def test_is_frozen(self):
        cr = CheckResult(
            check_name="syntax",
            passed=True,
            blocking_reason="",
            confidence=1.0,
            duration_ms=10,
            details={},
        )
        with pytest.raises(AttributeError):
            cr.passed = False

    def test_fields_accessible(self):
        cr = CheckResult(
            check_name="syntax",
            passed=False,
            blocking_reason="SyntaxError on line 5",
            confidence=0.0,
            duration_ms=42,
            details={"line": 5},
        )
        assert cr.check_name == "syntax"
        assert cr.passed is False
        assert cr.blocking_reason == "SyntaxError on line 5"
        assert cr.duration_ms == 42


class TestVerificationResult:
    def test_safe_to_apply_true_when_no_failures(self):
        vr = VerificationResult(
            safe_to_apply=True,
            passed=True,
            checks_run=["syntax"],
            checks_passed=["syntax"],
            checks_failed=[],
            skipped_checks=[],
            blocking_reason=None,
            confidence_score=1.0,
            verification_ms=10,
            check_results=[],
        )
        assert vr.safe_to_apply is True

    def test_safe_to_apply_false_when_failures(self):
        vr = VerificationResult(
            safe_to_apply=False,
            passed=True,
            checks_run=["syntax"],
            checks_passed=[],
            checks_failed=["syntax"],
            skipped_checks=[("import_integrity", "Short-circuited")],
            blocking_reason="SyntaxError",
            confidence_score=0.0,
            verification_ms=5,
            check_results=[],
        )
        assert vr.safe_to_apply is False
        assert vr.skipped_checks == [("import_integrity", "Short-circuited")]

    def test_is_frozen(self):
        vr = VerificationResult(
            safe_to_apply=True,
            passed=True,
            checks_run=[],
            checks_passed=[],
            checks_failed=[],
            skipped_checks=[],
            blocking_reason=None,
            confidence_score=0.0,
            verification_ms=0,
            check_results=[],
        )
        with pytest.raises(AttributeError):
            vr.safe_to_apply = False

    def test_confidence_zero_when_no_checks_passed(self):
        vr = VerificationResult(
            safe_to_apply=False,
            passed=True,
            checks_run=["syntax"],
            checks_passed=[],
            checks_failed=["syntax"],
            skipped_checks=[],
            blocking_reason="fail",
            confidence_score=0.0,
            verification_ms=5,
            check_results=[],
        )
        assert vr.confidence_score == 0.0
