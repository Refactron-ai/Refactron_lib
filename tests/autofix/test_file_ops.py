"""Tests for file operations module."""

import shutil
import tempfile
from pathlib import Path

import pytest

from refactron.autofix.file_ops import FileOperations


class TestFileOperations:
    """Test suite for FileOperations."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp = Path(tempfile.mkdtemp())
        yield temp
        # Cleanup
        if temp.exists():
            shutil.rmtree(temp)

    @pytest.fixture
    def file_ops(self, temp_dir):
        """Create FileOperations instance with temp backup dir."""
        backup_dir = temp_dir / "backups"
        return FileOperations(backup_dir=backup_dir)

    def test_initialization(self, file_ops):
        """Test FileOperations can be initialized."""
        assert file_ops.backup_dir.name == "backups"
        assert isinstance(file_ops.backup_index, dict)

    def test_backup_file(self, temp_dir, file_ops):
        """Test backing up a file."""
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Backup
        backup_path = file_ops.backup_file(test_file)

        assert backup_path.exists()
        assert backup_path.read_text() == "print('hello')"
        assert len(file_ops.backup_index["backups"]) == 1

    def test_backup_nonexistent_file(self, temp_dir, file_ops):
        """Test backing up nonexistent file raises error."""
        nonexistent = temp_dir / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            file_ops.backup_file(nonexistent)

    def test_write_with_backup_new_file(self, temp_dir, file_ops):
        """Test writing a new file (no backup needed)."""
        new_file = temp_dir / "new.py"
        content = "def hello():\n    pass"

        result = file_ops.write_with_backup(new_file, content)

        assert result["success"] is True
        assert new_file.exists()
        assert new_file.read_text() == content
        assert result["backup"] is None

    def test_write_with_backup_existing_file(self, temp_dir, file_ops):
        """Test writing to existing file creates backup."""
        existing_file = temp_dir / "existing.py"
        existing_file.write_text("old content")

        new_content = "new content"
        result = file_ops.write_with_backup(existing_file, new_content)

        assert result["success"] is True
        assert existing_file.read_text() == new_content
        assert result["backup"] is not None

        # Check backup contains old content
        backup_path = Path(result["backup"])
        assert backup_path.exists()
        assert backup_path.read_text() == "old content"

    def test_rollback_file(self, temp_dir, file_ops):
        """Test rolling back a file."""
        test_file = temp_dir / "rollback.py"
        test_file.write_text("original")

        # Make a change with backup
        file_ops.write_with_backup(test_file, "modified")
        assert test_file.read_text() == "modified"

        # Rollback
        success = file_ops.rollback_file(test_file)

        assert success is True
        assert test_file.read_text() == "original"

    def test_rollback_file_no_backup(self, temp_dir, file_ops):
        """Test rolling back file with no backup returns False."""
        test_file = temp_dir / "no_backup.py"
        test_file.write_text("content")

        success = file_ops.rollback_file(test_file)
        assert success is False

    def test_rollback_all(self, temp_dir, file_ops):
        """Test rolling back all files."""
        # Create and modify multiple files
        file1 = temp_dir / "file1.py"
        file2 = temp_dir / "file2.py"

        file1.write_text("original1")
        file2.write_text("original2")

        file_ops.write_with_backup(file1, "modified1")
        file_ops.write_with_backup(file2, "modified2")

        # Rollback all
        count = file_ops.rollback_all()

        assert count == 2
        assert file1.read_text() == "original1"
        assert file2.read_text() == "original2"

    def test_list_backups(self, temp_dir, file_ops):
        """Test listing backups."""
        test_file = temp_dir / "test.py"
        test_file.write_text("content")

        file_ops.write_with_backup(test_file, "new content")

        backups = file_ops.list_backups()

        assert len(backups) == 1
        assert "original" in backups[0]
        assert "backup" in backups[0]
        assert "timestamp" in backups[0]

    def test_clear_backups(self, temp_dir, file_ops):
        """Test clearing all backups."""
        test_file = temp_dir / "test.py"
        test_file.write_text("content")

        file_ops.write_with_backup(test_file, "new")
        assert len(file_ops.backup_index["backups"]) == 1

        count = file_ops.clear_backups()

        assert count == 1
        assert len(file_ops.backup_index["backups"]) == 0

    def test_atomic_write(self, temp_dir, file_ops):
        """Test that writes are atomic (temp file → rename)."""
        test_file = temp_dir / "atomic.py"
        test_file.write_text("original")

        # Write new content
        file_ops.write_with_backup(test_file, "new content")

        # File should exist and have new content
        assert test_file.exists()
        assert test_file.read_text() == "new content"

        # No temp files should remain
        temp_files = list(temp_dir.glob(".*atomic.py*.tmp"))
        assert len(temp_files) == 0
