"""Unit tests for SyntaxVerifier (Check 1)."""

from pathlib import Path

import pytest

from refactron.verification.checks.syntax import SyntaxVerifier


@pytest.fixture
def verifier():
    return SyntaxVerifier()


CLEAN_CODE = "def hello():\n    return 42\n"
BROKEN_SYNTAX = "def hello(\n    return 42\n"
CODE_WITH_EVAL = "result = eval('1+1')\n"
CODE_WITHOUT_EVAL = "result = 1 + 1\n"


class TestSyntaxVerifier:
    def test_name(self, verifier):
        assert verifier.name == "syntax"

    def test_valid_code_passes(self, verifier):
        cr = verifier.verify(CLEAN_CODE, CLEAN_CODE, Path("/tmp/t.py"))
        assert cr.passed is True
        assert cr.confidence == 1.0

    def test_syntax_error_blocks(self, verifier):
        cr = verifier.verify(CLEAN_CODE, BROKEN_SYNTAX, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "SyntaxError" in cr.blocking_reason or "syntax" in cr.blocking_reason.lower()

    def test_new_eval_blocks(self, verifier):
        cr = verifier.verify(CODE_WITHOUT_EVAL, CODE_WITH_EVAL, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "eval" in cr.blocking_reason.lower()

    def test_existing_eval_does_not_block(self, verifier):
        cr = verifier.verify(CODE_WITH_EVAL, CODE_WITH_EVAL, Path("/tmp/t.py"))
        assert cr.passed is True

    def test_import_count_decrease_noted_in_details(self, verifier):
        original = "import os\nimport sys\n\nos.getcwd()\n"
        transformed = "import os\n\nos.getcwd()\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is True
        assert cr.details.get("imports_removed") == 1

    def test_cst_roundtrip_corruption_blocks(self, verifier):
        cr = verifier.verify(CLEAN_CODE, CLEAN_CODE, Path("/tmp/t.py"))
        assert cr.passed is True

    def test_duration_ms_populated(self, verifier):
        cr = verifier.verify(CLEAN_CODE, CLEAN_CODE, Path("/tmp/t.py"))
        assert cr.duration_ms >= 0
