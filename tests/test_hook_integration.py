"""Integration tests for Git hook functionality."""

import os
from unittest.mock import patch

import pytest

from gitai.constants import HOOK_CONTENT
from gitai.hook import install_commit_msg_hook, uninstall_commit_msg_hook


class TestHookIntegration:
    """Test Git hook installation and removal."""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a mock git repository structure."""
        git_dir = tmp_path / ".git"
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        with patch("gitai.hook.find_git_root", return_value=tmp_path):
            yield tmp_path

    def test_install_hook_in_empty_repo(self, git_repo):
        """Test installing hook in repository without existing hook."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        with patch("gitai.util.print_success"):
            install_commit_msg_hook()

        assert hook_path.exists()
        content = hook_path.read_text()
        assert content == HOOK_CONTENT
        assert os.access(hook_path, os.X_OK)

    def test_install_hook_with_existing_hook(self, git_repo):
        """Test installing hook when one already exists."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        existing_content = "#!/bin/bash\necho 'existing hook'\n"
        hook_path.write_text(existing_content)

        with patch("gitai.hook.print_warning") as mock_warning:
            install_commit_msg_hook(force=False)

        mock_warning.assert_called()
        assert hook_path.read_text() == existing_content

    def test_install_hook_with_force(self, git_repo):
        """Test force installing hook over existing one."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        existing_content = "#!/bin/bash\necho 'existing hook'\n"
        hook_path.write_text(existing_content)

        with patch("gitai.util.print_success"):
            install_commit_msg_hook(force=True)

        content = hook_path.read_text()
        assert content == HOOK_CONTENT

    def test_install_hook_already_installed(self, git_repo):
        """Test installing hook when Git-AI hook is already installed."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        hook_path.write_text(HOOK_CONTENT)

        with patch("gitai.hook.print_success") as mock_success:
            install_commit_msg_hook()

        mock_success.assert_called_with("Git-AI commit-msg hook is already installed")

    def test_uninstall_hook(self, git_repo):
        """Test uninstalling Git-AI hook."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        hook_path.write_text(HOOK_CONTENT)

        with patch("gitai.hook.print_success"):
            uninstall_commit_msg_hook()

        assert not hook_path.exists()

    def test_uninstall_hook_not_found(self, git_repo):
        """Test uninstalling when no hook exists."""
        with patch("gitai.hook.print_warning") as mock_warning:
            uninstall_commit_msg_hook()

        mock_warning.assert_called_with("Git-AI commit-msg hook not found")

    def test_uninstall_modified_hook(self, git_repo):
        """Test uninstalling when hook exists but is modified."""
        hooks_dir = git_repo / ".git" / "hooks"
        hook_path = hooks_dir / "commit-msg"

        modified_content = HOOK_CONTENT + "\n# Modified by user\n"
        hook_path.write_text(modified_content)

        with patch("gitai.hook.print_warning") as mock_warning:
            uninstall_commit_msg_hook()

        mock_warning.assert_any_call("Existing hook doesn't match Git-AI hook content")
        mock_warning.assert_any_call("Refusing to remove potentially modified hook")

        assert hook_path.exists()

    def test_install_hook_no_git_repo(self):
        """Test installing hook when not in git repository."""
        with patch("gitai.hook.find_git_root", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                install_commit_msg_hook()
