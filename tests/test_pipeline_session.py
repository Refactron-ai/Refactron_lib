"""Tests for PipelineSession data model and SessionStore."""
from refactron.core.pipeline_session import (
    FixQueueItem,
    FixStatus,
    PipelineSession,
    SessionState,
    SessionStore,
)


class TestPipelineSession:
    def test_session_created_with_defaults(self, tmp_path):
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        assert session.session_id == "sess_001"
        assert session.state == SessionState.ANALYZED
        assert session.fix_queue == []
        assert session.applied_fixes == []
        assert session.blocked_fixes == []

    def test_session_to_dict_roundtrip(self, tmp_path):
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        d = session.to_dict()
        restored = PipelineSession.from_dict(d)
        assert restored.session_id == session.session_id
        assert restored.state == session.state

    def test_queue_item_pending_by_default(self):
        item = FixQueueItem(
            issue_id="issue_001",
            file_path="/tmp/foo.py",
            line_number=10,
            level="CRITICAL",
            message="too complex",
            fixer_name="ExtractMagicNumbersFixer",
        )
        assert item.status == FixStatus.PENDING


class TestSessionStore:
    def test_save_and_load(self, tmp_path):
        store = SessionStore(root_dir=tmp_path)
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        store.save(session)
        loaded = store.load("sess_001")
        assert loaded.session_id == "sess_001"

    def test_load_latest(self, tmp_path):
        store = SessionStore(root_dir=tmp_path)
        for sid in ["sess_001", "sess_002"]:
            store.save(PipelineSession(
                session_id=sid,
                target=str(tmp_path),
                created_at="2026-04-03T18:00:00",
            ))
        latest = store.load_latest()
        assert latest is not None
        assert latest.session_id == "sess_002"

    def test_load_missing_returns_none(self, tmp_path):
        store = SessionStore(root_dir=tmp_path)
        assert store.load("does_not_exist") is None

    def test_list_sessions(self, tmp_path):
        store = SessionStore(root_dir=tmp_path)
        for sid in ["sess_001", "sess_002", "sess_003"]:
            store.save(PipelineSession(
                session_id=sid,
                target=str(tmp_path),
                created_at="2026-04-03T18:00:00",
            ))
        sessions = store.list_sessions()
        assert len(sessions) == 3

    def test_sessions_dir_created_automatically(self, tmp_path):
        store = SessionStore(root_dir=tmp_path)
        session = PipelineSession(
            session_id="sess_001",
            target=str(tmp_path),
            created_at="2026-04-03T18:00:00",
        )
        store.save(session)
        assert (tmp_path / ".refactron" / "sessions").exists()
