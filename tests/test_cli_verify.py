"""Tests for `refactron verify <file> --against <original>` command."""

from unittest.mock import patch

from click.testing import CliRunner

from refactron.cli.verify import verify
from refactron.verification.result import CheckResult, VerificationResult


def _make_vr(safe: bool) -> VerificationResult:
    cr = CheckResult(
        check_name="syntax",
        passed=safe,
        blocking_reason="" if safe else "SyntaxError: bad code",
        confidence=1.0 if safe else 0.0,
        duration_ms=5,
        details={},
    )
    return VerificationResult(
        safe_to_apply=safe,
        passed=safe,
        checks_run=["syntax"],
        checks_passed=["syntax"] if safe else [],
        checks_failed=[] if safe else ["syntax"],
        skipped_checks=[],
        blocking_reason=None if safe else "SyntaxError: bad code",
        confidence_score=1.0 if safe else 0.0,
        verification_ms=5,
        check_results=[cr],
    )


class TestVerifyCommand:
    def test_verify_exits_0_when_safe(self, tmp_path):
        original = tmp_path / "orig.py"
        transformed = tmp_path / "new.py"
        original.write_text("x = 1\n")
        transformed.write_text("x = 1\n")

        runner = CliRunner()
        with patch("refactron.cli.verify.VerificationEngine") as mock_cls:
            mock_cls.return_value.verify.return_value = _make_vr(safe=True)
            result = runner.invoke(verify, [str(transformed), "--against", str(original)])

        assert result.exit_code == 0

    def test_verify_exits_1_when_blocked(self, tmp_path):
        original = tmp_path / "orig.py"
        transformed = tmp_path / "new.py"
        original.write_text("x = 1\n")
        transformed.write_text("def bad(\n")

        runner = CliRunner()
        with patch("refactron.cli.verify.VerificationEngine") as mock_cls:
            mock_cls.return_value.verify.return_value = _make_vr(safe=False)
            result = runner.invoke(verify, [str(transformed), "--against", str(original)])

        assert result.exit_code == 1

    def test_verify_prints_check_results(self, tmp_path):
        original = tmp_path / "orig.py"
        transformed = tmp_path / "new.py"
        original.write_text("x = 1\n")
        transformed.write_text("x = 1\n")

        runner = CliRunner()
        with patch("refactron.cli.verify.VerificationEngine") as mock_cls:
            mock_cls.return_value.verify.return_value = _make_vr(safe=True)
            result = runner.invoke(verify, [str(transformed), "--against", str(original)])

        assert "syntax" in result.output
        assert "Safe to apply" in result.output

    def test_verify_missing_against_shows_error(self, tmp_path):
        transformed = tmp_path / "new.py"
        transformed.write_text("x = 1\n")

        runner = CliRunner()
        result = runner.invoke(verify, [str(transformed)])

        assert result.exit_code != 0
