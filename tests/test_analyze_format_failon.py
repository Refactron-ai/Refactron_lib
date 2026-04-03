"""Tests for --format json and --fail-on flags on refactron analyze."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from refactron.cli.analysis import analyze
from refactron.core.analysis_result import AnalysisResult
from refactron.core.models import CodeIssue, FileMetrics, IssueCategory, IssueLevel


def _make_result(issues=None, files=1):
    first = FileMetrics(
        file_path=Path("/tmp/foo.py"),
        lines_of_code=10,
        comment_lines=0,
        blank_lines=0,
        complexity=1.0,
        maintainability_index=100.0,
        functions=0,
        classes=0,
        issues=issues or [],
    )
    rest = [
        FileMetrics(
            file_path=Path(f"/tmp/foo{i}.py"),
            lines_of_code=10,
            comment_lines=0,
            blank_lines=0,
            complexity=1.0,
            maintainability_index=100.0,
            functions=0,
            classes=0,
        )
        for i in range(files - 1)
    ]
    return AnalysisResult(file_metrics=[first] + rest)


def _make_issue(level=IssueLevel.CRITICAL, msg="bad thing"):
    return CodeIssue(
        category=IssueCategory.COMPLEXITY,
        level=level,
        message=msg,
        file_path=Path("/tmp/foo.py"),
        line_number=10,
        column=0,
        suggestion=None,
    )


class TestFormatJson:
    def test_json_output_is_valid_json(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result()

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(analyze, [str(tmp_path), "--format", "json", "--no-interactive"])

        data = json.loads(out.output)
        assert "total_files" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_json_output_contains_issue_fields(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        issue = _make_issue()
        result = _make_result(issues=[issue])

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(analyze, [str(tmp_path), "--format", "json", "--no-interactive"])

        data = json.loads(out.output)
        assert data["critical"] == 1
        assert data["issues"][0]["level"] == "CRITICAL"
        assert data["issues"][0]["message"] == "bad thing"
        assert data["issues"][0]["line"] == 10

    def test_json_format_suppresses_rich_output(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result()

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(analyze, [str(tmp_path), "--format", "json", "--no-interactive"])

        # Should be parseable JSON — no Rich markup in output
        json.loads(out.output)  # raises if markup present


class TestFailOn:
    def test_fail_on_critical_exits_1_when_critical_exists(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result(issues=[_make_issue(IssueLevel.CRITICAL)])

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(
                analyze,
                [str(tmp_path), "--fail-on", "CRITICAL", "--no-interactive"],
            )

        assert out.exit_code == 1

    def test_fail_on_critical_exits_0_when_only_warnings(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result(issues=[_make_issue(IssueLevel.WARNING)])

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(
                analyze,
                [str(tmp_path), "--fail-on", "CRITICAL", "--no-interactive"],
            )

        assert out.exit_code == 0

    def test_fail_on_warning_exits_1_when_warning_exists(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result(issues=[_make_issue(IssueLevel.WARNING)])

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(
                analyze,
                [str(tmp_path), "--fail-on", "WARNING", "--no-interactive"],
            )

        assert out.exit_code == 1

    def test_no_fail_on_exits_0_when_no_critical(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        result = _make_result(issues=[_make_issue(IssueLevel.WARNING)])

        with patch("refactron.cli.analysis.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = result
            out = runner.invoke(analyze, [str(tmp_path), "--no-interactive"])

        assert out.exit_code == 0
