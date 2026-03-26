"""Tests for fixture_bad_extract.py — enables TestSuiteGate verification."""

from fixture_bad_extract import build_query, dynamic_dispatch


def test_dynamic_dispatch_returns_value():
    result = dynamic_dispatch("1 + 2")
    assert result == 3


def test_dynamic_dispatch_fallback():
    result = dynamic_dispatch("None", fallback=42)
    assert result == 42


def test_build_query():
    query = build_query("users", ["id", "name"])
    assert query == "SELECT id, name FROM users"
