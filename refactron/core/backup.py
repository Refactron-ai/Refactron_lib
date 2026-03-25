"""
Backup and Rollback System for Refactron.

Provides functionality to:
- Auto-create .refactron-backup/ directory with original files before changes
- Git integration for automatic commits before major refactoring
- Rollback capability to restore original files
"""

import hashlib
import json
import logging
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage backups and rollbacks for refactoring operations."""

    BACKUP_DIR_NAME = ".refactron-backup"
    INDEX_FILE = "backup_index.json"

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize the backup manager.

        Args:
            root_dir: Root directory for backups. Defaults to current working directory.
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.backup_dir = self.root_dir / self.BACKUP_DIR_NAME
        self.index_file = self.backup_dir / self.INDEX_FILE
        self._index: Dict[str, Any] = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load backup index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                return {"sessions": [], "version": "1.0"}
        return {"sessions": [], "version": "1.0"}

    def _save_index(self) -> None:
        """Save backup index to disk."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, indent=2)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to save backup index: {e}")
            raise

    def create_backup_session(self, description: str = "") -> str:
        """
        Create a new backup session.

        Args:
            description: Description of the operation being performed.

        Returns:
            Session ID for the backup session.
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}_{now.strftime('%f')}"
        session_dir = self.backup_dir / session_id

        session_dir.mkdir(parents=True, exist_ok=True)

        session_info = {
            "id": session_id,
            "timestamp": timestamp,
            "description": description,
            "files": [],
            "git_commit": None,
        }

        self._index["sessions"].append(session_info)
        self._save_index()

        return session_id

    def backup_file(self, file_path: Path, session_id: str) -> Path:
        """
        Backup a single file to the backup directory.

        Args:
            file_path: Path to the file to backup.
            session_id: Session ID for this backup operation.

        Returns:
            Path to the backup file.
        """
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        session_dir = self.backup_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        try:
            relative_path = file_path.relative_to(self.root_dir)
        except ValueError:
            relative_path = Path(file_path.name)

        backup_path = session_dir / relative_path

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)

        file_sha256 = hashlib.sha256(backup_path.read_bytes()).hexdigest()

        for session in self._index["sessions"]:
            if session["id"] == session_id:
                session["files"].append(
                    {
                        "original": str(file_path),
                        "backup": str(backup_path),
                        "relative_path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "sha256": file_sha256,
                    }
                )
                break

        self._save_index()
        return backup_path

    def backup_files(
        self, file_paths: List[Path], session_id: str
    ) -> Tuple[List[Path], List[Path]]:
        """
        Backup multiple files.

        Args:
            file_paths: List of file paths to backup.
            session_id: Session ID for this backup operation.

        Returns:
            Tuple of (successful backup paths, failed file paths).
        """
        backup_paths = []
        failed_paths = []
        for file_path in file_paths:
            try:
                backup_path = self.backup_file(file_path, session_id)
                backup_paths.append(backup_path)
            except FileNotFoundError:
                logger.warning(f"File not found during backup, skipping: {file_path}")
                failed_paths.append(file_path)
        return backup_paths, failed_paths

    def rollback_session(self, session_id: Optional[str] = None) -> Tuple[int, List[str]]:
        """
        Rollback files from a backup session.

        Args:
            session_id: Session ID to rollback. If None, uses the latest session.

        Returns:
            Tuple of (number of files restored, list of failed file paths).
        """
        if not self._index["sessions"]:
            return 0, []

        if session_id is None:
            session = self._index["sessions"][-1]
        else:
            session = None
            for s in self._index["sessions"]:
                if s["id"] == session_id:
                    session = s
                    break

        if session is None:
            return 0, []

        # Validate backup integrity before restoring anything
        _, corrupt_paths = self.validate_backup_integrity(session["id"])
        corrupt_set = set(corrupt_paths)

        restored_count = 0
        failed_files = []
        for file_info in session["files"]:
            backup_path = Path(file_info["backup"])
            original_path = Path(file_info["original"])

            if str(original_path) in corrupt_set:
                logger.warning(
                    f"Skipping restore of {original_path}: backup failed integrity check"
                )
                failed_files.append(str(original_path))
                continue

            if backup_path.exists():
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, original_path)
                restored_count += 1
            else:
                logger.warning(f"Backup file missing, cannot restore: {backup_path}")
                failed_files.append(str(original_path))

        return restored_count, failed_files

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all backup sessions.

        Returns:
            List of session information dictionaries.
        """
        return self._index["sessions"]  # type: ignore[no-any-return]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific session.

        Args:
            session_id: Session ID to look up.

        Returns:
            Session information or None if not found.
        """
        for session in self._index["sessions"]:
            if session["id"] == session_id:
                return session  # type: ignore[no-any-return]
        return None

    def validate_backup_integrity(self, session_id: str) -> Tuple[List[str], List[str]]:
        """Verify that every backup file in a session matches its recorded SHA-256.

        Args:
            session_id: Session ID to validate.

        Returns:
            Tuple of (valid_original_paths, corrupt_original_paths).
            A path is "corrupt" if its backup file is missing or its hash doesn't match.
        """
        session = self.get_session(session_id)
        if session is None:
            return [], []

        valid: List[str] = []
        corrupt: List[str] = []

        for file_info in session["files"]:
            original_path = file_info["original"]
            backup_path = Path(file_info["backup"])
            stored_hash = file_info.get("sha256")

            if not backup_path.exists():
                logger.warning(f"Backup file missing for integrity check: {backup_path}")
                corrupt.append(original_path)
                continue

            if stored_hash is None:
                # Legacy backup without hash — treat as valid (best-effort)
                valid.append(original_path)
                continue

            try:
                current_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()
                if current_hash == stored_hash:
                    valid.append(original_path)
                else:
                    logger.warning(
                        f"Backup integrity failure for {original_path}: "
                        f"expected {stored_hash[:8]}…, got {current_hash[:8]}…"
                    )
                    corrupt.append(original_path)
            except Exception as e:
                logger.warning(f"Failed to verify backup for {original_path}: {e}")
                corrupt.append(original_path)

        return valid, corrupt

    def clear_session(self, session_id: str) -> bool:
        """
        Clear a specific backup session.

        Args:
            session_id: Session ID to clear.

        Returns:
            True if successful, False otherwise.
        """
        session_dir = self.backup_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

        self._index["sessions"] = [s for s in self._index["sessions"] if s["id"] != session_id]
        self._save_index()
        return True

    def clear_all_sessions(self) -> int:
        """
        Clear all backup sessions.

        Returns:
            Number of sessions cleared.
        """
        count = len(self._index["sessions"])

        for session in self._index["sessions"]:
            session_dir = self.backup_dir / session["id"]
            if session_dir.exists():
                shutil.rmtree(session_dir)

        self._index["sessions"] = []
        self._save_index()
        return count

    def update_session_git_commit(self, session_id: str, commit_hash: Optional[str]) -> bool:
        """
        Update the Git commit hash for a session.

        Args:
            session_id: Session ID to update.
            commit_hash: Git commit hash to associate with the session.

        Returns:
            True if successful, False if session not found.
        """
        for session in self._index["sessions"]:
            if session["id"] == session_id:
                session["git_commit"] = commit_hash
                self._save_index()
                return True
        return False

    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest backup session.

        Returns:
            Latest session information or None if no sessions exist.
        """
        if self._index["sessions"]:
            return self._index["sessions"][-1]  # type: ignore[no-any-return]
        return None


class GitIntegration:
    """Git integration for automatic commits before refactoring."""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize Git integration.

        Args:
            repo_path: Path to the Git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def is_git_repo(self) -> bool:
        """Check if the current directory is a Git repository."""
        git_dir = self.repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        if not self.is_git_repo():
            return False

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch name."""
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_current_commit(self) -> Optional[str]:
        """Get the current commit hash."""
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def create_pre_refactor_commit(
        self, message: Optional[str] = None, files: Optional[List[Path]] = None
    ) -> Optional[str]:
        """
        Create a commit before refactoring.

        Args:
            message: Commit message. Defaults to auto-generated message.
            files: Specific files to commit. If None, stages and commits all
                   uncommitted changes (git add -A). Note: This may include
                   unintended files like temporary files or build artifacts.

        Returns:
            Commit hash if successful, None otherwise.
        """
        if not self.is_git_repo():
            return None

        if not self.has_uncommitted_changes():
            return self.get_current_commit()

        try:
            if files:
                for file_path in files:
                    subprocess.run(
                        ["git", "add", str(file_path)],
                        cwd=self.repo_path,
                        capture_output=True,
                        check=True,
                    )
            else:
                logger.warning(
                    "No specific files provided; staging all changes (git add -A). "
                    "This may include unintended files."
                )
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=True,
                )

            if message is None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"refactron: pre-refactor snapshot ({timestamp})"

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )

            return self.get_current_commit()

        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def _is_valid_git_ref(ref: str) -> bool:
        """Validate that a string is a valid Git reference (commit hash or branch name)."""
        if not ref:
            return False
        if ref.startswith(".") or ".." in ref:
            return False
        dangerous_chars = [";", "&", "|", "$", "`", "\n", "\r", " ", "\\"]
        if any(char in ref for char in dangerous_chars):
            return False
        git_ref_pattern = re.compile(r"^[a-fA-F0-9]{7,40}$|^[a-zA-Z][a-zA-Z0-9._/-]*$")
        return bool(git_ref_pattern.match(ref))

    def git_rollback_to_commit(self, commit_hash: str) -> bool:
        """
        Rollback to a specific commit (soft reset).

        Args:
            commit_hash: Commit hash to rollback to.

        Returns:
            True if successful, False otherwise.
        """
        if not self.is_git_repo():
            return False

        if not self._is_valid_git_ref(commit_hash):
            logger.error(f"Invalid git reference: {commit_hash}")
            return False

        try:
            subprocess.run(
                ["git", "checkout", commit_hash, "--", "."],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False


class BackupRollbackSystem:
    """
    Combined backup and rollback system that integrates file backups with Git.
    """

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize the backup and rollback system.

        Args:
            root_dir: Root directory for operations.
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.backup_manager = BackupManager(self.root_dir)
        self.git = GitIntegration(self.root_dir)

    def prepare_for_refactoring(
        self,
        files: List[Path],
        description: str = "refactoring operation",
        create_git_commit: bool = True,
    ) -> Tuple[str, List[Path]]:
        """
        Prepare for a refactoring operation by creating backups and optionally a Git commit.

        Args:
            files: List of files to be refactored.
            description: Description of the refactoring operation.
            create_git_commit: Whether to create a Git commit before refactoring.

        Returns:
            Tuple of (session ID, list of files that failed to backup).
        """
        session_id = self.backup_manager.create_backup_session(description)

        _, failed_files = self.backup_manager.backup_files(files, session_id)

        if create_git_commit and self.git.is_git_repo():
            commit_hash = self.git.create_pre_refactor_commit(
                message=f"refactron: backup before {description}",
                files=files,
            )
            self.backup_manager.update_session_git_commit(session_id, commit_hash)

        return session_id, failed_files

    def rollback(
        self,
        session_id: Optional[str] = None,
        use_git: bool = False,
    ) -> Dict[str, Any]:
        """
        Rollback changes from a refactoring session.

        Args:
            session_id: Session ID to rollback. If None, uses the latest session.
            use_git: Whether to use Git rollback instead of file backup.

        Returns:
            Dictionary with rollback results.
        """
        result: Dict[str, Any] = {
            "success": False,
            "method": "git" if use_git else "backup",
            "files_restored": 0,
            "failed_files": [],
            "message": "",
        }

        if use_git:
            if session_id:
                session = self.backup_manager.get_session(session_id)
            else:
                session = self.backup_manager.get_latest_session()

            if session and session.get("git_commit"):
                if self.git.git_rollback_to_commit(session["git_commit"]):
                    result["success"] = True
                    result["message"] = f"Rolled back to commit {session['git_commit']}"
                else:
                    result["message"] = "Git rollback failed"
            else:
                result["message"] = "No Git commit found for session"
        else:
            files_restored, failed_files = self.backup_manager.rollback_session(session_id)
            result["files_restored"] = files_restored
            result["failed_files"] = failed_files
            result["success"] = files_restored > 0
            if failed_files:
                result["message"] = (
                    f"Restored {files_restored} file(s), {len(failed_files)} file(s) failed"
                )
            else:
                result["message"] = (
                    f"Restored {files_restored} file(s)"
                    if files_restored > 0
                    else "No files to restore"
                )

        return result

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all backup sessions."""
        return self.backup_manager.list_sessions()

    def clear_all(self) -> int:
        """Clear all backup sessions."""
        return self.backup_manager.clear_all_sessions()
