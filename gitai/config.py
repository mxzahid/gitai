"""Configuration management for GitAI."""

import os
from dataclasses import dataclass
from pathlib import Path

from .util import find_git_root, load_toml_config


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 300
    temperature: float = 0.0
    timeout_seconds: int = 45
    api_key: str | None = None
    base_url: str | None = None


@dataclass
class CommitConfig:
    """Commit message generation configuration."""

    style: str = "conventional"
    scope_detection: bool = True
    include_body: bool = True
    include_footers: bool = True
    wrap_width: int = 72


@dataclass
class ChangelogConfig:
    """Changelog generation configuration."""

    grouping: str = "type"
    heading_style: str = "keep-a-changelog"


@dataclass
class DebugConfig:
    """Debug configuration."""

    debug_mode: bool = False


@dataclass
class Config:
    """Main configuration."""

    llm: LLMConfig
    commit: CommitConfig
    changelog: ChangelogConfig
    git_root: Path
    debug_settings: DebugConfig

    @classmethod
    def load(cls, git_root: Path | None = None) -> "Config":
        """Load configuration from file and environment."""
        if git_root is None:
            git_root = find_git_root()

        config_path = git_root / ".gitai.toml"
        config_data = load_toml_config(config_path)

        llm_data = config_data.get("llm", {})

        # auto-detect provider based on available environment variables
        configured_provider = llm_data.get("provider")
        if configured_provider is None:
            if os.getenv("OPENAI_API_KEY"):
                configured_provider = "openai"
            elif os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_MODEL"):
                configured_provider = "ollama"
            else:
                configured_provider = None  # fallback

        llm_config = LLMConfig(
            provider=configured_provider,
            model=llm_data.get(
                "model",
                (
                    "gpt-4o-mini"
                    if configured_provider == "openai"
                    else "qwen2.5-coder:3b"
                ),
            ),
            max_tokens=llm_data.get("max_tokens", 300),
            temperature=llm_data.get("temperature", 0.0),
            timeout_seconds=llm_data.get("timeout_seconds", 45),
            api_key=(
                os.getenv("OPENAI_API_KEY") if configured_provider == "openai" else None
            ),
            base_url=(
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                if configured_provider == "ollama"
                else None
            ),
        )

        commit_data = config_data.get("commit", {})
        commit_config = CommitConfig(
            style=commit_data.get("style", "conventional"),
            scope_detection=commit_data.get("scope_detection", True),
            include_body=commit_data.get("include_body", True),
            include_footers=commit_data.get("include_footers", True),
            wrap_width=commit_data.get("wrap_width", 72),
        )

        changelog_data = config_data.get("changelog", {})
        changelog_config = ChangelogConfig(
            grouping=changelog_data.get("grouping", "type"),
            heading_style=changelog_data.get("heading_style", "keep-a-changelog"),
        )

        debug_settings = config_data.get("debug", {})
        debug_config = DebugConfig(debug_mode=debug_settings.get("debug_mode", False))

        return cls(
            llm=llm_config,
            commit=commit_config,
            changelog=changelog_config,
            debug_settings=debug_config,
            git_root=git_root,
        )

    def is_llm_available(self) -> bool:
        """Check if LLM provider is available."""
        if self.llm.provider == "openai":
            return self.llm.api_key is not None
        elif self.llm.provider == "ollama":
            # for ollama we assume it's available if base_url is set or model is configured
            return (
                self.llm.base_url is not None or os.getenv("OLLAMA_MODEL") is not None
            )
        return False
