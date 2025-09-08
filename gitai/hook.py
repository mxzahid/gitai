"""Git hook installation functionality."""

from .constants import HOOK_CONTENT
from .util import (
    backup_file,
    find_git_root,
    make_executable,
    print_success,
    print_warning,
)


def install_commit_msg_hook(force: bool = False) -> None:
    """Install the commit-msg Git hook."""
    git_root = find_git_root()
    hooks_dir = git_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print_warning(".git/hooks directory not found. Is this a valid git repository?")
        return

    hook_path = hooks_dir / "commit-msg"

    # check if hook already exists
    if hook_path.exists() and not force:
        content = hook_path.read_text().strip()
        if content == HOOK_CONTENT.strip():
            print_success("Git-AI commit-msg hook is already installed")
            return

        print_warning("Existing commit-msg hook found:")
        print_warning(str(hook_path))
        print_warning("Use --force to overwrite it, or manually merge the content.")

        # show current content
        print_warning("Current hook content:")
        print_warning(content)
        print_warning("---")
        print_warning("Git-AI hook content:")
        print_warning(HOOK_CONTENT.strip())

        # offer to create backup
        backup = backup_file(hook_path)
        if backup:
            print_success(f"Created backup: {backup}")

        return

    # install the hook
    try:
        hook_path.write_text(HOOK_CONTENT)
        make_executable(hook_path)
        print_success("Installed Git-AI commit-msg hook")
        print_success("The hook will generate commit messages for your commits.")
        print_success("To remove it, delete or modify .git/hooks/commit-msg")

    except Exception as e:
        print_warning(f"Failed to install hook: {e}")


def uninstall_commit_msg_hook() -> None:
    """Remove the Git-AI commit-msg hook."""
    git_root = find_git_root()
    hook_path = git_root / ".git" / "hooks" / "commit-msg"

    if not hook_path.exists():
        print_warning("Git-AI commit-msg hook not found")
        return

    # check if it's our hook
    content = hook_path.read_text().strip()
    if content != HOOK_CONTENT.strip():
        print_warning("Existing hook doesn't match Git-AI hook content")
        print_warning("Refusing to remove potentially modified hook")
        return

    try:
        hook_path.unlink()
        print_success("Removed Git-AI commit-msg hook")
    except Exception as e:
        print_warning(f"Failed to remove hook: {e}")
