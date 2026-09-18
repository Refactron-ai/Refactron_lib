"""Integration tests: full pipeline analyze → queue → apply → state checks."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from refactron.core.models import CodeIssue, FileMetrics, IssueCategory, IssueLevel
from refactron.core.pipeline import RefactronPipeline
from refactron.core.pipeline_session import FixStatus, SessionState


def _make_file_metrics(file_path: Path, issues=None):
    return FileMetrics(
        file_path=file_path,
        lines_of_code=20,
        comment_lines=0,
        blank_lines=0,
        complexity=5.0,
        maintainability_index=70.0,
        functions=1,
        classes=0,
        issues=issues or [],
    )


def _make_issue(file_path: Path, level=IssueLevel.WARNING):
    return CodeIssue(
        category=IssueCategory.COMPLEXITY,
        level=level,
        message="magic number 42",
        file_path=file_path,
        line_number=3,
        column=0,
        suggestion="extract to constant",
    )


class TestFullPipeline:
    def test_analyze_queue_apply_roundtrip(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 42\ny = x + 1\n")
        issue = _make_issue(py_file)

        pipeline = RefactronPipeline(project_root=tmp_path)

        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 1
        mock_result.file_metrics = [_make_file_metrics(py_file, issues=[issue])]

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        assert session.total_files == 1
        assert session.state == SessionState.ANALYZED

        pipeline.queue_issues(session, [issue])
        assert len(session.fix_queue) > 0

        pipeline.apply(session, dry_run=True)
        assert session.state == SessionState.FIXED

    def test_session_persisted_after_analyze(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")

        pipeline = RefactronPipeline(project_root=tmp_path)
        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 0
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        loaded = pipeline.store.load(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_blocked_fix_recorded_when_file_missing(self, tmp_path):
        pipeline = RefactronPipeline(project_root=tmp_path)
        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 1
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        ghost_issue = _make_issue(Path("/nonexistent/ghost.py"))

        # Patch fix_engine so it thinks it can fix the issue (fixer_name != None),
        # causing the item to be PENDING and then BLOCKED when file is missing.
        with patch.object(pipeline.fix_engine, "can_fix", return_value=True), patch.object(
            pipeline.fix_engine,
            "fixers",
            {"magic_number": MagicMock(preview=MagicMock(return_value=MagicMock(success=True)))},
        ):
            pipeline.queue_issues(session, [ghost_issue])

        pipeline.apply(session, dry_run=False)

        # Ghost file doesn't exist → PENDING item should be moved to blocked_fixes
        all_blocked = session.blocked_fixes + [
            i for i in session.fix_queue if i.status == FixStatus.BLOCKED
        ]
        assert len(all_blocked) > 0

    def test_min_level_filter_in_queue_issues(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")
        pipeline = RefactronPipeline(project_root=tmp_path)
        mock_result = MagicMock()
        mock_result.total_files = 1
        mock_result.total_issues = 2
        mock_result.file_metrics = []

        with patch("refactron.core.pipeline.Refactron") as mock_cls:
            mock_cls.return_value.analyze.return_value = mock_result
            session = pipeline.analyze(tmp_path)

        critical_issue = _make_issue(py_file, level=IssueLevel.CRITICAL)
        info_issue = _make_issue(py_file, level=IssueLevel.INFO)

        pipeline.queue_issues(session, [critical_issue, info_issue], min_level=IssueLevel.ERROR)

        # INFO issue should be filtered out (rank 0 < ERROR rank 2)
        assert len(session.fix_queue) == 1
        assert session.fix_queue[0].level == "CRITICAL"
