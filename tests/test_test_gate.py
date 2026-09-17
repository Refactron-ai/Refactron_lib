"""Unit tests for TestSuiteGate (Check 3)."""

import os
import sys
from pathlib import Path

import pytest

from refactron.verification.checks import test_gate as test_gate_module
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


class TestPackageImportMatching:
    """Relevance matching must handle qualified package imports, not just stems."""

    def _layout(self, tmp_path: Path, test_import: str):
        """Create mypkg/submodule/foo.py and tests/test_foo.py importing it."""
        pkg = tmp_path / "mypkg" / "submodule"
        pkg.mkdir(parents=True)
        (tmp_path / "mypkg" / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        foo = pkg / "foo.py"
        foo.write_text("def f():\n    return 1\n", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        test_file = tests / "test_foo.py"
        test_file.write_text(
            f"{test_import}\n\n\ndef test_it():\n    assert True\n", encoding="utf-8"
        )
        return foo, test_file

    def test_qualified_from_import_matches(self, tmp_path):
        """from mypkg.submodule import foo  ->  matches mypkg/submodule/foo.py."""
        foo, test_file = self._layout(tmp_path, "from mypkg.submodule import foo")
        gate = TestSuiteGate(project_root=tmp_path)
        assert test_file in gate._find_relevant_tests(foo)

    def test_dotted_import_matches(self, tmp_path):
        """import mypkg.submodule.foo  ->  matches the file under verification."""
        foo, test_file = self._layout(tmp_path, "import mypkg.submodule.foo")
        gate = TestSuiteGate(project_root=tmp_path)
        assert test_file in gate._find_relevant_tests(foo)

    def test_unrelated_import_does_not_match(self, tmp_path):
        foo, _ = self._layout(tmp_path, "import os")
        gate = TestSuiteGate(project_root=tmp_path)
        assert gate._find_relevant_tests(foo) == []

    def test_relative_import_matches(self, tmp_path):
        """from . import foo  in a test inside the package is attributed."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        foo = pkg / "foo.py"
        foo.write_text("def f():\n    return 1\n", encoding="utf-8")
        test_file = pkg / "test_foo.py"
        test_file.write_text(
            "from . import foo\n\n\ndef test_it():\n    assert foo.f() == 1\n",
            encoding="utf-8",
        )
        gate = TestSuiteGate(project_root=tmp_path)
        assert test_file in gate._find_relevant_tests(foo)

    def test_no_tests_yields_reduced_confidence(self, tmp_path):
        """An uncovered change is passed but with reduced (not high) confidence."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        foo = pkg / "foo.py"
        foo.write_text("X = 1\n", encoding="utf-8")
        gate = TestSuiteGate(project_root=tmp_path)
        cr = gate.verify("X = 1\n", "X = 1\n", foo)
        assert cr.passed is True
        assert cr.confidence == 0.6
        assert "not covered" in cr.details["note"]


class TestPytestInvocation:
    """The pytest subprocess must use the host interpreter and project root."""

    def _capture_run(self, monkeypatch):
        """Patch subprocess.run to capture its arguments without running pytest."""
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["cwd"] = kwargs.get("cwd")
            captured["env"] = kwargs.get("env")

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        monkeypatch.setattr(test_gate_module.subprocess, "run", fake_run)
        return captured

    def test_uses_host_interpreter(self, monkeypatch):
        """pytest must run via sys.executable, not a hard-coded python3."""
        captured = self._capture_run(monkeypatch)
        gate = TestSuiteGate(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")

        gate.verify(original, original, file_path)

        assert captured["cmd"][0] == sys.executable
        assert captured["cmd"][1:4] == ["-m", "pytest", "-x"]

    def test_cwd_is_resolved_project_root(self, monkeypatch):
        """pytest must run from the resolved project root, not file_path.parent."""
        captured = self._capture_run(monkeypatch)
        gate = TestSuiteGate(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")

        gate.verify(original, original, file_path)

        assert captured["cwd"] == str(FIXTURES_DIR.resolve())

    def test_project_root_added_to_pythonpath(self, monkeypatch):
        """The project root must be present on PYTHONPATH for the subprocess."""
        captured = self._capture_run(monkeypatch)
        gate = TestSuiteGate(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")

        gate.verify(original, original, file_path)

        pythonpath = captured["env"]["PYTHONPATH"].split(os.pathsep)
        assert str(FIXTURES_DIR.resolve()) in pythonpath
