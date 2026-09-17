"""Workspace management for Refactron CLI.

This module handles the mapping between remote GitHub repositories and local
directory paths, enabling seamless navigation and context switching.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse


@dataclass
class WorkspaceMapping:
    """Represents a mapping between a remote repository and a local path."""

    repo_name: str
    repo_full_name: str
    local_path: str
    connected_at: str
    repo_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_name": self.repo_name,
            "repo_full_name": self.repo_full_name,
            "local_path": self.local_path,
            "connected_at": self.connected_at,
            "repo_id": self.repo_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceMapping":
        """Create from dictionary."""
        # Robustly handle missing repo_name by extracting it from repo_full_name if needed
        repo_full_name = data.get("repo_full_name", "")
        repo_name = data.get("repo_name")
        if not repo_name and "/" in repo_full_name:
            repo_name = repo_full_name.split("/")[-1]
        elif not repo_name:
            repo_name = repo_full_name or "unknown"

        return cls(
            repo_id=data.get("repo_id"),
            repo_name=repo_name,
            repo_full_name=repo_full_name,
            local_path=data.get("local_path", ""),
            connected_at=data.get("connected_at", ""),
        )


class WorkspaceManager:
    """Manages workspace mappings between repositories and local paths."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the workspace manager.

        Args:
            config_path: Path to the workspaces.json file (default: ~/.refactron/workspaces.json)
        """
        self.config_path = config_path or (Path.home() / ".refactron" / "workspaces.json")
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """Ensure the configuration directory and file exist."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self._save_workspaces({})

    def _load_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """Load workspace mappings from disk.

        Returns:
            Dictionary mapping repo_full_name to workspace data
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_workspaces(self, workspaces: Dict[str, Dict[str, Any]]) -> None:
        """Save workspace mappings to disk.

        Args:
            workspaces: Dictionary mapping repo_full_name to workspace data
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(workspaces, f, indent=2, sort_keys=True)

        # Set file permissions to 0600 (user read/write only)
        try:
            os.chmod(self.config_path, 0o600)
        except OSError:
            pass

    def add_workspace(self, mapping: WorkspaceMapping) -> None:
        """Add or update a workspace mapping.

        Args:
            mapping: The workspace mapping to add
        """
        workspaces = self._load_workspaces()
        workspaces[mapping.repo_full_name] = mapping.to_dict()
        self._save_workspaces(workspaces)

    def get_workspace(self, repo_name: str) -> Optional[WorkspaceMapping]:
        """Get a workspace mapping by repository name.

        Args:
            repo_name: The repository name (e.g., "repo" or "user/repo")

        Returns:
            The workspace mapping, or None if not found
        """
        workspaces = self._load_workspaces()

        # Try exact match first (full name)
        data = workspaces.get(repo_name)
        if data:
            return WorkspaceMapping.from_dict(data)

        # Try matching by short name (repo name without user)
        repo_name_lower = repo_name.lower()
        for full_name, workspace_data in workspaces.items():
            # Extract short name from full name
            # (e.g., "volumeofsphere" from "omsherikar/volumeofsphere")
            short_name = full_name.split("/")[-1].lower()
            if short_name == repo_name_lower:
                return WorkspaceMapping.from_dict(workspace_data)

        return None

    def get_workspace_by_path(self, local_path: str) -> Optional[WorkspaceMapping]:
        """Get a workspace mapping by local path.

        Args:
            local_path: The local directory path

        Returns:
            The workspace mapping, or None if not found
        """
        normalized_path = str(Path(local_path).resolve())
        workspaces = self._load_workspaces()

        for data in workspaces.values():
            if str(Path(data["local_path"]).resolve()) == normalized_path:
                return WorkspaceMapping.from_dict(data)

        return None

    def list_workspaces(self) -> list[WorkspaceMapping]:
        """List all workspace mappings.

        Returns:
            List of all workspace mappings
        """
        workspaces = self._load_workspaces()
        return [WorkspaceMapping.from_dict(data) for data in workspaces.values()]

    def remove_workspace(self, repo_full_name: str) -> bool:
        """Remove a workspace mapping.

        Args:
            repo_full_name: The full name of the repository

        Returns:
            True if removed, False if not found
        """
        workspaces = self._load_workspaces()
        if repo_full_name in workspaces:
            del workspaces[repo_full_name]
            self._save_workspaces(workspaces)
            return True
        return False

    def detect_repository(self, directory: Optional[Path] = None) -> Optional[str]:
        """Attempt to detect the GitHub repository from the .git config.

        Args:
            directory: Directory to search (default: current directory)

        Returns:
            The repository full name (e.g., "user/repo"), or None if not detected
        """
        search_dir = directory or Path.cwd()
        git_dir = search_dir / ".git"

        if not git_dir.exists():
            # Search parent directories
            for parent in search_dir.parents:
                git_dir = parent / ".git"
                if git_dir.exists():
                    search_dir = parent
                    break
            else:
                return None

        # Try to read the remote URL from .git/config
        config_file = git_dir / "config"
        if not config_file.exists():
            return None

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the remote URL (support both HTTPS and SSH)
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("url = "):
                    url = line.replace("url = ", "").strip()

                    # Extract repo name from URL
                    # HTTPS: https://github.com/user/repo.git
                    # SSH: git@github.com:user/repo.git

                    # Handle SSH GitHub URLs explicitly (SCP-like syntax)
                    if url.startswith("git@github.com:"):
                        repo_path = url.replace("git@github.com:", "", 1).replace(".git", "")
                        if repo_path:
                            return repo_path

                    # Handle HTTPS/HTTP GitHub URLs with proper parsing
                    elif "://" in url:
                        try:
                            parsed = urlparse(url)
                            # Validate hostname is exactly github.com (not a substring)
                            if parsed.hostname == "github.com":
                                path = parsed.path.lstrip("/")
                                if path.endswith(".git"):
                                    path = path[:-4]  # Remove .git suffix
                                if path:
                                    return path
                        except ValueError:
                            continue

        except (IOError, OSError):
            pass

        return None
