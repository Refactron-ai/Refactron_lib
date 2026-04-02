"""End-to-end integration tests for the Verification Engine."""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestVerificationIntegration:
    def test_safe_extract_fixture_passes_verification(self):
        """fixture_safe_extract.py has genuinely unused import os — safe to remove."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_safe_extract.py"
        original = file_path.read_text(encoding="utf-8")
        transformed = original.replace(
            "import os  # noqa: F401 \u2014 intentionally unused (DEP001 trigger)\n", ""
        )
        assert transformed != original
        result = engine.verify(original, transformed, file_path)
        assert result.safe_to_apply is True

    def test_import_break_fixture_blocked(self):
        """fixture_import_break.py — removing collections breaks dotted access."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_import_break.py"
        original = file_path.read_text(encoding="utf-8")
        transformed = original.replace("import collections\n", "")
        result = engine.verify(original, transformed, file_path)
        assert result.safe_to_apply is False
        assert "collections" in (result.blocking_reason or "")

    def test_bad_extract_syntax_break(self):
        """fixture_bad_extract.py — removing eval line causes test failure via TestSuiteGate."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_bad_extract.py"
        original = file_path.read_text(encoding="utf-8")
        transformed = original.replace(
            "    result = eval(expression)  # SEC001 \u2014 dangerous function\n", ""
        )
        assert transformed != original
        result = engine.verify(original, transformed, file_path)
        assert result.safe_to_apply is False

    def test_clean_fixture_passes_all(self):
        """fixture_clean.py should pass all checks."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_clean.py"
        original = file_path.read_text(encoding="utf-8")
        result = engine.verify(original, original, file_path)
        assert result.safe_to_apply is True

    def test_test_break_signature_change_blocked(self):
        """Changing calculate_total signature should be blocked by test gate."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_test_break.py"
        original = file_path.read_text(encoding="utf-8")
        transformed = original.replace(
            "def calculate_total(items, tax_rate=0.1):",
            "def calculate_total(items):",
        ).replace(
            "return round(subtotal * (1 + tax_rate), 2)",
            "return round(subtotal * 1.1, 2)",
        )
        result = engine.verify(original, transformed, file_path)
        assert result.safe_to_apply is False

    def test_original_file_never_modified_on_block(self):
        """When verification blocks, the original file must be unchanged."""
        from refactron.verification import VerificationEngine

        engine = VerificationEngine(project_root=FIXTURES_DIR)
        file_path = FIXTURES_DIR / "fixture_import_break.py"
        original = file_path.read_text(encoding="utf-8")
        transformed = original.replace("import collections\n", "")
        engine.verify(original, transformed, file_path)
        after = file_path.read_text(encoding="utf-8")
        assert after == original

    def test_dry_run_and_verify_writes_nothing(self):
        """dry_run=True + verify=True should produce diff and result but write nothing."""
        from refactron.autofix.engine import AutoFixEngine
        from refactron.core.models import CodeIssue, IssueCategory, IssueLevel

        file_path = FIXTURES_DIR / "fixture_safe_extract.py"
        original = file_path.read_text(encoding="utf-8")

        engine = AutoFixEngine()
        issues = [
            CodeIssue(
                category=IssueCategory.DEPENDENCY,
                level=IssueLevel.WARNING,
                message="unused import",
                file_path=file_path,
                line_number=9,
                rule_id="DEP001",
            ),
        ]
        fixed_code, diff = engine.fix_file(file_path, issues, dry_run=True, verify=True)
        after = file_path.read_text(encoding="utf-8")
        assert after == original
