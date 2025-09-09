"""Commit message generation functionality."""

import re
from pathlib import Path

from rich.console import Console

from .config import Config
from .constants import (
    BODY_WRAP_WIDTH,
    COMMIT_SYSTEM_PROMPT,
    COMMIT_USER_PROMPT_MERGE,
    COMMIT_USER_PROMPT_SINGLE,
    MAX_SUBJECT_LENGTH,
    TYPE_HINTS_CONTENT,
    TYPE_HINTS_PATH,
)
from .diff import StagedDiff
from .providers.base import create_provider
from .util import extract_scope_from_path, truncate_subject, wrap_text

console = Console()


class CommitGenerator:
    """Generates commit messages from staged diffs."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = None

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

    def generate_commit_message(
        self,
        diff: StagedDiff,
        hook_path: Path | None = None,
        dry_run: bool = False,
        no_body: bool = False,
        style: str | None = None,
    ) -> str:
        """Generate a commit message from staged diff."""
        if diff.is_empty():
            return "No staged changes"

        commit_style = style or self.config.commit.style

        if commit_style == "plain":
            return self._generate_plain_message(diff)

        if self.provider:
            try:
                return self._generate_with_llm(diff, no_body)
            except Exception:
                pass

        return self._generate_with_heuristics(diff, no_body)

    def _generate_with_llm(self, diff: StagedDiff, no_body: bool) -> str:
        """Generate commit message using LLM."""
        if not self.provider:
            raise RuntimeError("No LLM provider available")

        with console.status("[bold yellow]Analyzing staged changes...", spinner="dots"):
            chunks = diff.chunk_by_files()

        if len(chunks) == 1:
            # single chunk so do direct generation
            prompt = COMMIT_USER_PROMPT_SINGLE.format(diff=chunks[0].content)
            if self.config.debug_settings.debug_mode:
                print("Sending to LLM (single chunk):")
                print(f"System: {COMMIT_SYSTEM_PROMPT}")
                print(f"User: {prompt}")
                print("-" * 50)
            response = self.provider.generate(
                system=COMMIT_SYSTEM_PROMPT,
                user=prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                timeout=self.config.llm.timeout_seconds,
            )
            if self.config.debug_settings.debug_mode:
                print(f"LLM Response: {response}")
                print("-" * 50)
        else:
            # multiple chunks so summarize each first, then merge
            if self.config.debug_settings.debug_mode:
                print(f"Processing {len(chunks)} chunks:")
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                if i >= 5:  # Limit to first 5 chunks to avoid token limits
                    break

                chunk_prompt = COMMIT_USER_PROMPT_SINGLE.format(diff=chunk.content)
                if self.config.debug_settings.debug_mode:
                    print(f"Chunk {i + 1} prompt: {chunk_prompt[:200]}...")
                summary = self.provider.generate(
                    system=COMMIT_SYSTEM_PROMPT,
                    user=chunk_prompt,
                    max_tokens=150,  # Shorter for summaries
                    temperature=self.config.llm.temperature,
                    timeout=self.config.llm.timeout_seconds,
                )
                if self.config.debug_settings.debug_mode:
                    print(f"Chunk {i + 1} summary: {summary}")
                chunk_summaries.append(f"- {summary}")

            merge_prompt = COMMIT_USER_PROMPT_MERGE.format(
                chunk_summaries="\n".join(chunk_summaries)
            )
            if self.config.debug_settings.debug_mode:
                print("Sending merge prompt to LLM:")
                print(f"System: {COMMIT_SYSTEM_PROMPT}")
                print(f"User: {merge_prompt}")
                print("-" * 50)
            response = self.provider.generate(
                system=COMMIT_SYSTEM_PROMPT,
                user=merge_prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                timeout=self.config.llm.timeout_seconds,
            )
            if self.config.debug_settings.debug_mode:
                print(f"LLM Response: {response}")
                print("-" * 50)

        return self._clean_and_format_response(response, no_body)

    def _generate_with_heuristics(self, diff: StagedDiff, no_body: bool) -> str:
        """Generate commit message using heuristics."""
        commit_type = self._infer_commit_type(diff)
        scope = self._infer_scope(diff)
        subject = self._generate_subject(diff, commit_type, scope)

        if no_body or not self.config.commit.include_body:
            return subject

        body = self._generate_body(diff)
        if body:
            return f"{subject}\n\n{body}"

        return subject

    def _generate_plain_message(self, diff: StagedDiff) -> str:
        """Generate plain commit message."""
        if len(diff.files) == 1:
            action = self._infer_action_from_diff(diff.raw_diff)
            filename = Path(diff.files[0]).name
            return f"{action} {filename}"
        else:
            action = self._infer_action_from_diff(diff.raw_diff)
            return f"{action} {len(diff.files)} files"

    def _infer_commit_type(self, diff: StagedDiff) -> str:
        """Infer conventional commit type from diff."""
        # check file paths first
        for file_path in diff.files:
            for pattern, commit_type in TYPE_HINTS_PATH.items():
                if pattern in file_path:
                    return commit_type

        # check content hints
        content_hints = []
        for line in diff.raw_diff.split("\n"):
            line_lower = line.lower()
            for hint, commit_type in TYPE_HINTS_CONTENT.items():
                if hint in line_lower:
                    content_hints.append(commit_type)

        # return most common hint, default to 'feat'
        if content_hints:
            return max(set(content_hints), key=content_hints.count)

        # default based on diff stats
        if diff.stats["new_files"] > 0:
            return "feat"
        elif diff.stats["deletions"] > diff.stats["additions"]:
            return "fix"
        else:
            return "feat"

    def _infer_scope(self, diff: StagedDiff) -> str | None:
        """Infer scope from diff files."""
        if not self.config.commit.scope_detection:
            return None

        scopes = []
        for file_path in diff.files:
            scope = extract_scope_from_path(file_path)
            if scope:
                scopes.append(scope)

        if not scopes:
            return None

        # return most common scope
        return max(set(scopes), key=scopes.count)

    def _generate_subject(
        self, diff: StagedDiff, commit_type: str, scope: str | None
    ) -> str:
        """Generate commit subject line."""
        # build type(scope) prefix
        prefix = commit_type
        if scope:
            prefix = f"{commit_type}({scope})"

        # generate description based on files and changes
        if len(diff.files) == 1:
            action = self._infer_action_from_diff(diff.raw_diff)
            filename = Path(diff.files[0]).name
            description = f"{action} {filename}"
        else:
            action = self._infer_action_from_diff(diff.raw_diff)
            description = f"{action} {len(diff.files)} files"

        subject = f"{prefix}: {description}"
        return truncate_subject(subject, MAX_SUBJECT_LENGTH)

    def _generate_body(self, diff: StagedDiff) -> str:
        """Generate commit body with bullet points."""
        bullets = []

        # add file changes
        if len(diff.files) <= 5:
            for file_path in diff.files:
                action = self._infer_action_from_file(file_path, diff.raw_diff)
                bullets.append(f"- {action} {file_path}")
        else:
            # group by directory for many files
            dirs: dict[str, list[str]] = {}
            for file_path in diff.files:
                dir_name = str(Path(file_path).parent)
                if dir_name not in dirs:
                    dirs[dir_name] = []
                dirs[dir_name].append(file_path)

            for dir_name, files in dirs.items():
                if len(files) == 1:
                    action = self._infer_action_from_file(files[0], diff.raw_diff)
                    bullets.append(f"- {action} {files[0]}")
                else:
                    bullets.append(f"- update {len(files)} files in {dir_name}")

        # add stats if significant
        if diff.stats["additions"] > 10 or diff.stats["deletions"] > 10:
            bullets.append(
                f"- {diff.stats['additions']} additions, {diff.stats['deletions']} deletions"
            )

        return "\n".join(bullets)

    def _infer_action_from_diff(self, diff_content: str) -> str:
        """Infer action verb from diff content."""
        actions = []
        lines = diff_content.split("\n")

        for line in lines:
            line_lower = line.lower()
            if line.startswith("+++ b/") and "(new file)" in line:
                actions.append("add")
            elif "rename" in line_lower:
                actions.append("rename")
            elif line.startswith("+") and not line.startswith("+++"):
                actions.append("add")
            elif line.startswith("-") and not line.startswith("---"):
                actions.append("update")

        if actions:
            return max(set(actions), key=actions.count)

        return "update"

    def _infer_action_from_file(self, file_path: str, diff_content: str) -> str:
        """Infer action for a specific file."""
        # check if file is new
        if f"+++ b/{file_path}" in diff_content and "(new file)" in diff_content:
            return "add"

        # check for renames
        if "rename" in diff_content and file_path in diff_content:
            return "rename"

        return "update"

    def _clean_and_format_response(self, response: str, no_body: bool) -> str:
        """Clean and format LLM response."""
        # remove code fences if present
        response = re.sub(r"```.*?\n?", "", response)
        response = response.strip()

        # split into subject and body
        lines = response.split("\n")
        subject = lines[0].strip()

        # ensure subject follows conventional format
        if ":" not in subject:
            # try to add type if missing
            subject = f"feat: {subject}"

        # truncate subject if too long
        subject = truncate_subject(subject, MAX_SUBJECT_LENGTH)

        if no_body or len(lines) == 1:
            return subject

        # format body
        body_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line:
                # wrap long lines
                if len(line) > BODY_WRAP_WIDTH:
                    line = wrap_text(line, BODY_WRAP_WIDTH)
                body_lines.append(line)

        if body_lines:
            return f"{subject}\n\n" + "\n".join(body_lines)

        return subject
