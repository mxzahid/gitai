"""Command-line interface for GitAI."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from .changelog import ChangelogGenerator
from .commit import CommitGenerator
from .config import Config
from .diff import get_staged_diff
from .hook import install_commit_msg_hook, uninstall_commit_msg_hook
from .util import exit_with_error, print_info, print_success

app = typer.Typer(
    name="git-ai",
    help="Generate Conventional Commit messages and changelog sections using AI",
    add_completion=False,
)

console = Console()


@app.command()
def commit(
    hook: Annotated[
        Optional[str],
        typer.Option(
            "--hook",
            help="Path to COMMIT_EDITMSG file (used by Git hook)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview commit message without committing"),
    ] = False,
    no_body: Annotated[
        bool,
        typer.Option("--no-body", help="Generate subject line only"),
    ] = False,
    style: Annotated[
        Optional[str],
        typer.Option(
            "--style",
            help="Commit style: conventional or plain",
        ),
    ] = None,
) -> None:
    """Generate a commit message from staged changes."""
    try:
        config = Config.load()
        diff = get_staged_diff()

        if diff.is_empty():
            exit_with_error(
                "No staged changes found. Did you forget to run 'git add'?\n"
                "Use 'git status' to see unstaged changes."
            )

        generator = CommitGenerator(config)
        message = generator.generate_commit_message(
            diff=diff,
            hook_path=Path(hook) if hook else None,
            dry_run=dry_run,
            no_body=no_body,
            style=style,
        )

        if hook:
            # Write to hook file
            hook_path = Path(hook)
            hook_path.write_text(message + "\n")
            print_success(f"Generated commit message written to {hook_path}")
        elif dry_run:
            print_info("Generated commit message (dry run):")
            console.print(message)
        else:
            # print to stdout for git commit -m "$(gitai commit)"
            print(message)

    except KeyboardInterrupt:
        exit_with_error("Operation cancelled")
    except Exception as e:
        exit_with_error(f"Error generating commit message: {e}")


@app.command()
def hook(
    action: Annotated[
        str,
        typer.Argument(help="Action to perform: install or uninstall"),
    ],
    force: Annotated[
        bool,
        typer.Option("--force", help="Force overwrite existing hook"),
    ] = False,
) -> None:
    """Install or uninstall Git hooks."""
    if action == "install":
        install_commit_msg_hook(force=force)
    elif action == "uninstall":
        uninstall_commit_msg_hook()
    else:
        exit_with_error("Invalid action. Use 'install' or 'uninstall'")


@app.command()
def changelog(
    since: Annotated[
        str,
        typer.Option("--since", help="Starting reference (tag or commit)"),
    ],
    to: Annotated[
        str,
        typer.Option(
            "--to",
            help="Ending reference (defaults to HEAD)",
        ),
    ] = "HEAD",
    version: Annotated[
        Optional[str],
        typer.Option(
            "--version",
            help="Version for changelog section header",
        ),
    ] = None,
    output: Annotated[
        Optional[str],
        typer.Option(
            "--output",
            help="Output file path (defaults to CHANGELOG.md)",
        ),
    ] = None,
) -> None:
    """Generate changelog section from commit history."""
    if not since:
        exit_with_error("--since is required")

    try:
        config = Config.load()
        generator = ChangelogGenerator(config)

        result = generator.generate_changelog(
            since_ref=since,
            to_ref=to,
            version=version,
            output_path=Path(output) if output else None,
        )

        print_success(result)

    except KeyboardInterrupt:
        exit_with_error("Operation cancelled")
    except Exception as e:
        exit_with_error(f"Error generating changelog: {e}")


@app.callback()
def main() -> None:
    """GitAI - Generate Conventional Commit messages and changelog sections using AI."""
    pass


if __name__ == "__main__":
    app()
