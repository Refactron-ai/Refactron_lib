"""Unit tests for TestSuiteGate (Check 3)."""

from pathlib import Path

import pytest

from refactron.verification.checks.test_gate import TestSuiteGate

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def gate():
    return TestSuiteGate(project_root=FIXTURES_DIR)


class TestTestSuiteGate:
    def test_name(self, gate):
        assert gate.name == "test_gate"

    def test_no_tests_found_passes_with_skip(self, gate):
        """fixture_clean.py has no companion test file."""
        file_path = FIXTURES_DIR / "fixture_clean.py"
        original = file_path.read_text(encoding="utf-8")
        cr = gate.verify(original, original, file_path)
        assert cr.passed is True
        assert "No tests" in cr.details.get("note", "")

    def test_unchanged_code_passes_tests(self, gate):
        """fixture_test_break.py with its own code should pass its tests."""
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        cr = gate.verify(original, original, file_path)
        assert cr.passed is True

    def test_broken_transform_fails_tests(self, gate):
        """Changing the function signature should break tests."""
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        broken = original.replace(
            "def calculate_total(items, tax_rate=0.1):",
            "def calculate_total(items):",
        ).replace(
            "return round(subtotal * (1 + tax_rate), 2)",
            "return round(subtotal * 1.1, 2)",
        )
        cr = gate.verify(original, broken, file_path)
        assert cr.passed is False
        assert cr.blocking_reason

    def test_original_file_restored_after_check(self, gate):
        """The swap-and-restore must leave the original file intact."""
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        broken = original.replace("tax_rate=0.1", "tax_rate=0.999")
        gate.verify(original, broken, file_path)
        after = file_path.read_text(encoding="utf-8")
        assert after == original

    def test_original_restored_even_on_failure(self, gate):
        """Even when tests fail, the original must be restored."""
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        broken = "def calculate_total(): return 'BROKEN'\n"
        gate.verify(original, broken, file_path)
        after = file_path.read_text(encoding="utf-8")
        assert after == original

    def test_confidence_is_0_9(self, gate):
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        cr = gate.verify(original, original, file_path)
        assert cr.confidence == 0.9
