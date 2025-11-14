"""
File operations for auto-fix system with backup and rollback support.
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileOperations:
    """Handle file operations with safety guarantees."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize file operations.

        Args:
            backup_dir: Directory for backups (default: .refactron_backups)
        """
        self.backup_dir = backup_dir or Path(".refactron_backups")
        self.backup_index_file = self.backup_dir / "index.json"
        self.backup_index = self._load_backup_index()

    def _load_backup_index(self) -> Dict[Any, Any]:
        """Load backup index from disk."""
        if self.backup_index_file.exists():
            try:
                with open(self.backup_index_file, "r") as f:
                    result: Dict[Any, Any] = json.load(f)  # type: ignore[assignment]
                    return result
            except Exception:
                return {"backups": []}
        return {"backups": []}

    def _save_backup_index(self) -> None:
        """Save backup index to disk."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        with open(self.backup_index_file, "w") as f:
            json.dump(self.backup_index, f, indent=2)

    def backup_file(self, filepath: Path) -> Path:
        """
        Create a backup of a file.

        Args:
            filepath: Path to file to backup

        Returns:
            Path to backup file
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        # Copy file
        shutil.copy2(filepath, backup_path)

        # Update index
        self.backup_index["backups"].append(
            {
                "original": str(filepath),
                "backup": str(backup_path),
                "timestamp": timestamp,
                "size": filepath.stat().st_size,
            }
        )
        self._save_backup_index()

        return backup_path

    def write_with_backup(self, filepath: Path, content: str) -> Dict:
        """
        Write content to file with automatic backup.

        Args:
            filepath: Path to file to write
            content: Content to write

        Returns:
            Dictionary with operation details
        """
        # Create backup if file exists
        backup_path = None
        if filepath.exists():
            backup_path = self.backup_file(filepath)

        # Write atomically (temp file → rename)
        try:
            # Create temp file in same directory
            temp_fd, temp_path = tempfile.mkstemp(
                dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp"
            )

            # Write content
            with open(temp_fd, "w") as f:
                f.write(content)

            # Atomic rename
            Path(temp_path).replace(filepath)

            return {
                "success": True,
                "filepath": str(filepath),
                "backup": str(backup_path) if backup_path else None,
                "size": len(content),
            }

        except Exception as e:
            # Rollback if backup exists
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, filepath)
            raise Exception(f"Failed to write file: {e}")

    def rollback_file(self, filepath: Path) -> bool:
        """
        Rollback a file to its last backup.

        Args:
            filepath: Path to file to rollback

        Returns:
            True if successful, False otherwise
        """
        # Find latest backup
        backups = [b for b in self.backup_index["backups"] if b["original"] == str(filepath)]

        if not backups:
            return False

        # Get most recent backup
        latest = sorted(backups, key=lambda x: x["timestamp"], reverse=True)[0]
        backup_path = Path(latest["backup"])

        if not backup_path.exists():
            return False

        # Restore
        shutil.copy2(backup_path, filepath)
        return True

    def rollback_all(self) -> int:
        """
        Rollback all backed up files.

        Returns:
            Number of files rolled back
        """
        count = 0
        processed = set()

        # Group by original file, get latest backup for each
        for backup in reversed(self.backup_index["backups"]):
            original = Path(backup["original"])
            if str(original) in processed:
                continue

            backup_path = Path(backup["backup"])
            if backup_path.exists() and original.exists():
                shutil.copy2(backup_path, original)
                count += 1
                processed.add(str(original))

        return count

    def list_backups(self) -> List[Any]:
        """
        List all backups.

        Returns:
            List of backup information
        """
        result: List[Any] = self.backup_index["backups"]  # type: ignore[assignment]
        return result

    def clear_backups(self) -> int:
        """
        Clear all backups.

        Returns:
            Number of backups cleared
        """
        count = len(self.backup_index["backups"])

        # Remove backup files
        for backup in self.backup_index["backups"]:
            backup_path = Path(backup["backup"])
            if backup_path.exists():
                backup_path.unlink()

        # Clear index
        self.backup_index = {"backups": []}
        self._save_backup_index()

        return count
