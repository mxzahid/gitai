"""Constants and templates for GitAI."""

from typing import Final

# Commit message prompts
COMMIT_SYSTEM_PROMPT: Final[
    str
] = """You are an expert release engineer. Output plain text only, no code fences.
Follow Conventional Commits strictly. Do not invent changes."""

COMMIT_USER_PROMPT_SINGLE: Final[
    str
] = """Generate a Conventional Commit message from this unified diff.

Rules:
- Subject < 70 chars: type(optional-scope): message
- Sentence case, no trailing period in subject
- Include a short body with bullet points only if helpful
- Wrap body at 72 columns
- Do not invent changes; reflect only what the diff shows

Diff:
{diff}"""

COMMIT_USER_PROMPT_MERGE: Final[
    str
] = """Given these chunk summaries of staged changes, produce one Conventional Commit message.
Follow the same rules as above. Prefer the most representative type(scope).

Chunk summaries:
{chunk_summaries}"""

# Changelog prompts
CHANGELOG_SYSTEM_PROMPT: Final[str] = (
    """You are an expert technical writer. Output markdown bullets only. Do not invent facts."""
)

CHANGELOG_USER_PROMPT: Final[
    str
] = """Polish these grouped commit bullets for a changelog. Improve clarity and brevity.
Do not add or invent items. Keep issue/PR references unchanged.

Grouped bullets:
{grouped_bullets}"""

# Type mappings for heuristics
TYPE_HINTS_PATH: Final[dict[str, str]] = {
    "tests/": "test",
    "_test.": "test",
    "docs/": "docs",
    ".md": "docs",
    "mkdocs.yml": "docs",
    ".github/workflows/": "ci",
    "Dockerfile": "ci",
    "docker-compose": "ci",
    "Makefile": "build",
    "pyproject.toml": "build",
    "setup.py": "build",
    "requirements": "build",
}

TYPE_HINTS_CONTENT: Final[dict[str, str]] = {
    "add": "feat",
    "new": "feat",
    "create": "feat",
    "remove": "feat",
    "delete": "feat",
    "fix": "fix",
    "bug": "fix",
    "error": "fix",
    "issue": "fix",
    "refactor": "refactor",
    "rename": "chore",
    "move": "chore",
    "update": "feat",
    "improve": "feat",
    "enhance": "feat",
    "optimize": "perf",
    "performance": "perf",
    "speed": "perf",
    "test": "test",
    "testing": "test",
    "doc": "docs",
    "document": "docs",
    "readme": "docs",
    "ci": "ci",
    "build": "ci",
    "config": "ci",
    "chore": "chore",
    "maintenance": "chore",
}

# Conventional Commit types in display order
CHANGELOG_SECTIONS: Final[list[str]] = [
    "Features",
    "Fixes",
    "Performance",
    "Documentation",
    "Refactoring",
    "CI",
    "Build",
    "Tests",
    "Chore",
    "Other",
]

# Type to section mapping
TYPE_TO_SECTION: Final[dict[str, str]] = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "docs": "Documentation",
    "refactor": "Refactoring",
    "ci": "CI",
    "build": "Build",
    "test": "Tests",
    "chore": "Chore",
}

# File size limits
MAX_CHUNK_SIZE: Final[int] = 6000  # characters
MAX_SUBJECT_LENGTH: Final[int] = 100
BODY_WRAP_WIDTH: Final[int] = 72
CHANGELOG_WRAP_WIDTH: Final[int] = 100

# Default timeouts
DEFAULT_TIMEOUT: Final[int] = 45

# Git hook content
HOOK_CONTENT: Final[
    str
] = """#!/usr/bin/env sh
git-ai commit --hook "$1" || exit 0
"""
