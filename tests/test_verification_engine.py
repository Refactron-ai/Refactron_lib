"""Tests for VerificationEngine pipeline orchestration."""

from pathlib import Path

from refactron.verification.engine import BaseCheck, VerificationEngine
from refactron.verification.result import CheckResult


class _PassingCheck(BaseCheck):
    name = "always_pass"

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        return CheckResult(
            check_name=self.name,
            passed=True,
            blocking_reason="",
            confidence=1.0,
            duration_ms=1,
            details={},
        )


class _FailingCheck(BaseCheck):
    name = "always_fail"

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        return CheckResult(
            check_name=self.name,
            passed=False,
            blocking_reason="Intentional failure",
            confidence=0.0,
            duration_ms=1,
            details={},
        )


class _TrackingCheck(BaseCheck):
    """Records whether verify() was called."""

    name = "tracker"

    def __init__(self):
        self.called = False

    def verify(self, original: str, transformed: str, file_path: Path) -> CheckResult:
        self.called = True
        return CheckResult(
            check_name=self.name,
            passed=True,
            blocking_reason="",
            confidence=0.9,
            duration_ms=2,
            details={},
        )


class TestVerificationEngine:
    def test_all_pass_returns_safe(self):
        engine = VerificationEngine(checks=[_PassingCheck(), _PassingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        assert result.safe_to_apply is True
        assert result.checks_failed == []
        assert len(result.checks_passed) == 2

    def test_first_fail_short_circuits(self):
        tracker = _TrackingCheck()
        engine = VerificationEngine(checks=[_FailingCheck(), tracker])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        assert result.safe_to_apply is False
        assert result.checks_failed == ["always_fail"]
        assert tracker.called is False  # short-circuited
        assert ("tracker", "Short-circuited after always_fail failed") in result.skipped_checks

    def test_confidence_is_geometric_mean(self):
        engine = VerificationEngine(checks=[_PassingCheck(), _TrackingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        # geometric mean of 1.0 and 0.9 = sqrt(0.9) ≈ 0.9487
        assert 0.94 < result.confidence_score < 0.96

    def test_confidence_zero_when_no_pass(self):
        engine = VerificationEngine(checks=[_FailingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        assert result.confidence_score == 0.0

    def test_verification_ms_is_positive(self):
        engine = VerificationEngine(checks=[_PassingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        assert result.verification_ms >= 0

    def test_passed_true_even_when_check_cleanly_fails(self):
        engine = VerificationEngine(checks=[_FailingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        # passed=True because the check ran without exceptions
        assert result.passed is True
        assert result.safe_to_apply is False

    def test_exception_in_check_sets_passed_false(self):
        class _CrashingCheck(BaseCheck):
            name = "crasher"

            def verify(self, original, transformed, file_path):
                raise RuntimeError("boom")

        engine = VerificationEngine(checks=[_CrashingCheck()])
        result = engine.verify("a = 1", "a = 1", Path("/tmp/test.py"))
        assert result.passed is False
        assert result.safe_to_apply is False
        assert "boom" in (result.blocking_reason or "")


class TestVerificationEngineWithRealChecks:
    """Tests using the real SyntaxVerifier and ImportIntegrityVerifier."""

    def test_default_engine_has_three_checks(self):
        engine = VerificationEngine(project_root=Path("/tmp"))
        assert len(engine.checks) == 3
        names = [c.name for c in engine.checks]
        assert names == ["syntax", "import_integrity", "test_gate"]

    def test_clean_code_passes_all(self):
        engine = VerificationEngine(project_root=Path("/tmp"))
        code = "import os\n\nos.getcwd()\n"
        result = engine.verify(code, code, Path("/tmp/test.py"))
        assert result.safe_to_apply is True

    def test_syntax_error_short_circuits(self):
        engine = VerificationEngine(project_root=Path("/tmp"))
        original = "x = 1\n"
        broken = "x = (\n"
        result = engine.verify(original, broken, Path("/tmp/test.py"))
        assert result.safe_to_apply is False
        assert "syntax" in result.checks_failed
        assert any("import_integrity" in s[0] for s in result.skipped_checks)
