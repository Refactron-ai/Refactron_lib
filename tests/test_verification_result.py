"""Contract tests for VerificationResult and CheckResult."""

import json

import pytest

from refactron.verification.report import format_verification_result_json
from refactron.verification.result import (
    JSON_SCHEMA_VERSION,
    CheckResult,
    VerificationResult,
)


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


def _sample_result(safe: bool) -> VerificationResult:
    cr = CheckResult(
        check_name="syntax",
        passed=safe,
        blocking_reason="" if safe else "SyntaxError on line 5",
        confidence=1.0 if safe else 0.0,
        duration_ms=12,
        details={"line": 5},
    )
    return VerificationResult(
        safe_to_apply=safe,
        passed=True,
        checks_run=["syntax"],
        checks_passed=["syntax"] if safe else [],
        checks_failed=[] if safe else ["syntax"],
        skipped_checks=[] if safe else [("test_suite", "Short-circuited after syntax failed")],
        blocking_reason=None if safe else "SyntaxError on line 5",
        confidence_score=1.0 if safe else 0.0,
        verification_ms=42,
        check_results=[cr],
    )


class TestCheckResultJson:
    def test_to_json_dict_has_all_fields(self):
        cr = CheckResult(
            check_name="syntax",
            passed=False,
            blocking_reason="boom",
            confidence=0.0,
            duration_ms=7,
            details={"k": "v"},
        )
        d = cr.to_json_dict()
        assert d == {
            "check_name": "syntax",
            "passed": False,
            "blocking_reason": "boom",
            "confidence": 0.0,
            "duration_ms": 7,
            "details": {"k": "v"},
        }


class TestVerificationResultJson:
    def test_to_json_dict_safe(self):
        d = _sample_result(safe=True).to_json_dict()
        assert d["schema_version"] == JSON_SCHEMA_VERSION
        assert d["status"] == "safe"
        assert d["safe_to_apply"] is True
        assert d["blocking_reason"] is None
        assert d["checks_run"] == ["syntax"]
        assert d["skipped_checks"] == []
        assert d["checks"][0]["check_name"] == "syntax"

    def test_to_json_dict_blocked(self):
        d = _sample_result(safe=False).to_json_dict()
        assert d["status"] == "blocked"
        assert d["safe_to_apply"] is False
        assert d["blocking_reason"] == "SyntaxError on line 5"
        assert d["checks_failed"] == ["syntax"]
        assert d["skipped_checks"] == [
            {"check_name": "test_suite", "reason": "Short-circuited after syntax failed"}
        ]

    def test_format_json_is_parseable(self):
        text = format_verification_result_json(_sample_result(safe=True))
        parsed = json.loads(text)
        assert parsed["schema_version"] == JSON_SCHEMA_VERSION
        assert parsed["status"] == "safe"
