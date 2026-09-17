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


def _make_pkg(root: Path) -> Path:
    """Create a minimal `pkg` package: a.py (no imports) + b.py -> a."""
    pkg = root / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (pkg / "b.py").write_text("from . import a\n\nprint(a.VALUE)\n", encoding="utf-8")
    return pkg


class TestImportCycleDetection:
    """Step 4 — project-wide import-cycle detection."""

    def test_transform_introducing_cycle_blocks(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        verifier = ImportIntegrityVerifier(project_root=tmp_path)
        original = (pkg / "a.py").read_text(encoding="utf-8")
        # a.py now imports b, while b.py already imports a -> cycle.
        transformed = "from . import b\n\nVALUE = b\n"
        cr = verifier.verify(original, transformed, pkg / "a.py")
        assert cr.passed is False
        assert "cycle" in cr.blocking_reason.lower()
        assert "pkg.a" in cr.blocking_reason and "pkg.b" in cr.blocking_reason
        assert cr.details["import_cycle"][0] == "pkg.a"
        assert cr.details["import_cycle"][-1] == "pkg.a"

    def test_transform_without_cycle_passes(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        (pkg / "c.py").write_text("C = 1\n", encoding="utf-8")
        verifier = ImportIntegrityVerifier(project_root=tmp_path)
        original = (pkg / "a.py").read_text(encoding="utf-8")
        transformed = "from . import c\n\nVALUE = c.C\n"
        cr = verifier.verify(original, transformed, pkg / "a.py")
        assert cr.passed is True
        assert cr.details["cycle_check"] == "ran: no cycle"

    def test_preexisting_cycle_not_blocked(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        # a <-> b are already cyclic on disk.
        (pkg / "a.py").write_text("from . import b\n", encoding="utf-8")
        (pkg / "b.py").write_text("from . import a\n", encoding="utf-8")
        (pkg / "c.py").write_text("C = 1\n", encoding="utf-8")
        verifier = ImportIntegrityVerifier(project_root=tmp_path)
        original = (pkg / "a.py").read_text(encoding="utf-8")
        transformed = "from . import b\nfrom . import c\n"
        cr = verifier.verify(original, transformed, pkg / "a.py")
        assert cr.passed is True
        assert cr.details["cycle_check"].startswith("ran: pre-existing")

    def test_cycle_check_skipped_without_project_root(self):
        verifier = ImportIntegrityVerifier()
        cr = verifier.verify("VALUE = 1\n", "from . import b\n", Path("/tmp/x.py"))
        assert cr.passed is True
        assert cr.details["cycle_check"] == "skipped: no project_root"

    def test_file_outside_project_root_skips_cycle_check(self, tmp_path):
        _make_pkg(tmp_path)
        verifier = ImportIntegrityVerifier(project_root=tmp_path)
        cr = verifier.verify("VALUE = 1\n", "from . import b\n", Path("/elsewhere/x.py"))
        assert cr.passed is True
        assert cr.details["cycle_check"] == "skipped: file outside project_root"
