"""Tests for workspace management logic."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from refactron.core.workspace import WorkspaceManager, WorkspaceMapping


@pytest.fixture
def temp_config(tmp_path):
    """Fixture for temporary workspace config."""
    return tmp_path / "workspaces.json"


@pytest.fixture
def manager(temp_config):
    """Fixture for WorkspaceManager with temp config."""
    return WorkspaceManager(config_path=temp_config)


def test_workspace_mapping_serialization():
    """Test WorkspaceMapping dict conversion."""
    mapping = WorkspaceMapping(
        repo_id=1,
        repo_name="test-repo",
        repo_full_name="user/test-repo",
        local_path="/path/to/local",
        connected_at="2024-01-01T00:00:00Z",
    )
    data = mapping.to_dict()
    assert data["repo_id"] == 1
    assert data["repo_full_name"] == "user/test-repo"

    restored = WorkspaceMapping.from_dict(data)
    assert restored == mapping


def test_manager_initialization(temp_config):
    """Test that manager ensures config directory exists."""
    manager = WorkspaceManager(config_path=temp_config)
    assert temp_config.exists()
    # Should contain empty dict
    with open(temp_config, "r") as f:
        assert json.load(f) == {}


def test_add_and_get_workspace(manager):
    """Test adding and retrieving a workspace."""
    mapping = WorkspaceMapping(
        repo_id=123,
        repo_name="my-app",
        repo_full_name="org/my-app",
        local_path="/local/app",
        connected_at="now",
    )
    manager.add_workspace(mapping)

    # Get by full name
    retrieved = manager.get_workspace("org/my-app")
    assert retrieved == mapping

    # Get by short name
    retrieved_short = manager.get_workspace("my-app")
    assert retrieved_short == mapping


def test_get_workspace_by_path(manager, tmp_path):
    """Test retrieving workspace by local path."""
    local_dir = tmp_path / "app"
    local_dir.mkdir()

    mapping = WorkspaceMapping(
        repo_id=1,
        repo_name="app",
        repo_full_name="user/app",
        local_path=str(local_dir),
        connected_at="now",
    )
    manager.add_workspace(mapping)

    retrieved = manager.get_workspace_by_path(str(local_dir))
    assert retrieved.repo_full_name == "user/app"


def test_list_and_remove_workspace(manager):
    """Test listing and removing workspaces."""
    m1 = WorkspaceMapping(repo_id=1, repo_name="a", repo_full_name="u/a", local_path="/p1", connected_at="t")
    m2 = WorkspaceMapping(repo_id=2, repo_name="b", repo_full_name="u/b", local_path="/p2", connected_at="t")

    manager.add_workspace(m1)
    manager.add_workspace(m2)

    workspaces = manager.list_workspaces()
    assert len(workspaces) == 2

    assert manager.remove_workspace("u/a") is True
    assert manager.remove_workspace("non-existent") is False
    assert len(manager.list_workspaces()) == 1


@patch("pathlib.Path.cwd")
def test_detect_repository_https(mock_cwd, tmp_path):
    """Test repository detection from HTTPS URL."""
    repo_dir = tmp_path / "my-repo"
    repo_dir.mkdir()
    git_dir = repo_dir / ".git"
    git_dir.mkdir()

    config_content = """
[remote "origin"]
    url = https://github.com/user/my-repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
    (git_dir / "config").write_text(config_content)

    manager = WorkspaceManager()
    repo = manager.detect_repository(repo_dir)
    assert repo == "user/my-repo"


@patch("pathlib.Path.cwd")
def test_detect_repository_ssh(mock_cwd, tmp_path):
    """Test repository detection from SSH URL."""
    repo_dir = tmp_path / "ssh-repo"
    repo_dir.mkdir()
    git_dir = repo_dir / ".git"
    git_dir.mkdir()

    config_content = """
[remote "origin"]
    url = git@github.com:org/ssh-repo.git
"""
    (git_dir / "config").write_text(config_content)

    manager = WorkspaceManager()
    repo = manager.detect_repository(repo_dir)
    assert repo == "org/ssh-repo"


def test_detect_repository_none(tmp_path):
    """Test detection when no git repo exists."""
    manager = WorkspaceManager()
    assert manager.detect_repository(tmp_path) is None
