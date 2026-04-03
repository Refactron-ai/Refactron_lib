"""
PipelineSession — shared state carrier for the Refactron connected pipeline.

One session is created per `refactron analyze` invocation and consumed by
every subsequent command (autofix, status, rollback). Persisted as JSON
in <project_root>/.refactron/sessions/<session_id>.json.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

_logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    ANALYZED = "analyzed"
    FIXING = "fixing"
    FIXED = "fixed"
    ROLLED_BACK = "rolled_back"


class FixStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class FixQueueItem:
    """One issue queued for fixing."""

    issue_id: str
    file_path: str
    line_number: int
    level: str
    message: str
    fixer_name: str
    status: FixStatus = FixStatus.PENDING
    diff: Optional[str] = None
    block_reason: Optional[str] = None
    backup_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "level": self.level,
            "message": self.message,
            "fixer_name": self.fixer_name,
            "status": self.status.value,
            "diff": self.diff,
            "block_reason": self.block_reason,
            "backup_path": self.backup_path,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> FixQueueItem:
        return cls(
            issue_id=d["issue_id"],
            file_path=d["file_path"],
            line_number=d["line_number"],
            level=d["level"],
            message=d["message"],
            fixer_name=d["fixer_name"],
            status=FixStatus(d.get("status", "pending")),
            diff=d.get("diff"),
            block_reason=d.get("block_reason"),
            backup_path=d.get("backup_path"),
        )


@dataclass
class PipelineSession:
    """
    Central state object for one Refactron pipeline run.

    Created by `refactron analyze`, consumed by `refactron autofix`,
    `refactron status`, and `refactron rollback`.
    """

    session_id: str
    target: str
    created_at: str
    state: SessionState = SessionState.ANALYZED
    total_files: int = 0
    total_issues: int = 0
    issues_by_level: Dict[str, int] = field(default_factory=dict)
    fix_queue: List[FixQueueItem] = field(default_factory=list)
    applied_fixes: List[FixQueueItem] = field(default_factory=list)
    blocked_fixes: List[FixQueueItem] = field(default_factory=list)
    backup_session_id: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "target": self.target,
            "created_at": self.created_at,
            "state": self.state.value,
            "total_files": self.total_files,
            "total_issues": self.total_issues,
            "issues_by_level": self.issues_by_level,
            "fix_queue": [i.to_dict() for i in self.fix_queue],
            "applied_fixes": [i.to_dict() for i in self.applied_fixes],
            "blocked_fixes": [i.to_dict() for i in self.blocked_fixes],
            "backup_session_id": self.backup_session_id,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PipelineSession:
        return cls(
            session_id=d["session_id"],
            target=d["target"],
            created_at=d["created_at"],
            state=SessionState(d.get("state", "analyzed")),
            total_files=d.get("total_files", 0),
            total_issues=d.get("total_issues", 0),
            issues_by_level=d.get("issues_by_level", {}),
            fix_queue=[FixQueueItem.from_dict(i) for i in d.get("fix_queue", [])],
            applied_fixes=[FixQueueItem.from_dict(i) for i in d.get("applied_fixes", [])],
            blocked_fixes=[FixQueueItem.from_dict(i) for i in d.get("blocked_fixes", [])],
            backup_session_id=d.get("backup_session_id"),
            finished_at=d.get("finished_at"),
        )


class SessionStore:
    """Persists PipelineSession objects to <root>/.refactron/sessions/."""

    SESSIONS_DIR = Path(".refactron") / "sessions"

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.sessions_dir = self.root_dir / self.SESSIONS_DIR

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def save(self, session: PipelineSession) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        path = self._session_path(session.session_id)
        path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    def load(self, session_id: str) -> Optional[PipelineSession]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            session = PipelineSession.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
        if session.session_id != session_id:
            _logger.warning(
                "Session ID mismatch: requested %s, got %s", session_id, session.session_id
            )
        return session

    def load_latest(self) -> Optional[PipelineSession]:
        if not self.sessions_dir.exists():
            return None
        paths = sorted(self.sessions_dir.glob("*.json"))
        if not paths:
            return None
        try:
            return PipelineSession.from_dict(json.loads(paths[-1].read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def list_sessions(self) -> List[PipelineSession]:
        if not self.sessions_dir.exists():
            return []
        sessions: List[PipelineSession] = []
        for p in sorted(self.sessions_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                sessions.append(PipelineSession.from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        return sessions

    @staticmethod
    def make_session_id() -> str:
        now = datetime.now(timezone.utc)
        return f"sess_{now.strftime('%Y%m%d_%H%M%S_%f')}"
