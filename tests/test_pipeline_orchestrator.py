"""Tests for RefactronPipeline orchestrator."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.core.pipeline import RefactronPipeline
from refactron.core.pipeline_session import (  # noqa: F401
    FixStatus,
    PipelineSession,
    SessionState,
    SessionStore,
)


def _make_issue(file_path: Path, level: IssueLevel = IssueLevel.CRITICAL) -> CodeIssue:
    return CodeIssue(
        category=IssueCategory.COMPLEXITY,
        level=level,
        message="too complex",
        file_path=file_path,
        line_number=5,
        column=0,
        suggestion="simplify",
    )


class TestRefactronPipeline:
    def test_analyze_creates_session(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)

        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 0
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        assert session.session_id.startswith("sess_")
        assert session.total_files == 1
        assert session.state == SessionState.ANALYZED

    def test_analyze_saves_session_to_disk(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)

        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 0
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        store = SessionStore(root_dir=tmp_path)
        loaded = store.load(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_queue_issues_adds_to_fix_queue(self, tmp_path):
        py_file = tmp_path / "foo.py"
        py_file.write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        issue = _make_issue(py_file)
        pipeline.queue_issues(session, [issue])
        # Queue should have the issue (either PENDING or SKIPPED)
        assert len(session.fix_queue) == 1

    def test_apply_dry_run_does_not_write(self, tmp_path):
        py_file = tmp_path / "foo.py"
        py_file.write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        issue = _make_issue(py_file)
        pipeline.queue_issues(session, [issue])
        pipeline.apply(session, dry_run=True)
        assert py_file.read_text() == "x = 1\n"

    def test_state_transitions_to_fixed_after_apply(self, tmp_path):
        py_file = tmp_path / "foo.py"
        py_file.write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        pipeline.apply(session, dry_run=True)
        assert session.state == SessionState.FIXED

    def test_last_result_stored_after_analyze(self, tmp_path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)

        mock_result = MagicMock()
        mock_result.total_files = 2
        mock_result.total_issues = 0
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            pipeline.analyze(tmp_path)

        assert pipeline._last_result is not None
        assert pipeline._last_result.total_files == 2
