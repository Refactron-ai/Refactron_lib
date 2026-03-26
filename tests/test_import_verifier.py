"""Unit tests for ImportIntegrityVerifier (Check 2)."""

from pathlib import Path

import pytest

from refactron.verification.checks.imports import ImportIntegrityVerifier


@pytest.fixture
def verifier():
    return ImportIntegrityVerifier()


class TestImportIntegrityVerifier:
    def test_name(self, verifier):
        assert verifier.name == "import_integrity"

    def test_identical_code_passes(self, verifier):
        code = "import os\n\nos.getcwd()\n"
        cr = verifier.verify(code, code, Path("/tmp/t.py"))
        assert cr.passed is True

    def test_removed_import_still_used_as_name_blocks(self, verifier):
        original = "import os\nimport sys\n\nos.getcwd()\nsys.exit()\n"
        transformed = "import os\n\nos.getcwd()\nsys.exit()\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "sys" in cr.blocking_reason

    def test_removed_import_still_used_as_dotted_blocks(self, verifier):
        """The fixture_import_break.py scenario — collections.OrderedDict."""
        original = "import collections\nimport sys\n\ncollections.OrderedDict()\n"
        transformed = "import sys\n\ncollections.OrderedDict()\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "collections" in cr.blocking_reason

    def test_removed_unused_import_passes(self, verifier):
        original = "import os\nimport sys\n\nos.getcwd()\n"
        transformed = "import os\n\nos.getcwd()\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is True

    def test_new_import_resolvable_passes(self, verifier):
        original = "import os\n"
        transformed = "import os\nimport sys\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is True

    def test_new_import_unresolvable_blocks(self, verifier):
        original = "import os\n"
        transformed = "import os\nimport nonexistent_module_xyz_abc\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "nonexistent_module_xyz_abc" in cr.blocking_reason

    def test_from_import_tracked(self, verifier):
        original = "from os.path import join\n\njoin('a', 'b')\n"
        transformed = "\njoin('a', 'b')\n"
        cr = verifier.verify(original, transformed, Path("/tmp/t.py"))
        assert cr.passed is False
        assert "join" in cr.blocking_reason

    def test_confidence_1_when_passed(self, verifier):
        code = "import os\n\nos.getcwd()\n"
        cr = verifier.verify(code, code, Path("/tmp/t.py"))
        assert cr.confidence == 1.0

    def test_duration_populated(self, verifier):
        code = "x = 1\n"
        cr = verifier.verify(code, code, Path("/tmp/t.py"))
        assert cr.duration_ms >= 0
