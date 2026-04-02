"""Tests for fixture_test_break.calculate_total().

These tests exercise the exact public signature of ``calculate_total``
including the ``tax_rate`` keyword argument.  If autofix changes the
function signature, these tests must fail — and the TestSuiteGate
should block the transform.
"""

import sys
from pathlib import Path

# Ensure the fixtures directory is importable
sys.path.insert(0, str(Path(__file__).parent))

from fixture_test_break import calculate_total  # noqa: E402


def test_basic_total():
    assert calculate_total([10, 20, 30]) == 66.0


def test_custom_tax_rate():
    result = calculate_total([10, 20, 30], tax_rate=0.2)
    assert result == 72.0


def test_discount_applied_above_threshold():
    # subtotal = 200, discount = 10, taxed = 190 * 1.1 = 209.0
    result = calculate_total([100, 100])
    assert result == 209.0


def test_no_discount_below_threshold():
    # subtotal = 50, no discount, taxed = 50 * 1.1 = 55.0
    result = calculate_total([20, 30])
    assert result == 55.0


def test_empty_items():
    assert calculate_total([]) == 0.0
