"""
RefactronPipeline — orchestrates the full analyze → fix → verify → write pipeline.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from refactron.autofix.engine import AutoFixEngine
from refactron.autofix.models import FixRiskLevel
from refactron.core.backup import BackupManager
from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.core.pipeline_session import (
    FixQueueItem,
    FixStatus,
    PipelineSession,
    SessionState,
    SessionStore,
)
from refactron.core.refactron import Refactron

logger = logging.getLogger(__name__)

_LEVEL_MAP: Dict[IssueLevel, str] = {
    IssueLevel.CRITICAL: "CRITICAL",
    IssueLevel.ERROR: "ERROR",
    IssueLevel.WARNING: "WARNING",
    IssueLevel.INFO: "INFO",
}
_LEVEL_REVERSE: Dict[str, IssueLevel] = {v: k for k, v in _LEVEL_MAP.items()}
_LEVEL_RANK: Dict[IssueLevel, int] = {
    IssueLevel.INFO: 0,
    IssueLevel.WARNING: 1,
    IssueLevel.ERROR: 2,
    IssueLevel.CRITICAL: 3,
}


class RefactronPipeline:
    """Connects analysis → fix queue → verification → file write → session persistence."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        safety_level: FixRiskLevel = FixRiskLevel.SAFE,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.store = SessionStore(root_dir=self.project_root)
        self.fix_engine = AutoFixEngine(safety_level=safety_level)
        self.backup_manager = BackupManager(root_dir=self.project_root)
        self._last_result: Any = None

    def analyze(self, target: Path) -> PipelineSession:
        """Run analysis on target, create and save a PipelineSession."""
        r = Refactron()
        result = r.analyze(target)
        self._last_result = result

        session_id = SessionStore.make_session_id()
        now = datetime.now(timezone.utc).isoformat()

        issues_by_level: Dict[str, int] = {
            "CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0
        }
        for fm in result.file_metrics:
            for issue in fm.issues:
                level_str = _LEVEL_MAP.get(issue.level, "INFO")
                issues_by_level[level_str] = issues_by_level.get(level_str, 0) + 1

        session = PipelineSession(
            session_id=session_id,
            target=str(target),
            created_at=now,
            state=SessionState.ANALYZED,
            total_files=result.total_files,
            total_issues=result.total_issues,
            issues_by_level=issues_by_level,
        )
        self.store.save(session)
        logger.info("Pipeline session created: %s", session_id)
        return session

    def queue_issues(
        self,
        session: PipelineSession,
        issues: List[CodeIssue],
        min_level: Optional[IssueLevel] = None,
    ) -> None:
        """Map issues to fixers and add to session.fix_queue."""
        min_rank = _LEVEL_RANK.get(min_level, 0) if min_level else 0

        for idx, issue in enumerate(issues):
            if _LEVEL_RANK.get(issue.level, 0) < min_rank:
                continue
            fixer_name = self._find_fixer_name(issue)
            item = FixQueueItem(
                issue_id=f"issue_{idx:04d}",
                file_path=str(issue.file_path),
                line_number=issue.line_number,
                level=_LEVEL_MAP.get(issue.level, "INFO"),
                message=issue.message,
                fixer_name=fixer_name or "none",
                status=FixStatus.PENDING if fixer_name else FixStatus.SKIPPED,
            )
            session.fix_queue.append(item)
        self.store.save(session)

    def _find_fixer_name(self, issue: CodeIssue) -> Optional[str]:
        if not self.fix_engine.can_fix(issue):
            return None
        for name, fixer in self.fix_engine.fixers.items():
            try:
                result = fixer.preview(issue, "x = 1\n")
                if result.success:
                    return name
            except Exception:
                continue
        return None

    def apply(
        self,
        session: PipelineSession,
        dry_run: bool = True,
        verify: bool = True,
    ) -> None:
        """Verify + write fixes, record results in session."""
        session.state = SessionState.FIXING
        self.store.save(session)

        files_to_fix: Dict[str, List[FixQueueItem]] = {}
        for item in session.fix_queue:
            if item.status == FixStatus.PENDING:
                files_to_fix.setdefault(item.file_path, []).append(item)

        backup_session_id: Optional[str] = None
        if not dry_run and files_to_fix:
            backup_session_id = self.backup_manager.create_backup_session(
                description=f"autofix session {session.session_id}"
            )
            session.backup_session_id = backup_session_id

        for file_path_str, items in files_to_fix.items():
            file_path = Path(file_path_str)
            if not file_path.exists():
                for item in items:
                    item.status = FixStatus.BLOCKED
                    item.block_reason = "file not found"
                    session.blocked_fixes.append(item)
                continue

            issues_for_file = self._queue_items_to_issues(items, file_path)
            try:
                fixed_code, diff = self.fix_engine.fix_file(
                    file_path, issues_for_file, dry_run=dry_run, verify=verify
                )
            except Exception as exc:
                logger.warning("fix_file failed for %s: %s", file_path, exc)
                for item in items:
                    item.status = FixStatus.BLOCKED
                    item.block_reason = str(exc)
                    session.blocked_fixes.append(item)
                continue

            if diff:
                for item in items:
                    item.diff = diff
                    if not dry_run:
                        item.status = FixStatus.APPLIED
                        if backup_session_id:
                            item.backup_path = str(
                                self.backup_manager.backup_dir
                                / backup_session_id
                                / file_path.name
                            )
                        session.applied_fixes.append(item)
            else:
                for item in items:
                    item.status = FixStatus.BLOCKED
                    item.block_reason = "verification blocked or no changes generated"
                    session.blocked_fixes.append(item)

        session.state = SessionState.FIXED
        session.finished_at = datetime.now(timezone.utc).isoformat()
        self.store.save(session)

    def _queue_items_to_issues(
        self, items: List[FixQueueItem], file_path: Path
    ) -> List[CodeIssue]:
        return [
            CodeIssue(
                category=IssueCategory.COMPLEXITY,
                level=_LEVEL_REVERSE.get(item.level, IssueLevel.INFO),
                message=item.message,
                file_path=file_path,
                line_number=item.line_number,
                column=0,
                suggestion=None,
            )
            for item in items
        ]
