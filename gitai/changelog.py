"""Changelog generation functionality."""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .config import Config
from .constants import (
    CHANGELOG_SECTIONS,
    CHANGELOG_SYSTEM_PROMPT,
    CHANGELOG_USER_PROMPT,
    CHANGELOG_WRAP_WIDTH,
    TYPE_TO_SECTION,
)
from .diff import get_commit_history
from .providers.base import create_provider
from .util import wrap_text


class ChangelogGenerator:
    """Generates changelog sections from commit history."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = None

        # Initialize LLM provider if available
        if config.is_llm_available():
            try:
                if config.llm.provider == "openai":
                    self.provider = create_provider(
                        "openai",
                        api_key=config.llm.api_key,
                        base_url=config.llm.base_url,
                        model=config.llm.model,
                        timeout=config.llm.timeout_seconds,
                    )
                elif config.llm.provider == "ollama":
                    self.provider = create_provider(
                        "ollama",
                        base_url=config.llm.base_url,
                        model=config.llm.model,
                        timeout=config.llm.timeout_seconds,
                    )
            except Exception:
                self.provider = None

    def generate_changelog(
        self,
        since_ref: str,
        to_ref: str = "HEAD",
        version: str | None = None,
        output_path: Path | None = None,
    ) -> str:
        """Generate changelog section from commits between refs."""
        commits = get_commit_history(since_ref, to_ref)

        if not commits:
            return "No commits found in the specified range."

        # Parse and group commits
        grouped_commits = self._group_commits(commits)

        # Generate raw changelog content
        changelog_content = self._generate_raw_changelog(grouped_commits, version)

        # Polish with LLM if available
        if self.provider and grouped_commits:
            try:
                changelog_content = self._polish_with_llm(changelog_content)
            except Exception:
                # Fall back to raw content on LLM failure
                pass

        # Insert into existing CHANGELOG.md if it exists
        if output_path:
            return self._insert_into_changelog(changelog_content, output_path)
        else:
            # Default to CHANGELOG.md in git root
            default_path = self.config.git_root / "CHANGELOG.md"
            return self._insert_into_changelog(changelog_content, default_path)

    def _group_commits(self, commits: list[dict[str, str]]) -> dict[str, list[str]]:
        """Group commits by type for changelog sections."""
        grouped = defaultdict(list)

        for commit in commits:
            subject = commit["subject"]
            body = commit.get("body", "")

            # Parse conventional commit format: type(scope): description
            match = re.match(r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$", subject)
            if match:
                commit_type = match.group(1)
                scope = match.group(2)
                description = match.group(3)

                # Map to changelog section
                section = TYPE_TO_SECTION.get(commit_type, "Other")

                # Include scope if present
                if scope:
                    description = f"**{scope}:** {description}"

                # Add PR/issue references from body
                pr_refs = self._extract_pr_references(body)
                if pr_refs:
                    description += f" ({pr_refs})"

                grouped[section].append(description)
            else:
                # Non-conventional commit
                grouped["Other"].append(subject)

        return dict(grouped)

    def _generate_raw_changelog(
        self, grouped_commits: dict[str, list[str]], version: str | None
    ) -> str:
        """Generate raw changelog content from grouped commits."""
        lines = []

        # Add header
        if version:
            lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}")
        else:
            lines.append(f"## {datetime.now().strftime('%Y-%m-%d')}")

        lines.append("")

        # Add sections in order
        for section in CHANGELOG_SECTIONS:
            if section in grouped_commits:
                lines.append(f"### {section}")
                lines.append("")

                for item in grouped_commits[section]:
                    # Wrap long lines
                    wrapped_item = wrap_text(item, CHANGELOG_WRAP_WIDTH)
                    lines.append(f"- {wrapped_item}")

                lines.append("")

        return "\n".join(lines)

    def _polish_with_llm(self, raw_changelog: str) -> str:
        """Polish changelog content using LLM."""
        if not self.provider:
            return raw_changelog
        lines = raw_changelog.split("\n")
        header_lines = []
        content_lines = []

        in_content = False
        for line in lines:
            if line.startswith("### "):
                in_content = True
            if in_content:
                content_lines.append(line)
            else:
                header_lines.append(line)

        if not content_lines:
            return raw_changelog

        grouped_bullets = "\n".join(content_lines)

        prompt = CHANGELOG_USER_PROMPT.format(grouped_bullets=grouped_bullets)
        if self.config.debug_settings.debug_mode:
            print("Sending changelog to LLM for polishing...")
            print(f"System: {CHANGELOG_SYSTEM_PROMPT}")
            print(f"User: {prompt}")
            print("-" * 50)

        polished_content = self.provider.generate(
            system=CHANGELOG_SYSTEM_PROMPT,
            user=prompt,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            timeout=self.config.llm.timeout_seconds,
        )
        if self.config.debug_settings.debug_mode:
            print(f"LLM polished response: {polished_content}")
            print("-" * 50)

        polished_lines = []
        for line in polished_content.split("\n"):
            line = line.strip()
            if line and not line.startswith("```"):
                if not line.startswith("- "):
                    line = f"- {line}"
                polished_lines.append(line)

        return "\n".join(header_lines) + "\n" + "\n".join(polished_lines) + "\n"

    def _insert_into_changelog(self, new_content: str, changelog_path: Path) -> str:
        """Insert new changelog content at the top of existing file."""
        if not changelog_path.exists():
            # create new changelog file
            changelog_path.write_text(new_content + "\n")
            return f"Created new changelog at {changelog_path}"

        # read existing content
        existing_content = changelog_path.read_text()

        # find the first header to insert before it
        lines = existing_content.split("\n")
        insert_index = 0

        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_index = i
                break

        # insert new content
        new_lines = new_content.split("\n")
        updated_lines = lines[:insert_index] + new_lines + [""] + lines[insert_index:]

        # write back to file
        changelog_path.write_text("\n".join(updated_lines))

        return f"Updated changelog at {changelog_path}"

    def _extract_pr_references(self, body: str) -> str:
        """Extract PR and issue references from commit body."""
        references = []

        # common patterns for PR/issue references
        patterns = [
            r"#(\d+)",
            r"\b(PR|Pull Request|Issue|Fixes|Closes)\s*#?(\d+)\b",
            r"\bGH-(\d+)\b",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # for patterns with capture groups
                    ref_num = match[1] if len(match) > 1 else match[0]
                    references.append(f"#{ref_num}")
                else:
                    references.append(f"#{match}")

        # remove duplicates and return
        def extract_number(ref: str) -> int:
            match = re.match(r"#(\d+)", ref)
            return int(match.group(1)) if match else 0

        return ", ".join(sorted(set(references), key=extract_number))
