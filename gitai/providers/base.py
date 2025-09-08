"""Base protocol for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from ..config import Config


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    @abstractmethod
    def generate(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> str:
        """Generate text using the LLM provider.

        Args:
            system: System prompt
            user: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            config: Configuration object
        Returns:
            Generated text

        Raises:
            Exception: If generation fails
        """


class BaseProvider(ABC):
    """Base class for LLM providers with common functionality."""

    def __init__(self, timeout: int = 60, config: Config = Config.load()):
        self.timeout = timeout
        self.debug_mode = config.debug_settings.debug_mode

    @abstractmethod
    def generate(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> str:
        """Generate text using the LLM provider."""
        pass


def create_provider(provider_name: str, **kwargs: Any) -> LLMProvider:
    """Factory function to create LLM providers."""
    if provider_name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)
    elif provider_name == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
