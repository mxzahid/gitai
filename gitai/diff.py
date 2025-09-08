"""Diff collection and chunking functionality."""

import re
from typing import Any

from .constants import MAX_CHUNK_SIZE
from .util import run


class DiffChunk:
    """Represents a chunk of diff content."""

    def __init__(self, content: str, files: list[str]):
        self.content = content
        self.files = files
        self.size = len(content)

    def __str__(self) -> str:
        return f"DiffChunk({len(self.files)} files, {self.size} chars)"


class StagedDiff:
    """Represents staged changes in a git repository."""

    def __init__(self, raw_diff: str):
        self.raw_diff = raw_diff
        self.files = self._extract_files()
        self.stats = self._extract_stats()

    def _extract_files(self) -> list[str]:
        """Extract file paths from diff."""
        files = []
        lines = self.raw_diff.split("\n")

        for line in lines:
            if line.startswith("diff --git"):
                # extract file paths from diff --git a/path b/path
                match = re.search(r"diff --git a/(.+) b/(.+)", line)
                if match:
                    file_path = match.group(2)  # use b/path (new path)
                    files.append(file_path)

        return files

    def _extract_stats(self) -> dict[str, Any]:
        """Extract statistics from diff."""
        stats = {
            "files_changed": len(self.files),
            "additions": 0,
            "deletions": 0,
            "renames": 0,
            "new_files": 0,
        }

        lines = self.raw_diff.split("\n")
        for line in lines:
            if line.startswith("+++ b/") and line.endswith("(new file)"):
                stats["new_files"] += 1
            elif line.startswith("rename"):
                stats["renames"] += 1
            elif line.startswith("+") and not line.startswith("+++"):
                stats["additions"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                stats["deletions"] += 1

        return stats

    def is_empty(self) -> bool:
        """Check if diff is empty."""
        return not self.raw_diff.strip()

    def chunk_by_files(self, max_size: int = MAX_CHUNK_SIZE) -> list[DiffChunk]:
        """Chunk diff by files to stay within size limits."""
        if self.is_empty():
            return []

        chunks = []
        current_chunk = ""
        current_files: list[str] = []

        # split diff by file boundaries
        file_sections = re.split(r"(?=diff --git)", self.raw_diff)

        for section in file_sections:
            if not section.strip():
                continue

            # extract file path from this section
            file_match = re.search(r"diff --git a/(.+) b/(.+)", section)
            if file_match:
                file_path = file_match.group(2)

                # check if adding this file would exceed the chunk size
                if len(current_chunk + section) > max_size and current_chunk:
                    # create chunk with current content
                    chunks.append(DiffChunk(current_chunk.strip(), current_files))
                    current_chunk = section
                    current_files = [file_path]
                else:
                    current_chunk += section
                    current_files.append(file_path)

        # add remaining content as final chunk
        if current_chunk.strip():
            chunks.append(DiffChunk(current_chunk.strip(), current_files))

        return chunks


def get_staged_diff() -> StagedDiff:
    """Get staged diff from git."""
    try:
        raw_diff = run(["git", "diff", "--staged", "-U0"])
        return StagedDiff(raw_diff)
    except SystemExit:
        # return empty diff if command fails
        return StagedDiff("")


def get_diff_between_refs(since_ref: str, to_ref: str = "HEAD") -> str:
    """Get diff between two git references."""
    try:
        return run(
            [
                "git",
                "log",
                "--pretty=format:%H%n%s%n%b---END---",
                f"{since_ref}..{to_ref}",
            ]
        )
    except SystemExit:
        return ""


def get_commit_history(since_ref: str, to_ref: str = "HEAD") -> list[dict[str, str]]:
    """Get commit history between two references."""
    try:
        log_output = run(
            [
                "git",
                "log",
                "--pretty=format:%H%n%s%n%b---END---",
                f"{since_ref}..{to_ref}",
            ]
        )

        commits = []
        sections = log_output.split("---END---")

        for section in sections:
            lines = section.strip().split("\n")
            if len(lines) >= 2:
                commit_hash = lines[0]
                subject = lines[1]
                body = "\n".join(lines[2:]) if len(lines) > 2 else ""

                commits.append(
                    {
                        "hash": commit_hash,
                        "subject": subject,
                        "body": body,
                    }
                )

        return commits
    except SystemExit:
        return []
