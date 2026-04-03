"""Tests for `refactron status` command."""
from unittest.mock import patch

from click.testing import CliRunner

from refactron.cli.status import status
from refactron.core.pipeline_session import PipelineSession, SessionState


def _make_session(tmp_path, state=SessionState.ANALYZED):
    return PipelineSession(
        session_id="sess_test_001",
        target=str(tmp_path),
        created_at="2026-04-03T18:00:00+00:00",
        state=state,
        total_files=5,
        total_issues=12,
        issues_by_level={"CRITICAL": 2, "ERROR": 0, "WARNING": 7, "INFO": 3},
    )


class TestStatusCommand:
    def test_status_shows_session_info(self, tmp_path):
        session = _make_session(tmp_path)
        runner = CliRunner()
        with patch("refactron.cli.status.SessionStore") as mock_store_cls:
            mock_store_cls.return_value.load_latest.return_value = session
            result = runner.invoke(status, ["--project-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "sess_test_001" in result.output
        assert "5" in result.output

    def test_status_by_session_id(self, tmp_path):
        session = _make_session(tmp_path)
        runner = CliRunner()
        with patch("refactron.cli.status.SessionStore") as mock_store_cls:
            mock_store_cls.return_value.load.return_value = session
            result = runner.invoke(
                status, ["--session", "sess_test_001", "--project-root", str(tmp_path)]
            )
        assert result.exit_code == 0
        assert "sess_test_001" in result.output

    def test_status_no_session_shows_message(self, tmp_path):
        runner = CliRunner()
        with patch("refactron.cli.status.SessionStore") as mock_store_cls:
            mock_store_cls.return_value.load_latest.return_value = None
            result = runner.invoke(status, ["--project-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "No session" in result.output

    def test_status_lists_all_sessions(self, tmp_path):
        runner = CliRunner()
        sessions = [
            PipelineSession(
                session_id=f"sess_{i:03d}",
                target=str(tmp_path),
                created_at="2026-04-03T18:00:00+00:00",
            )
            for i in range(3)
        ]
        with patch("refactron.cli.status.SessionStore") as mock_store_cls:
            mock_store_cls.return_value.list_sessions.return_value = sessions
            result = runner.invoke(status, ["--list", "--project-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "sess_000" in result.output
        assert "sess_002" in result.output
