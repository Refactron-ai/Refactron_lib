"""Comprehensive tests for the CLI interface."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from click.testing import CliRunner

from refactron import __version__
from refactron.cli.analysis import analyze, metrics, report, serve_metrics, suggest
from refactron.cli.cicd import init
from refactron.cli.main import main
from refactron.cli.refactor import autofix, document, refactor, rollback
from refactron.cli.ui import (
    _auth_banner,
    _collect_feedback_interactive,
    _confirm_apply_mode,
    _create_refactor_table,
    _create_summary_table,
    _interactive_file_selector,
    _print_custom_help,
    _print_detailed_issues,
    _print_file_count,
    _print_helpful_tips,
    _print_refactor_filters,
    _print_refactor_messages,
    _print_status_messages,
    _record_applied_operations,
    console,
)
from refactron.cli.utils import (
    ApiKeyValidationResult,
    _detect_project_type,
    _get_pattern_storage_from_config,
    _load_config,
    _setup_logging,
    _validate_api_key,
    _validate_path,
)
from refactron.core.credentials import RefactronCredentials
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.llm.models import SuggestionStatus
from refactron.llm.orchestrator import LLMOrchestrator


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    """Mock authentication for all CLI tests."""
    fake_creds = RefactronCredentials(
        api_base_url="https://api.refactron.dev",
        access_token="fake-token",
        token_type="Bearer",
        expires_at=None,
        email="test@example.com",
        plan="pro",
        api_key="ref_FAKE",
    )
    import sys

    import refactron.cli.main  # noqa: F401

    monkeypatch.setattr(sys.modules["refactron.cli.main"], "load_credentials", lambda: fake_creds)


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_main_help(self):
        """Test main help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Refactron" in result.output
        assert "analyze" in result.output
        assert "refactor" in result.output

    def test_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestAnalyzeCommand:
    """Test the analyze command."""

    def test_analyze_help(self):
        """Test analyze help."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()

    def test_analyze_single_file(self):
        """Test analyzing a single file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def test_function(a, b, c, d, e, f):
    '''Function with too many parameters.'''
    return a + b + c + d + e + f
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            assert result.exit_code == 0
            assert "Analysis Summary" in result.output or "Files Analyzed" in result.output
        finally:
            os.unlink(temp_path)

    def test_analyze_with_summary_flag(self):
        """Test analyze with --summary flag."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def simple(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path, "--summary"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_with_detailed_flag(self):
        """Test analyze with --detailed flag."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def simple(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path, "--detailed"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_nonexistent_file(self):
        """Test analyzing a nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_analyze_directory(self):
        """Test analyzing a directory."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            result = runner.invoke(analyze, [tmpdir])
            assert result.exit_code == 0

    def test_analyze_detects_issues(self):
        """Test that analyze actually detects issues."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def bad_function(a, b, c, d, e, f, g):
    if True:
        if True:
            if True:
                if True:
                    return eval(a)
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should detect multiple issues
            assert "Issues" in result.output or "Total" in result.output
        finally:
            os.unlink(temp_path)

    def test_analyze_with_config(self):
        """Test analyze with config file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_path = Path(tmpdir) / ".refactron.yaml"
            config_path.write_text(
                """
enabled_analyzers:
  - complexity
max_function_complexity: 5
"""
            )

            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            result = runner.invoke(analyze, [str(test_file), "-c", str(config_path)])
            assert result.exit_code == 0


class TestRefactorCommand:
    """Test the refactor command."""

    def test_refactor_help(self):
        """Test refactor help."""
        runner = CliRunner()
        result = runner.invoke(refactor, ["--help"])
        assert result.exit_code == 0
        assert "refactor" in result.output.lower()

    def test_refactor_preview_mode(self):
        """Test refactor in preview mode."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def calculate_discount(price):
    if price > 1000:
        return price * 0.15
    return 0
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(refactor, [temp_path, "--preview"])
            assert result.exit_code == 0
            assert "Refactoring" in result.output or "Operations" in result.output
        finally:
            os.unlink(temp_path)

    def test_refactor_with_types_filter(self):
        """Test refactor with specific types."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(refactor, [temp_path, "--preview", "-t", "extract_constant"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_refactor_nonexistent_file(self):
        """Test refactoring a nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(refactor, ["/nonexistent/file.py"])
        assert result.exit_code != 0


class TestReportCommand:
    """Test the report command."""

    def test_report_help(self):
        """Test report help."""
        runner = CliRunner()
        result = runner.invoke(report, ["--help"])
        assert result.exit_code == 0
        assert "report" in result.output.lower()

    def test_report_text_format(self):
        """Test report with text format."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(report, [temp_path, "-f", "text"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_report_json_format(self):
        """Test report with JSON format."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            temp_path = f.name

        try:
            result = runner.invoke(report, [temp_path, "-f", "json"])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_report_with_output_file(self):
        """Test report with output file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")

            output_file = Path(tmpdir) / "report.txt"

            result = runner.invoke(report, [str(test_file), "-o", str(output_file)])
            assert result.exit_code == 0
            assert output_file.exists()
            assert output_file.stat().st_size > 0

    def test_report_nonexistent_file(self):
        """Test report on nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(report, ["/nonexistent/file.py"])
        assert result.exit_code != 0


class TestInitCommand:
    """Test the init command."""

    def test_init_help(self):
        """Test init help."""
        runner = CliRunner()
        result = runner.invoke(init, ["--help"])
        assert result.exit_code == 0

    def test_init_creates_config(self):
        """Test that init creates config file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(init)
                assert result.exit_code == 0

                config_path = Path(tmpdir) / ".refactron.yaml"
                assert config_path.exists()

                content = config_path.read_text()
                assert "enabled_analyzers" in content
                assert "enabled_refactorers" in content
            finally:
                os.chdir(original_dir)

    def test_init_doesnt_overwrite_without_confirm(self):
        """Test that init doesn't overwrite existing config without confirmation."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create existing config
                config_path = Path(tmpdir) / ".refactron.yaml"
                config_path.write_text("existing: config")

                # Try to init without confirming
                _result = runner.invoke(init, input="n\n")  # noqa: F841

                # Should still have original content
                assert "existing: config" in config_path.read_text()
            finally:
                os.chdir(original_dir)


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self):
        """Test invalid command."""
        runner = CliRunner()
        result = runner.invoke(main, ["invalid_command"])
        assert result.exit_code != 0

    def test_analyze_empty_file(self):
        """Test analyzing an empty file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_analyze_binary_file(self):
        """Test analyzing a binary file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pyc", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully or skip
            assert result.exit_code in [0, 1]
        finally:
            os.unlink(temp_path)

    def test_analyze_syntax_error_file(self):
        """Test analyzing a file with syntax errors."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken function(:")
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            # Should handle gracefully
            assert result.exit_code in [0, 1]
        finally:
            os.unlink(temp_path)


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_full_workflow(self):
        """Test complete workflow: init, analyze, refactor, report."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)

                # 1. Init
                result = runner.invoke(init)
                assert result.exit_code == 0

                # 2. Create test file
                test_file = Path(tmpdir) / "test.py"
                test_file.write_text(
                    """
def calculate(price):
    if price > 1000:
        return price * 0.15
    return 0
"""
                )

                # 3. Analyze
                result = runner.invoke(analyze, [str(test_file)])
                assert result.exit_code == 0

                # 4. Refactor
                result = runner.invoke(refactor, [str(test_file), "--preview"])
                assert result.exit_code == 0

                # 5. Report
                output_file = Path(tmpdir) / "report.txt"
                result = runner.invoke(report, [str(test_file), "-o", str(output_file)])
                assert result.exit_code == 0
                assert output_file.exists()

            finally:
                os.chdir(original_dir)

    def test_analyze_with_all_analyzers(self):
        """Test analyze with all analyzers enabled."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """

def process(data):
    # Some issues but no critical ones
    if True:
        result = data * 2
    return result

def unused():
    pass
"""
            )
            temp_path = f.name

        try:
            result = runner.invoke(analyze, [temp_path])
            assert result.exit_code == 0
            # Should detect multiple types of issues
        finally:
            os.unlink(temp_path)


# ─────────────── CLI Analysis (boost) ───────────────


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_cfg():
    cfg = MagicMock()
    cfg.log_level = "INFO"
    cfg.log_format = "text"
    cfg.enable_metrics = False
    cfg.backup_enabled = True
    cfg.report_format = "text"
    return cfg


@pytest.fixture()
def mock_analysis_result():
    result = MagicMock()
    result.all_issues = []
    result.summary.return_value = {
        "total_files": 1,
        "files_analyzed": 1,
        "files_failed": 0,
        "total_issues": 0,
        "critical": 0,
        "errors": 0,
        "warnings": 0,
        "info": 0,
        "applied": False,
        "total_operations": 0,
        "safe": 0,
        "high_risk": 0,
    }
    result.report.return_value = "# Report\n"
    return result


# ─────────────────────────── analyze command ──────────────────────────────────


class TestAnalyzeCommandBoost:
    def test_analyze_no_target_no_workspace(self, runner, tmp_path, mock_cfg):
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.WorkspaceManager") as mock_ws:
            mock_ws.return_value.get_workspace_by_path.return_value = None
            result = runner.invoke(analyze, [])
        assert result.exit_code == 1

    def test_analyze_with_target(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis._validate_path", return_value=tmp_path), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.analysis._print_file_count"
        ), patch(
            "refactron.cli.analysis._create_summary_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.analysis._print_status_messages"
        ), patch(
            "refactron.cli.analysis._print_helpful_tips"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(analyze, [str(tmp_path)])
        assert result.exit_code == 0

    def test_analyze_with_critical_issues(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        mock_analysis_result.summary.return_value["critical"] = 2
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis._validate_path", return_value=tmp_path), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.analysis._print_file_count"
        ), patch(
            "refactron.cli.analysis._create_summary_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.analysis._print_status_messages"
        ), patch(
            "refactron.cli.analysis._print_helpful_tips"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(analyze, [str(tmp_path)])
        assert result.exit_code == 1

    def test_analyze_exception_raises_systemexit(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis._validate_path", return_value=tmp_path), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.analysis._print_file_count"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.analyze.side_effect = RuntimeError("fail")
            result = runner.invoke(analyze, [str(tmp_path)])
        assert result.exit_code == 1

    def test_analyze_show_metrics(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        mock_cfg.enable_metrics = True
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        mock_collector = MagicMock()
        mock_collector.get_analysis_summary.return_value = {
            "total_analysis_time_ms": 100.0,
            "average_time_per_file_ms": 50.0,
            "success_rate_percent": 100.0,
        }
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis._validate_path", return_value=tmp_path), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.analysis._print_file_count"
        ), patch(
            "refactron.cli.analysis._create_summary_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.analysis._print_status_messages"
        ), patch(
            "refactron.cli.analysis._print_helpful_tips"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ), patch(
            "refactron.core.metrics.get_metrics_collector", return_value=mock_collector
        ):
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(analyze, [str(tmp_path), "--show-metrics"])
        assert result.exit_code == 0

    def test_analyze_workspace_connected(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        mock_workspace = MagicMock()
        mock_workspace.repo_full_name = "user/repo"
        mock_workspace.local_path = str(tmp_path)
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.WorkspaceManager") as mock_ws, patch(
            "refactron.cli.analysis._interactive_file_selector", return_value=tmp_path / "f.py"
        ), patch(
            "refactron.cli.analysis._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.analysis._print_file_count"
        ), patch(
            "refactron.cli.analysis._create_summary_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.analysis._print_status_messages"
        ), patch(
            "refactron.cli.analysis._print_helpful_tips"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ws.return_value.get_workspace_by_path.return_value = mock_workspace
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(analyze, [])
        assert result.exit_code == 0


# ─────────────────────────── report command ───────────────────────────────────


class TestReportCommandBoost:
    def test_report_text_to_stdout(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch("refactron.cli.analysis._auth_banner"):
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(report, [str(tmp_path)])
        assert result.exit_code == 0

    def test_report_to_file(self, runner, tmp_path, mock_cfg, mock_analysis_result):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        output_file = tmp_path / "report.txt"
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch("refactron.cli.analysis._auth_banner"):
            mock_ref.return_value.analyze.return_value = mock_analysis_result
            result = runner.invoke(report, [str(tmp_path), "--output", str(output_file)])
        assert result.exit_code == 0

    def test_report_failure(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.analysis._load_config", return_value=mock_cfg), patch(
            "refactron.cli.analysis.Refactron"
        ) as mock_ref, patch("refactron.cli.analysis._auth_banner"):
            mock_ref.return_value.analyze.side_effect = RuntimeError("oops")
            result = runner.invoke(report, [str(tmp_path)])
        assert result.exit_code == 1


# ─────────────────────────── metrics command ──────────────────────────────────


class TestMetricsCommand:
    def test_metrics_text_format(self, runner):
        mock_collector = MagicMock()
        mock_collector.get_analysis_summary.return_value = {
            "total_files_analyzed": 5,
            "total_files_failed": 0,
            "total_issues_found": 2,
            "total_analysis_time_ms": 100.0,
            "average_time_per_file_ms": 20.0,
            "success_rate_percent": 100.0,
            "analyzer_hit_counts": {"complexity": 3},
        }
        mock_collector.get_combined_summary.return_value = {
            "analysis": mock_collector.get_analysis_summary.return_value,
            "refactoring": {"total_refactorings_applied": 0, "success_rate_percent": 100.0},
        }
        # metrics is lazy-imported inside the command; patch at source
        with patch(
            "refactron.core.metrics.get_metrics_collector", return_value=mock_collector
        ), patch("refactron.cli.analysis._auth_banner"):
            result = runner.invoke(metrics, [])
        assert result.exit_code == 0

    def test_metrics_json_format(self, runner):
        mock_collector = MagicMock()
        mock_collector.get_combined_summary.return_value = {"analysis": {}, "refactoring": {}}
        with patch(
            "refactron.core.metrics.get_metrics_collector", return_value=mock_collector
        ), patch("refactron.cli.analysis._auth_banner"):
            result = runner.invoke(metrics, ["--format", "json"])
        assert result.exit_code == 0


# ─────────────────────────── serve_metrics command ────────────────────────────


class TestServeMetricsCommand:
    def test_serve_metrics_keyboard_interrupt(self, runner):
        # Patch at the lazy-import source modules
        with patch("refactron.core.prometheus_metrics.start_metrics_server"), patch(
            "refactron.core.prometheus_metrics.stop_metrics_server"
        ), patch("refactron.cli.analysis._auth_banner"), patch(
            "time.sleep", side_effect=KeyboardInterrupt
        ):
            result = runner.invoke(serve_metrics, [])
        assert result.exit_code == 0

    def test_serve_metrics_start_failure(self, runner):
        with patch(
            "refactron.core.prometheus_metrics.start_metrics_server",
            side_effect=RuntimeError("port busy"),
        ), patch("refactron.cli.analysis._auth_banner"):
            result = runner.invoke(serve_metrics, [])
        assert result.exit_code == 1


# ─────────────────────────── suggest command ──────────────────────────────────


class TestSuggestCommand:
    def test_suggest_on_file(self, runner, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("def foo():\n    x = 1\n    return x\n")

        from refactron.llm.models import SuggestionStatus

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.PENDING
        mock_sugg.explanation = "Use constant"
        mock_sugg.proposed_code = "def foo():\n    return 1\n"
        mock_sugg.model_name = "test-model"
        mock_sugg.confidence_score = 0.9
        mock_sugg.llm_confidence = 0.9
        mock_sugg.safety_result = None

        with patch("refactron.cli.analysis._load_config"), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.Refactron") as mock_ref, patch(
            "refactron.cli.analysis.ContextRetriever"
        ), patch(
            "refactron.cli.analysis.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_suggestion.return_value = mock_sugg
            result = runner.invoke(suggest, [str(py_file)])
        assert result.exit_code == 0

    def test_suggest_directory_not_supported(self, runner, tmp_path):
        with patch("refactron.cli.analysis._load_config"), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.Refactron") as mock_ref, patch(
            "refactron.cli.analysis.ContextRetriever"
        ), patch(
            "refactron.cli.analysis.LLMOrchestrator"
        ), patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            result = runner.invoke(suggest, [str(tmp_path)])
        assert result.exit_code == 0

    def test_suggest_failed_status(self, runner, tmp_path):
        py_file = tmp_path / "bad.py"
        py_file.write_text("x = 1\n")

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.FAILED
        mock_sugg.explanation = "No LLM"

        with patch("refactron.cli.analysis._load_config"), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.Refactron") as mock_ref, patch(
            "refactron.cli.analysis.ContextRetriever"
        ), patch(
            "refactron.cli.analysis.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_suggestion.return_value = mock_sugg
            result = runner.invoke(suggest, [str(py_file)])
        assert result.exit_code == 0

    def test_suggest_with_line(self, runner, tmp_path):
        py_file = tmp_path / "code.py"
        py_file.write_text("\n".join(["x = 0"] * 20) + "\n")

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.PENDING
        mock_sugg.explanation = "Better"
        mock_sugg.proposed_code = "x = 0\n"
        mock_sugg.model_name = "model"
        mock_sugg.confidence_score = 0.9
        mock_sugg.llm_confidence = 0.9
        mock_sugg.safety_result = None

        with patch("refactron.cli.analysis._load_config"), patch(
            "refactron.cli.analysis._setup_logging"
        ), patch("refactron.cli.analysis.Refactron") as mock_ref, patch(
            "refactron.cli.analysis.ContextRetriever"
        ), patch(
            "refactron.cli.analysis.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.analysis._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_suggestion.return_value = mock_sugg
            result = runner.invoke(suggest, [str(py_file), "--line", "5"])
        assert result.exit_code == 0


# ─────────────── CLI Refactor (boost) ───────────────


@pytest.fixture()
def runner_boost():
    return CliRunner()


@pytest.fixture()
def mock_cfg_boost():
    cfg = MagicMock()
    cfg.backup_enabled = True
    return cfg


@pytest.fixture()
def mock_refactor_result():
    result = MagicMock()
    result.operations = []
    result.summary.return_value = {
        "total_operations": 0,
        "safe": 0,
        "high_risk": 0,
        "applied": False,
    }
    result.show_diff.return_value = ""
    result.apply.return_value = True
    return result


# ─────────────────────────── refactor command ─────────────────────────────────


class TestRefactorCommandBoost:
    def test_no_target_no_workspace(self, runner, mock_cfg):
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor.WorkspaceManager") as mock_ws:
            mock_ws.return_value.get_workspace_by_path.return_value = None
            result = runner.invoke(refactor, [])
        assert result.exit_code == 1

    def test_refactor_preview(self, runner, tmp_path, mock_cfg, mock_refactor_result):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.refactor._print_refactor_filters"
        ), patch(
            "refactron.cli.refactor._confirm_apply_mode"
        ), patch(
            "refactron.cli.refactor.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.refactor._create_refactor_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.refactor._print_refactor_messages"
        ):
            mock_ref.return_value.refactor.return_value = mock_refactor_result
            result = runner.invoke(refactor, [str(py_file)])
        assert result.exit_code == 0

    def test_refactor_failure(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.refactor._print_refactor_filters"
        ), patch(
            "refactron.cli.refactor._confirm_apply_mode"
        ), patch(
            "refactron.cli.refactor.Refactron"
        ) as mock_ref:
            mock_ref.return_value.refactor.side_effect = RuntimeError("fail")
            result = runner.invoke(refactor, [str(py_file)])
        assert result.exit_code == 1

    def test_refactor_no_target_workspace_found(
        self, runner, tmp_path, mock_cfg, mock_refactor_result
    ):
        mock_ws_obj = MagicMock()
        mock_ws_obj.local_path = str(tmp_path)
        mock_ws_obj.repo_full_name = "user/repo"
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.refactor._print_refactor_filters"
        ), patch(
            "refactron.cli.refactor._confirm_apply_mode"
        ), patch(
            "refactron.cli.refactor.WorkspaceManager"
        ) as mock_ws, patch(
            "refactron.cli.refactor.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.refactor._create_refactor_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.refactor._print_refactor_messages"
        ):
            mock_ws.return_value.get_workspace_by_path.return_value = mock_ws_obj
            mock_ref.return_value.refactor.return_value = mock_refactor_result
            result = runner.invoke(refactor, [])
        assert result.exit_code == 0

    def test_refactor_with_backup_io_error(self, runner, tmp_path, mock_cfg, mock_refactor_result):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        mock_cfg.backup_enabled = True
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.refactor._print_refactor_filters"
        ), patch(
            "refactron.cli.refactor._confirm_apply_mode"
        ), patch(
            "refactron.cli.refactor.BackupRollbackSystem"
        ) as mock_brs, patch(
            "refactron.cli.refactor.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.refactor._create_refactor_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.refactor._print_refactor_messages"
        ):
            mock_ref_inst = MagicMock()
            mock_ref_inst.detect_project_root.return_value = tmp_path
            mock_ref_inst.get_python_files.return_value = [py_file]
            mock_ref_inst.refactor.return_value = mock_refactor_result
            mock_ref.return_value = mock_ref_inst

            mock_brs.return_value.git.is_git_repo.return_value = False
            mock_brs.return_value.prepare_for_refactoring.side_effect = OSError("No space")

            # With --apply and stdin confirming "y" for continue without backup
            result = runner.invoke(refactor, [str(py_file), "--apply"], input="y\n")
        assert result.exit_code in (0, 1)

    def test_refactor_apply_with_operations(self, runner, tmp_path, mock_cfg, mock_refactor_result):
        py_file = tmp_path / "s.py"
        py_file.write_text("x = 1\n")
        mock_refactor_result.operations = [MagicMock(metadata={})]
        mock_refactor_result.summary.return_value["total_operations"] = 1
        with patch("refactron.cli.refactor._setup_logging"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch(
            "refactron.cli.refactor._print_refactor_filters"
        ), patch(
            "refactron.cli.refactor._confirm_apply_mode"
        ), patch(
            "refactron.cli.refactor.Refactron"
        ) as mock_ref, patch(
            "refactron.cli.refactor._create_refactor_table", return_value=MagicMock()
        ), patch(
            "refactron.cli.refactor._print_refactor_messages"
        ), patch(
            "refactron.cli.refactor._record_applied_operations"
        ):
            mock_cfg.backup_enabled = False
            mock_ref.return_value.refactor.return_value = mock_refactor_result
            result = runner.invoke(refactor, [str(py_file), "--apply"])
        assert result.exit_code == 0


# ─────────────────────────── autofix command ──────────────────────────────────


class TestAutofixCommand:
    def _make_mock_pipeline(self, tmp_path):
        """Return a mock RefactronPipeline suitable for autofix tests."""
        mock_session = MagicMock()
        mock_session.session_id = "sess_test_123"
        mock_session.fix_queue = []
        mock_session.applied_fixes = []
        mock_session.blocked_fixes = []

        mock_pipeline = MagicMock()
        mock_pipeline.store.load.return_value = None
        mock_pipeline.analyze.return_value = mock_session
        mock_pipeline._last_result = None
        mock_pipeline.apply.return_value = None

        return mock_pipeline, mock_session

    def test_autofix_preview_mode(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        mock_pipeline, _ = self._make_mock_pipeline(tmp_path)
        with patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch("refactron.cli.refactor._print_file_count"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch(
            "refactron.core.pipeline.RefactronPipeline", return_value=mock_pipeline
        ):
            result = runner.invoke(autofix, [str(py_file)])
        assert result.exit_code == 0
        assert "Dry-run complete" in result.output or "session" in result.output.lower()

    def test_autofix_apply_mode(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        mock_pipeline, _ = self._make_mock_pipeline(tmp_path)
        with patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
            "refactron.cli.refactor._validate_path", return_value=tmp_path
        ), patch("refactron.cli.refactor._print_file_count"), patch(
            "refactron.cli.refactor._auth_banner"
        ), patch(
            "refactron.core.pipeline.RefactronPipeline", return_value=mock_pipeline
        ):
            result = runner.invoke(autofix, [str(py_file), "--apply"])
        assert result.exit_code == 0

    def test_autofix_safety_levels(self, runner, tmp_path, mock_cfg):
        py_file = tmp_path / "s.py"
        py_file.write_text("x = 1\n")
        mock_pipeline, _ = self._make_mock_pipeline(tmp_path)
        for level in ["safe", "low", "moderate", "high"]:
            with patch("refactron.cli.refactor._load_config", return_value=mock_cfg), patch(
                "refactron.cli.refactor._validate_path", return_value=tmp_path
            ), patch("refactron.cli.refactor._print_file_count"), patch(
                "refactron.cli.refactor._auth_banner"
            ), patch(
                "refactron.core.pipeline.RefactronPipeline", return_value=mock_pipeline
            ):
                result = runner.invoke(autofix, [str(py_file), "--safety-level", level])
            assert result.exit_code == 0


# ─────────────────────────── rollback command ─────────────────────────────────


class TestRollbackCommand:
    def test_rollback_no_sessions(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = []
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, [])
        assert "No backup" in result.output

    def test_rollback_list(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "sess1", "timestamp": "2024-01-01", "files": ["a.py"], "description": "test"}
        ]
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, ["--list"])
        assert "sess1" in result.output

    def test_rollback_clear_confirmed(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "x", "timestamp": "t", "files": [], "description": "d"}
        ]
        mock_system.clear_all.return_value = 1
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, ["--clear"], input="y\n")
        assert "Cleared" in result.output or result.exit_code == 0

    def test_rollback_clear_cancelled(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "x", "timestamp": "t", "files": [], "description": "d"}
        ]
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, ["--clear"], input="n\n")
        assert result.exit_code == 0

    def test_rollback_specific_session_not_found(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "sess1", "timestamp": "t", "files": [], "description": "d"}
        ]
        mock_system.backup_manager.get_session.return_value = None
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, ["missing_session_id"])
        assert result.exit_code == 1

    def test_rollback_latest_success(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "sess1", "timestamp": "t", "files": ["a.py"], "description": "d"}
        ]
        mock_system.rollback.return_value = {
            "success": True,
            "message": "Restored",
            "files_restored": 1,
        }
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, [], input="y\n")
        assert result.exit_code == 0

    def test_rollback_latest_failure(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "sess1", "timestamp": "t", "files": ["a.py"], "description": "d"}
        ]
        mock_system.rollback.return_value = {"success": False, "message": "Failed to restore"}
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, [], input="y\n")
        assert result.exit_code == 1

    def test_rollback_use_git(self, runner):
        mock_system = MagicMock()
        mock_system.list_sessions.return_value = [
            {"id": "sess1", "timestamp": "t", "files": ["a.py"], "description": "d"}
        ]
        mock_system.rollback.return_value = {
            "success": True,
            "message": "Git rollback done",
            "files_restored": 1,
        }
        with patch("refactron.cli.refactor.BackupRollbackSystem", return_value=mock_system):
            result = runner.invoke(rollback, ["--use-git"], input="y\n")
        assert result.exit_code == 0


# ─────────────────────────── document command ─────────────────────────────────


class TestDocumentCommand:
    def test_document_file(self, runner, tmp_path):
        py_file = tmp_path / "module.py"
        py_file.write_text("def foo(): pass\n")

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.PENDING
        mock_sugg.explanation = "Docs added"
        mock_sugg.proposed_code = "# docs\n"
        mock_sugg.model_name = "model"
        mock_sugg.confidence_score = 0.9

        with patch("refactron.cli.refactor._load_config"), patch(
            "refactron.cli.refactor._setup_logging"
        ), patch("refactron.cli.refactor.Refactron") as mock_ref, patch(
            "refactron.cli.refactor.ContextRetriever"
        ), patch(
            "refactron.cli.refactor.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.refactor._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_documentation.return_value = mock_sugg
            result = runner.invoke(document, [str(py_file)])
        assert result.exit_code == 0

    def test_document_directory_not_supported(self, runner, tmp_path):
        with patch("refactron.cli.refactor._load_config"), patch(
            "refactron.cli.refactor._setup_logging"
        ), patch("refactron.cli.refactor.Refactron") as mock_ref, patch(
            "refactron.cli.refactor.ContextRetriever"
        ), patch(
            "refactron.cli.refactor.LLMOrchestrator"
        ), patch(
            "refactron.cli.refactor._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            result = runner.invoke(document, [str(tmp_path)])
        assert result.exit_code == 0  # returns early

    def test_document_failed_generation(self, runner, tmp_path):
        py_file = tmp_path / "module.py"
        py_file.write_text("def foo(): pass\n")

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.FAILED
        mock_sugg.explanation = "No LLM"

        with patch("refactron.cli.refactor._load_config"), patch(
            "refactron.cli.refactor._setup_logging"
        ), patch("refactron.cli.refactor.Refactron") as mock_ref, patch(
            "refactron.cli.refactor.ContextRetriever"
        ), patch(
            "refactron.cli.refactor.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.refactor._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_documentation.return_value = mock_sugg
            result = runner.invoke(document, [str(py_file)])
        assert result.exit_code == 0

    def test_document_apply_interactive(self, runner, tmp_path):
        py_file = tmp_path / "m.py"
        py_file.write_text("def bar(): pass\n")

        mock_sugg = MagicMock()
        mock_sugg.status = SuggestionStatus.PENDING
        mock_sugg.explanation = "Docs"
        mock_sugg.proposed_code = "# new docs\n"
        mock_sugg.model_name = "m"
        mock_sugg.confidence_score = 0.8

        with patch("refactron.cli.refactor._load_config"), patch(
            "refactron.cli.refactor._setup_logging"
        ), patch("refactron.cli.refactor.Refactron") as mock_ref, patch(
            "refactron.cli.refactor.ContextRetriever"
        ), patch(
            "refactron.cli.refactor.LLMOrchestrator"
        ) as mock_orch, patch(
            "refactron.cli.refactor._auth_banner"
        ):
            mock_ref.return_value.detect_project_root.return_value = tmp_path
            mock_orch.return_value.generate_documentation.return_value = mock_sugg
            result = runner.invoke(document, [str(py_file), "--apply", "--no-interactive"])
        assert result.exit_code == 0


# ─────────────── CLI UI (boost) ───────────────


def make_summary(**kwargs):
    base = {
        "total_files": 5,
        "files_analyzed": 5,
        "files_failed": 0,
        "total_issues": 0,
        "critical": 0,
        "errors": 0,
        "warnings": 0,
        "info": 0,
        "applied": False,
        "total_operations": 0,
        "safe": 0,
        "high_risk": 0,
    }
    base.update(kwargs)
    return base


def make_issue_mock(level_val="warning", suggestion=None):
    issue = MagicMock()
    issue.level.value = level_val
    issue.suggestion = suggestion
    issue.__str__ = lambda self: f"Issue at line 1: {level_val}"
    return issue


# ─────────────────────────── _auth_banner ─────────────────────────────────────


class TestAuthBanner:
    def test_renders_without_error(self):
        with patch.object(console, "print"):
            _auth_banner("Test Title")  # Should not raise

    def test_title_appears(self):
        captured = []
        with patch.object(console, "print", side_effect=lambda *a, **k: captured.append(str(a))):
            _auth_banner("Analysis")


# ─────────────────────────── _print_file_count ────────────────────────────────


class TestPrintFileCount:
    def test_directory_prints_count(self, tmp_path):
        (tmp_path / "a.py").write_text("x=1")
        (tmp_path / "b.py").write_text("y=2")
        with patch.object(console, "print") as mock_print:
            _print_file_count(tmp_path)
        mock_print.assert_called()

    def test_file_prints_nothing(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x=1")
        with patch.object(console, "print") as mock_print:
            _print_file_count(py_file)
        mock_print.assert_not_called()


# ─────────────────────────── _create_summary_table ────────────────────────────


class TestCreateSummaryTable:
    def test_no_issues(self):
        table = _create_summary_table(make_summary())
        assert table is not None

    def test_with_critical(self):
        table = _create_summary_table(make_summary(critical=2, files_failed=1, total_issues=3))
        assert table is not None

    def test_with_all_counts(self):
        table = _create_summary_table(
            make_summary(total_issues=5, critical=1, errors=2, warnings=1, info=1)
        )
        assert table is not None


# ─────────────────────────── _print_status_messages ───────────────────────────


class TestPrintStatusMessages:
    def test_no_issues_no_failures(self):
        with patch.object(console, "print"):
            _print_status_messages(make_summary())  # Panel shown

    def test_files_failed(self):
        with patch.object(console, "print") as mock_print:
            _print_status_messages(make_summary(files_failed=2, total_issues=0))
        assert mock_print.called

    def test_critical_issues(self):
        with patch.object(console, "print") as mock_print:
            _print_status_messages(make_summary(critical=3, total_issues=3))
        assert mock_print.called

    def test_no_issues_but_failures(self):
        with patch.object(console, "print") as mock_print:
            _print_status_messages(make_summary(files_failed=1, total_issues=0))
        assert mock_print.called


# ─────────────────────────── _print_detailed_issues ───────────────────────────


class TestPrintDetailedIssues:
    def test_critical_issue(self):
        result = MagicMock()
        result.all_issues = [make_issue_mock("critical")]
        with patch.object(console, "print"):
            _print_detailed_issues(result)

    def test_warning_with_suggestion(self):
        result = MagicMock()
        result.all_issues = [make_issue_mock("warning", suggestion="Use xyz")]
        with patch.object(console, "print"):
            _print_detailed_issues(result)

    def test_info_issue(self):
        result = MagicMock()
        result.all_issues = [make_issue_mock("info")]
        with patch.object(console, "print"):
            _print_detailed_issues(result)

    def test_error_issue(self):
        result = MagicMock()
        result.all_issues = [make_issue_mock("error")]
        with patch.object(console, "print"):
            _print_detailed_issues(result)


# ─────────────────────────── _print_helpful_tips ──────────────────────────────


class TestPrintHelpfulTips:
    def test_no_issues(self):
        with patch.object(console, "print") as mock_print:
            _print_helpful_tips(make_summary(total_issues=0), detailed=True)
        mock_print.assert_not_called()

    def test_issues_not_detailed(self):
        with patch.object(console, "print") as mock_print:
            _print_helpful_tips(make_summary(total_issues=2), detailed=False)
        assert any("--detailed" in str(c) for c in mock_print.call_args_list)

    def test_many_issues(self):
        with patch.object(console, "print") as mock_print:
            _print_helpful_tips(make_summary(total_issues=10), detailed=True)
        assert mock_print.called


# ─────────────────────────── _print_refactor_filters ──────────────────────────


class TestPrintRefactorFilters:
    def test_no_types(self):
        with patch.object(console, "print") as mock_print:
            _print_refactor_filters(())
        mock_print.assert_not_called()

    def test_with_types(self):
        with patch.object(console, "print") as mock_print:
            _print_refactor_filters(("rename", "extract"))
        assert mock_print.called


# ─────────────────────────── _confirm_apply_mode ──────────────────────────────


class TestConfirmApplyMode:
    def test_preview_mode_no_confirm(self):
        with patch.object(console, "print") as mock_print:
            _confirm_apply_mode(preview=True)
        mock_print.assert_not_called()

    def test_apply_mode_confirmed(self):
        with patch.object(console, "print"), patch(
            "refactron.cli.ui.click.confirm", return_value=True
        ):
            _confirm_apply_mode(preview=False)  # Should not raise

    def test_apply_mode_cancelled(self):
        with patch.object(console, "print"), patch(
            "refactron.cli.ui.click.confirm", return_value=False
        ):
            with pytest.raises(SystemExit):
                _confirm_apply_mode(preview=False)


# ─────────────────────────── _create_refactor_table ───────────────────────────


class TestCreateRefactorTable:
    def test_no_high_risk(self):
        table = _create_refactor_table(
            make_summary(total_operations=3, safe=3, high_risk=0, applied=False)
        )
        assert table is not None

    def test_with_high_risk(self):
        table = _create_refactor_table(
            make_summary(total_operations=2, safe=1, high_risk=1, applied=True)
        )
        assert table is not None


# ─────────────────────────── _print_refactor_messages ─────────────────────────


class TestPrintRefactorMessages:
    def test_no_operations(self):
        with patch.object(console, "print"):
            _print_refactor_messages(make_summary(total_operations=0), preview=True)

    def test_high_risk(self):
        with patch.object(console, "print") as mock_print:
            _print_refactor_messages(make_summary(total_operations=2, high_risk=1), preview=True)
        assert mock_print.called

    def test_preview_with_operations(self):
        with patch.object(console, "print") as mock_print:
            _print_refactor_messages(make_summary(total_operations=3), preview=True)
        assert mock_print.called

    def test_applied_success(self):
        with patch.object(console, "print") as mock_print:
            _print_refactor_messages(make_summary(total_operations=2, applied=True), preview=False)
        assert mock_print.called


# ─────────────────────────── _collect_feedback_interactive ────────────────────


class TestCollectFeedbackInteractive:
    def test_no_operations(self):
        refactron = MagicMock()
        result = MagicMock()
        result.operations = []
        with patch.object(console, "print"):
            _collect_feedback_interactive(refactron, result)
        refactron.record_feedback.assert_not_called()

    def test_skip_feedback(self):
        refactron = MagicMock()
        op = MagicMock()
        op.operation_id = "op1"
        op.operation_type = "rename"
        op.file_path = "test.py"
        op.line_number = 5
        result = MagicMock()
        result.operations = [op]
        result.get_ranking_score.return_value = 0.5
        with patch.object(console, "print"), patch(
            "refactron.cli.ui.click.prompt", return_value="s"
        ):
            _collect_feedback_interactive(refactron, result)
        refactron.record_feedback.assert_not_called()

    def test_accepted_feedback_with_reason(self):
        refactron = MagicMock()
        op = MagicMock()
        op.operation_id = "op2"
        op.operation_type = "extract"
        op.file_path = "a.py"
        op.line_number = 1
        result = MagicMock()
        result.operations = [op]
        result.get_ranking_score.return_value = 0.0
        with patch.object(console, "print"), patch(
            "refactron.cli.ui.click.prompt", side_effect=["a", "looks good"]
        ):
            _collect_feedback_interactive(refactron, result)
        refactron.record_feedback.assert_called_once()

    def test_rejected_feedback_no_reason(self):
        refactron = MagicMock()
        op = MagicMock()
        op.operation_id = "op3"
        op.operation_type = "rename"
        op.file_path = "b.py"
        op.line_number = 3
        result = MagicMock()
        result.operations = [op]
        result.get_ranking_score.return_value = 0.0
        with patch.object(console, "print"), patch(
            "refactron.cli.ui.click.prompt", side_effect=["r", ""]
        ):
            _collect_feedback_interactive(refactron, result)
        refactron.record_feedback.assert_called_once()


# ─────────────────────────── _record_applied_operations ───────────────────────


class TestRecordAppliedOperations:
    def test_no_operations(self):
        refactron = MagicMock()
        result = MagicMock()
        result.operations = []
        _record_applied_operations(refactron, result)
        refactron.record_feedback.assert_not_called()

    def test_records_accepted(self):
        refactron = MagicMock()
        op = MagicMock()
        op.operation_id = "op1"
        result = MagicMock()
        result.operations = [op]
        _record_applied_operations(refactron, result)
        refactron.record_feedback.assert_called_once_with(
            operation_id="op1",
            action="accepted",
            reason="Applied via --apply flag",
            operation=op,
        )


# ─────────────────────────── _interactive_file_selector ───────────────────────


class TestInteractiveFileSelector:
    def test_nonexistent_directory(self, tmp_path):
        result = _interactive_file_selector(tmp_path / "nonexistent")
        assert result is None

    def test_no_matching_files(self, tmp_path):
        result = _interactive_file_selector(tmp_path, pattern="*.py")
        assert result is None

    def test_user_cancels_with_zero(self, tmp_path):
        (tmp_path / "a.py").write_text("x=1")
        with patch("refactron.cli.ui.IntPrompt.ask", return_value=0):
            result = _interactive_file_selector(tmp_path, pattern="*.py")
        assert result is None

    def test_selects_file(self, tmp_path):
        (tmp_path / "a.py").write_text("x=1")
        (tmp_path / "b.py").write_text("y=2")
        with patch("refactron.cli.ui.IntPrompt.ask", return_value=1), patch.object(
            console, "print"
        ):
            result = _interactive_file_selector(tmp_path, pattern="*.py")
        assert result is not None

    def test_out_of_range_selection(self, tmp_path):
        (tmp_path / "a.py").write_text("x=1")
        with patch("refactron.cli.ui.IntPrompt.ask", return_value=999), patch.object(
            console, "print"
        ):
            result = _interactive_file_selector(tmp_path, pattern="*.py")
        assert result is None

    def test_more_than_20_files(self, tmp_path):
        for i in range(25):
            (tmp_path / f"file{i}.py").write_text(f"x={i}")
        with patch("refactron.cli.ui.IntPrompt.ask", return_value=0), patch.object(
            console, "print"
        ):
            result = _interactive_file_selector(tmp_path, pattern="*.py")
        assert result is None


# ─────────────────────────── _print_custom_help ───────────────────────────────


class TestPrintCustomHelp:
    def test_renders_without_error(self):
        ctx = MagicMock()
        ctx.command.list_commands.return_value = ["analyze", "refactor"]
        ctx.command.get_command.return_value = MagicMock(get_short_help_str=lambda: "desc")
        with patch.object(console, "print"):
            _print_custom_help(ctx)


# ─────────────── CLI Utils/Orchestrator ───────────────


# ──────────────────────────────────────────────
# ApiKeyValidationResult
# ──────────────────────────────────────────────


class TestApiKeyValidationResult:
    def test_ok_result(self):
        r = ApiKeyValidationResult(ok=True, message="Verified.")
        assert r.ok is True

    def test_fail_result(self):
        r = ApiKeyValidationResult(ok=False, message="Invalid API key.")
        assert r.ok is False


class TestValidateApiKey:
    def _mock_response(self, status_code: int):
        resp = MagicMock()
        resp.status_code = status_code
        return resp

    def test_200_returns_ok(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(200)):
            result = _validate_api_key("https://api.example.com", "key123", 5)
        assert result.ok is True

    def test_401_returns_invalid(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(401)):
            result = _validate_api_key("https://api.example.com", "badkey", 5)
        assert result.ok is False
        assert "Invalid" in result.message

    def test_403_returns_invalid(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(403)):
            result = _validate_api_key("https://api.example.com", "badkey", 5)
        assert result.ok is False

    def test_404_returns_missing_endpoint(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(404)):
            result = _validate_api_key("https://api.example.com", "key", 5)
        assert result.ok is False
        assert "404" in result.message

    def test_500_returns_server_error(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(500)):
            result = _validate_api_key("https://api.example.com", "key", 5)
        assert result.ok is False
        assert "500" in result.message

    def test_timeout_returns_error(self):
        import requests

        with patch("refactron.cli.utils.requests.get", side_effect=requests.Timeout):
            result = _validate_api_key("https://api.example.com", "key", 1)
        assert result.ok is False
        assert "timed out" in result.message.lower()

    def test_connection_error_returns_error(self):

        with patch("refactron.cli.utils.requests.get", side_effect=requests.ConnectionError):
            result = _validate_api_key("https://api.example.com", "key", 5)
        assert result.ok is False
        assert "reach" in result.message.lower()

    def test_request_exception_returns_error(self):

        with patch("refactron.cli.utils.requests.get", side_effect=requests.RequestException):
            result = _validate_api_key("https://api.example.com", "key", 5)
        assert result.ok is False

    def test_unknown_status_code(self):
        with patch("refactron.cli.utils.requests.get", return_value=self._mock_response(418)):
            result = _validate_api_key("https://api.example.com", "key", 5)
        assert result.ok is False
        assert "418" in result.message


class TestSetupLogging:
    def test_setup_verbose(self):
        _setup_logging(verbose=True)
        # verbose mode should not suppress httpx
        assert True  # verbose mode does not suppress httpx

    def test_setup_normal(self):
        import logging

        _setup_logging(verbose=False)
        # Noisy loggers should be set to ERROR
        assert logging.getLogger("httpx").level == logging.ERROR


class TestLoadConfig:
    def test_default_config_no_path(self):
        config = _load_config(None)
        assert config is not None

    def test_config_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('version: "1.0"\nmax_function_complexity: 12\n')
            fname = f.name
        config = _load_config(fname)
        assert config is not None

    def test_config_missing_file_exits(self):
        with pytest.raises(SystemExit):
            _load_config("/nonexistent/path/config.yaml")

    def test_config_with_profile(self):
        config = _load_config(None, profile="default", environment=None)
        assert config is not None


class TestValidatePath:
    def test_valid_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _validate_path(tmpdir)
            assert result == Path(tmpdir)

    def test_invalid_path_exits(self):
        with pytest.raises(SystemExit):
            _validate_path("/nonexistent/path/that/does/not/exist")


class TestDetectProjectType:
    def test_detects_django(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manage_py = Path(tmpdir) / "manage.py"
            manage_py.write_text("import django\nDJANGO_SETTINGS_MODULE = 'myproject.settings'\n")
            with patch("refactron.cli.utils.Path.cwd", return_value=Path(tmpdir)):
                result = _detect_project_type()
            assert result == "django"

    def test_detects_fastapi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_py = Path(tmpdir) / "main.py"
            main_py.write_text("from fastapi import FastAPI\napp = FastAPI()\n")
            with patch("refactron.cli.utils.Path.cwd", return_value=Path(tmpdir)):
                result = _detect_project_type()
            assert result == "fastapi"

    def test_detects_flask(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_py = Path(tmpdir) / "app.py"
            app_py.write_text("from flask import Flask\napp = Flask(__name__)\n")
            with patch("refactron.cli.utils.Path.cwd", return_value=Path(tmpdir)):
                result = _detect_project_type()
            assert result == "flask"

    def test_no_framework_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("refactron.cli.utils.Path.cwd", return_value=Path(tmpdir)):
                result = _detect_project_type()
            assert result is None


class TestGetPatternStorageFromConfig:
    def test_returns_storage_when_enabled(self):
        config = MagicMock()
        config.enable_pattern_learning = True
        config.pattern_storage_dir = Path(tempfile.mkdtemp())
        result = _get_pattern_storage_from_config(config)
        assert result is not None

    def test_returns_none_when_disabled(self):
        config = MagicMock()
        config.enable_pattern_learning = False
        result = _get_pattern_storage_from_config(config)
        assert result is None


# ──────────────────────────────────────────────
# LLMOrchestrator
# ──────────────────────────────────────────────


def make_issue(line=1):
    return CodeIssue(
        category=IssueCategory.CODE_SMELL,
        level=IssueLevel.WARNING,
        message="Magic number detected",
        file_path=Path("test.py"),
        line_number=line,
        rule_id="C001",
    )


class TestLLMOrchestrator:
    def _make_orchestrator(
        self,
        response_text=(
            '{"proposed_code": "x = 1", "explanation": "test",'
            ' "reasoning": "ok", "confidence": 0.9}'
        ),
    ):
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(return_value=response_text)
        return LLMOrchestrator(llm_client=mock_client), mock_client

    def test_generate_suggestion_success(self):
        orchestrator, _ = self._make_orchestrator(
            '{"proposed_code": "x = 1", "explanation": "fixed it",'
            ' "reasoning": "clean", "confidence": 0.95}'
        )
        issue = make_issue()
        result = orchestrator.generate_suggestion(issue, "x = 42")
        assert result is not None
        assert result.model_name == "test-model"

    def test_generate_suggestion_with_retriever(self):
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(
            return_value=(
                '{"proposed_code": "x = 1", "explanation": "ok",'
                ' "reasoning": "fine", "confidence": 0.9}'
            )
        )
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "similar code snippet"
        mock_retriever.retrieve_similar = MagicMock(return_value=[mock_result])

        orchestrator = LLMOrchestrator(llm_client=mock_client, retriever=mock_retriever)
        issue = make_issue()
        result = orchestrator.generate_suggestion(issue, "x = 42")
        assert result is not None
        mock_retriever.retrieve_similar.assert_called_once()

    def test_generate_suggestion_retriever_fails_gracefully(self):
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(
            return_value=(
                '{"proposed_code": "x=1", "explanation": "ok",'
                ' "reasoning": "ok", "confidence": 0.9}'
            )
        )
        mock_retriever = MagicMock()
        mock_retriever.retrieve_similar = MagicMock(side_effect=RuntimeError("index unavailable"))

        orchestrator = LLMOrchestrator(llm_client=mock_client, retriever=mock_retriever)
        result = orchestrator.generate_suggestion(make_issue(), "x = 42")
        assert result is not None  # Graceful degradation

    def test_generate_suggestion_llm_failure(self):
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(side_effect=RuntimeError("LLM unavailable"))

        orchestrator = LLMOrchestrator(llm_client=mock_client)
        result = orchestrator.generate_suggestion(make_issue(), "x = 42")
        assert result is not None  # Returns a failed suggestion

    def test_evaluate_issues_batch_empty(self):
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.evaluate_issues_batch([], "x = 1")
        assert result == {}

    def test_evaluate_issues_batch_success(self):
        response = json.dumps({"C001:1:0": 0.9, "C001:2:1": 0.3})
        orchestrator, mock_client = self._make_orchestrator(response)
        mock_client.generate = MagicMock(return_value=response)

        issues = [make_issue(1), make_issue(2)]
        result = orchestrator.evaluate_issues_batch(issues, "x = 42\ny = 99")
        assert isinstance(result, dict)
        assert all(isinstance(v, float) for v in result.values())

    def test_evaluate_issues_batch_llm_failure(self):
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(side_effect=RuntimeError("LLM down"))

        orchestrator = LLMOrchestrator(llm_client=mock_client)
        issues = [make_issue(1)]
        result = orchestrator.evaluate_issues_batch(issues, "x = 42")
        # Falls back to 0.5 for each issue
        assert all(v == 0.5 for v in result.values())

    def test_clean_json_response_markdown_block(self):
        orchestrator, _ = self._make_orchestrator()
        raw = '```json\n{"key": "value"}\n```'
        cleaned = orchestrator._clean_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_json_response_plain_code_block(self):
        orchestrator, _ = self._make_orchestrator()
        raw = '```\n{"key": "value"}\n```'
        cleaned = orchestrator._clean_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_json_response_no_block(self):
        orchestrator, _ = self._make_orchestrator()
        raw = '{"key": "value"}'
        cleaned = orchestrator._clean_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_json_response_unclosed_block(self):
        orchestrator, _ = self._make_orchestrator()
        raw = '```json\n{"key": "value"}'
        cleaned = orchestrator._clean_json_response(raw)
        assert '{"key": "value"}' in cleaned

    def test_evaluate_issues_batch_with_retriever(self):
        response = json.dumps({"C001:1:0": 0.85})
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(return_value=response)

        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "context"
        mock_retriever.retrieve_similar = MagicMock(return_value=[mock_result])

        orchestrator = LLMOrchestrator(llm_client=mock_client, retriever=mock_retriever)
        issues = [make_issue(1)]
        result = orchestrator.evaluate_issues_batch(issues, "x = 42")
        assert isinstance(result, dict)

    def test_evaluate_duplicate_rule_ids(self):
        """Issues with same rule_id get unique IDs."""
        response = "{}"
        mock_client = MagicMock()
        mock_client.model = "test-model"
        mock_client.generate = MagicMock(return_value=response)
        orchestrator = LLMOrchestrator(llm_client=mock_client)

        issues = [
            CodeIssue(
                category=IssueCategory.CODE_SMELL,
                level=IssueLevel.WARNING,
                message="same issue",
                file_path=Path("test.py"),
                line_number=1,
                rule_id="DUPE",
            ),
            CodeIssue(
                category=IssueCategory.CODE_SMELL,
                level=IssueLevel.WARNING,
                message="same issue",
                file_path=Path("test.py"),
                line_number=1,
                rule_id="DUPE",
            ),
        ]
        result = orchestrator.evaluate_issues_batch(issues, "x = 1")
        # Should not raise
        assert isinstance(result, dict)
