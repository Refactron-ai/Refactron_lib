"""Incremental analysis tracking for performance optimization."""

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class IncrementalAnalysisTracker:
    """
    Track file changes to enable incremental analysis.

    Only analyzes files that have changed since the last run.
    Thread-safe for concurrent updates.
    """

    def __init__(
        self,
        state_file: Optional[Path] = None,
        enabled: bool = True,
    ):
        """
        Initialize the incremental analysis tracker.

        Args:
            state_file: Path to the state file. If None, uses default location.
            enabled: Whether incremental analysis is enabled.
        """
        self.enabled = enabled

        if state_file is None:
            import tempfile

            self.state_file = Path(tempfile.gettempdir()) / "refactron_incremental_state.json"
        else:
            self.state_file = Path(state_file)

        # State tracking: file_path -> {mtime, size, sha256}
        # sha256 is the authoritative change signal; mtime/size are fast pre-checks only.
        self._state: Dict[str, Dict[str, object]] = {}

        # Thread lock for safe concurrent access
        self._lock = threading.Lock()

        if self.enabled:
            self._load_state()

    def _load_state(self) -> None:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
                logger.debug(f"Loaded incremental state from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load incremental state: {e}")
                self._state = {}

    def _save_state(self) -> None:
        """Save state to disk."""
        if not self.enabled:
            return

        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            logger.debug(f"Saved incremental state to {self.state_file}")
        except Exception as e:
            logger.warning(f"Failed to save incremental state: {e}")

    def has_file_changed(self, file_path: Path) -> bool:
        """
        Check if a file has changed since the last analysis.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file has changed or is new, False otherwise.
        """
        if not self.enabled:
            return True  # If disabled, consider all files as changed

        if not file_path.exists():
            return False  # File doesn't exist, skip it

        file_path_str = str(file_path.absolute())

        # Get current file stats
        try:
            stat = file_path.stat()
            current_mtime = stat.st_mtime
            current_size = stat.st_size
        except Exception as e:
            logger.warning(f"Failed to get stats for {file_path}: {e}")
            return True  # Assume changed if we can't get stats

        # Check if file is new
        if file_path_str not in self._state:
            logger.debug(f"New file detected: {file_path}")
            return True

        previous = self._state[file_path_str]
        previous_size = previous.get("size", 0)

        # Fast pre-check: size difference means content definitely changed
        if current_size != previous_size:
            logger.debug(f"Changed file detected (size mismatch): {file_path}")
            return True

        # Authoritative check: compare SHA-256 hashes when available
        stored_hash = previous.get("sha256")
        if stored_hash:
            try:
                current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                if current_hash != stored_hash:
                    logger.debug(f"Changed file detected (hash mismatch): {file_path}")
                    return True
                return False  # Same size AND same hash → unchanged
            except Exception as e:
                logger.warning(f"Failed to hash {file_path} for change detection: {e}")
                # Fall through to mtime comparison on hash failure

        # Legacy fallback: no hash stored — use mtime (pre-SHA-256 state entries)
        previous_mtime = previous.get("mtime", 0)
        if current_mtime != previous_mtime:
            logger.debug(f"Changed file detected (mtime mismatch, no hash): {file_path}")
            return True

        return False

    def get_changed_files(self, file_paths: List[Path]) -> List[Path]:
        """
        Filter list of files to only those that have changed.

        Args:
            file_paths: List of file paths to check.

        Returns:
            List of files that have changed or are new.
        """
        if not self.enabled:
            return file_paths

        changed_files = [fp for fp in file_paths if self.has_file_changed(fp)]

        total = len(file_paths)
        changed = len(changed_files)
        skipped = total - changed

        if skipped > 0:
            logger.info(f"Incremental analysis: {changed} changed, {skipped} unchanged (skipped)")

        return changed_files

    def update_file_state(self, file_path: Path) -> None:
        """
        Update the state for a file after analysis.

        Args:
            file_path: Path to the file that was analyzed.
        """
        if not self.enabled:
            return

        if not file_path.exists():
            return

        file_path_str = str(file_path.absolute())

        try:
            stat = file_path.stat()
            content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            with self._lock:
                self._state[file_path_str] = {
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "sha256": content_hash,
                }
        except Exception as e:
            logger.warning(f"Failed to update state for {file_path}: {e}")

    def remove_file_state(self, file_path: Path) -> None:
        """
        Remove a file from the state tracking.

        Args:
            file_path: Path to the file to remove.
        """
        if not self.enabled:
            return

        file_path_str = str(file_path.absolute())
        with self._lock:
            if file_path_str in self._state:
                del self._state[file_path_str]
                logger.debug(f"Removed file from state: {file_path}")

    def cleanup_missing_files(self, valid_file_paths: Set[Path]) -> None:
        """
        Remove files from state that no longer exist or are not in the valid set.

        Args:
            valid_file_paths: Set of file paths that are still valid.
        """
        if not self.enabled:
            return

        valid_paths_str = {str(p.absolute()) for p in valid_file_paths}

        with self._lock:
            # Find files in state that are no longer valid
            to_remove = [fp for fp in self._state.keys() if fp not in valid_paths_str]

            for file_path_str in to_remove:
                del self._state[file_path_str]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} files from incremental state")

    def save(self) -> None:
        """Save the current state to disk."""
        self._save_state()

    def clear(self) -> None:
        """Clear all state data."""
        with self._lock:
            self._state.clear()

        if self.state_file.exists():
            try:
                self.state_file.unlink()
                logger.info("Incremental state cleared")
            except Exception as e:
                logger.warning(f"Failed to clear incremental state: {e}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the tracked state.

        Returns:
            Dictionary containing statistics.
        """
        return {
            "enabled": self.enabled,
            "tracked_files": len(self._state),
        }
