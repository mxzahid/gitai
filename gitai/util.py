"""Utility functions for GitAI."""

import shutil
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path
from typing import Any, NoReturn

from rich.console import Console

console = Console()


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    """Run a command and return its stdout."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(cmd)}\n{e.stderr}"
        console.print(f"[red]Error:[/red] {error_msg}")
        if check:
            sys.exit(1)
        return ""


def find_git_root() -> Path:
    """Find the root of the git repository."""
    try:
        result = run(["git", "rev-parse", "--show-toplevel"])
        return Path(result)
    except SystemExit:
        console.print("[red]Error:[/red] Not in a git repository")
        sys.exit(1)


def load_toml_config(path: Path) -> dict[str, Any]:
    """Load TOML configuration file."""
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Failed to load config {path}: {e}")
        return {}


def wrap_text(text: str, width: int = 72) -> str:
    """Wrap text to specified width."""
    return textwrap.fill(
        text, width=width, break_long_words=False, break_on_hyphens=False
    )


def truncate_subject(subject: str, max_length: int = 70) -> str:
    """Truncate subject line if too long."""
    if len(subject) <= max_length:
        return subject

    # try to truncate at word boundary
    truncated = subject[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:  # don't truncate too much
        truncated = truncated[:last_space]

    return truncated.rstrip() + "..."


def extract_scope_from_path(path: str) -> str | None:
    """Extract scope from file path."""
    parts = Path(path).parts
    if not parts:
        return None

    # use first directory as scope
    first_dir = parts[0]
    if first_dir in ("src", "lib", "app", "core", "api", "web", "cli", "utils"):
        return first_dir

    # for deeper paths, use the most specific meaningful directory
    for part in reversed(parts[:-1]):  # exclude filename
        if part not in ("__pycache__", "node_modules", ".git", "tests", "docs"):
            return part

    return None


def make_executable(path: Path) -> None:
    """Make a file executable."""
    current_mode = path.stat().st_mode
    path.chmod(current_mode | 0o111)


def backup_file(path: Path) -> Path | None:
    """Create a backup of a file."""
    if not path.exists():
        return None

    backup_path = path.with_suffix(path.suffix + ".backup")
    counter = 1
    while backup_path.exists():
        backup_path = path.with_suffix(f"{path.suffix}.backup{counter}")
        counter += 1

    shutil.copy2(path, backup_path)
    return backup_path


def exit_with_error(message: str) -> NoReturn:
    """Exit with an error message."""
    console.print(f"[red]Error:[/red] {message}")
    sys.exit(1)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]Info:[/blue] {message}")
