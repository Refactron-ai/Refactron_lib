"""
Day 2 — SHA-256 hardening for IncrementalAnalysisTracker.

Tests verify that:
- A file whose content changes is detected as changed even if mtime is rolled back
- A file whose mtime changes but content is identical is NOT re-analyzed
- Backup integrity validation catches a corrupted backup file
- Rollback skips corrupt backup files and reports them as failures
"""

import hashlib
import os
from pathlib import Path

from refactron.core.backup import BackupManager
from refactron.core.incremental import IncrementalAnalysisTracker

# ─── helpers ────────────────────────────────────────────────────────────────


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ─── IncrementalAnalysisTracker (SHA-256 hardening) ─────────────────────────


def test_cache_invalidates_on_content_change_not_mtime(tmp_path):
    """Content change must trigger re-analysis even when mtime is rolled back to original."""
    state_file = tmp_path / "state.json"
    tracker = IncrementalAnalysisTracker(state_file=state_file, enabled=True)

    py_file = tmp_path / "module.py"
    _write(py_file, "x = 1\n")

    # Record initial state
    tracker.update_file_state(py_file)
    original_mtime = py_file.stat().st_mtime

    # Change content
    _write(py_file, "x = 999  # changed\n")

    # Roll mtime back to the original value — simulates a git checkout or Docker volume
    os.utime(py_file, (original_mtime, original_mtime))

    # mtime is identical to recorded state, but content changed — must detect it
    assert tracker.has_file_changed(py_file), (
        "File with changed content must be detected as changed, "
        "even when mtime is rolled back to the original value"
    )


def test_cache_stable_when_content_unchanged_but_mtime_changes(tmp_path):
    """A file whose mtime is bumped but content is identical must NOT trigger re-analysis."""
    state_file = tmp_path / "state.json"
    tracker = IncrementalAnalysisTracker(state_file=state_file, enabled=True)

    py_file = tmp_path / "module.py"
    content = "x = 1\n"
    _write(py_file, content)

    # Record initial state
    tracker.update_file_state(py_file)

    # Advance mtime by 1 second without changing content — simulates a `touch`
    new_mtime = py_file.stat().st_mtime + 1.0
    os.utime(py_file, (new_mtime, new_mtime))

    # Content is identical → should NOT be considered changed
    assert not tracker.has_file_changed(py_file), (
        "File with unchanged content must not trigger re-analysis, "
        "even when mtime advances (e.g. after git checkout or touch)"
    )


def test_state_persists_sha256_across_reload(tmp_path):
    """SHA-256 stored by update_file_state must survive save/reload."""
    state_file = tmp_path / "state.json"
    py_file = tmp_path / "module.py"
    _write(py_file, "y = 42\n")

    tracker1 = IncrementalAnalysisTracker(state_file=state_file, enabled=True)
    tracker1.update_file_state(py_file)
    tracker1.save()

    # Advance mtime, same content
    new_mtime = py_file.stat().st_mtime + 5.0
    os.utime(py_file, (new_mtime, new_mtime))

    tracker2 = IncrementalAnalysisTracker(state_file=state_file, enabled=True)
    assert not tracker2.has_file_changed(
        py_file
    ), "After reload, unchanged content must still be recognised as unchanged"


# ─── BackupManager integrity validation ─────────────────────────────────────


def test_backup_stores_sha256_in_index(tmp_path):
    """backup_file() must record a 'sha256' field in the backup index."""
    mgr = BackupManager(root_dir=tmp_path)
    session_id = mgr.create_backup_session("test")

    source = tmp_path / "app.py"
    _write(source, "print('hello')\n")

    mgr.backup_file(source, session_id)

    session = mgr.get_session(session_id)
    assert session is not None
    file_record = session["files"][0]
    assert "sha256" in file_record, "Backup index must include sha256 of backed-up file"
    assert file_record["sha256"] == _sha256(source)


def test_backup_validation_passes_for_intact_backup(tmp_path):
    """validate_backup_integrity() must return True for an unmodified backup."""
    mgr = BackupManager(root_dir=tmp_path)
    session_id = mgr.create_backup_session("test")

    source = tmp_path / "app.py"
    _write(source, "x = 1\n")
    mgr.backup_file(source, session_id)

    valid, corrupt = mgr.validate_backup_integrity(session_id)
    assert valid == [str(source)]
    assert corrupt == []


def test_backup_validation_catches_corrupted_file(tmp_path):
    """validate_backup_integrity() must flag a backup file whose content was altered."""
    mgr = BackupManager(root_dir=tmp_path)
    session_id = mgr.create_backup_session("test")

    source = tmp_path / "app.py"
    _write(source, "x = 1\n")
    backup_path = mgr.backup_file(source, session_id)

    # Corrupt the backup by overwriting it with different content
    backup_path.write_text("CORRUPTED\n", encoding="utf-8")

    valid, corrupt = mgr.validate_backup_integrity(session_id)
    assert str(source) in corrupt
    assert str(source) not in valid


def test_rollback_refuses_invalid_backup(tmp_path):
    """rollback_session() must skip corrupt backup files and include them in failed_files."""
    mgr = BackupManager(root_dir=tmp_path)
    session_id = mgr.create_backup_session("test")

    source = tmp_path / "app.py"
    original_content = "x = 1\n"
    _write(source, original_content)
    backup_path = mgr.backup_file(source, session_id)

    # Modify the original (simulate a refactoring was applied)
    _write(source, "x = 999  # refactored\n")

    # Corrupt the backup
    backup_path.write_text("CORRUPTED\n", encoding="utf-8")

    restored_count, failed_files = mgr.rollback_session(session_id)

    # The file should NOT be restored from a corrupt backup
    assert restored_count == 0
    assert str(source) in failed_files
    # Original file should not have been overwritten with corrupted content
    assert source.read_text(encoding="utf-8") == "x = 999  # refactored\n"


def test_rollback_succeeds_for_intact_backup(tmp_path):
    """rollback_session() must restore files correctly when backup is intact."""
    mgr = BackupManager(root_dir=tmp_path)
    session_id = mgr.create_backup_session("test")

    source = tmp_path / "app.py"
    original_content = "x = 1\n"
    _write(source, original_content)
    mgr.backup_file(source, session_id)

    # Simulate refactoring changing the file
    _write(source, "x = 999  # refactored\n")

    restored_count, failed_files = mgr.rollback_session(session_id)

    assert restored_count == 1
    assert failed_files == []
    assert source.read_text(encoding="utf-8") == original_content
