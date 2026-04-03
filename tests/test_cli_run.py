"""Tests for `refactron run` one-shot pipeline command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from refactron.cli.run import run
from refactron.core.pipeline_session import PipelineSession, SessionState


def _make_session(tmp_path, state=SessionState.FIXED):
    return PipelineSession(
        session_id="sess_run_001",
        target=str(tmp_path),
        created_at="2026-04-03T18:00:00+00:00",
        state=state,
        total_files=2,
        total_issues=3,
        issues_by_level={"CRITICAL": 1, "ERROR": 0, "WARNING": 2, "INFO": 0},
        applied_fixes=[],
        blocked_fixes=[],
    )


class TestRunCommand:
    def test_run_dry_run_exits_0(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        session = _make_session(tmp_path)

        with patch("refactron.cli.run.RefactronPipeline") as mock_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.analyze.return_value = session
            mock_pipeline._last_result = None
            mock_pipeline.store = MagicMock()
            mock_cls.return_value = mock_pipeline
            result = runner.invoke(run, [str(tmp_path), "--dry-run"])

        assert result.exit_code == 0

    def test_run_fail_on_critical_exits_1_when_critical_found(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        session = _make_session(tmp_path)
        session.issues_by_level = {"CRITICAL": 1, "ERROR": 0, "WARNING": 0, "INFO": 0}

        with patch("refactron.cli.run.RefactronPipeline") as mock_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.analyze.return_value = session
            mock_pipeline._last_result = None
            mock_pipeline.store = MagicMock()
            mock_cls.return_value = mock_pipeline
            result = runner.invoke(run, [str(tmp_path), "--dry-run", "--fail-on", "CRITICAL"])

        assert result.exit_code == 1

    def test_run_prints_session_id(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        runner = CliRunner()
        session = _make_session(tmp_path)

        with patch("refactron.cli.run.RefactronPipeline") as mock_cls:
            mock_pipeline = MagicMock()
            mock_pipeline.analyze.return_value = session
            mock_pipeline._last_result = None
            mock_pipeline.store = MagicMock()
            mock_cls.return_value = mock_pipeline
            result = runner.invoke(run, [str(tmp_path), "--dry-run"])

        assert "sess_run_001" in result.output
