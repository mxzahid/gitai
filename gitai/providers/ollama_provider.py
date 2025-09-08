"""Ollama local LLM provider."""

import json

import requests
from rich.console import Console

from .base import BaseProvider

console = Console()


class OllamaProvider(BaseProvider):
    """Ollama provider for local LLM models."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:3b",
        timeout: int = 60,
    ):
        super().__init__(timeout)
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> str:
        """Generate text using Ollama API."""
        # combine system and user prompts
        full_prompt = f"{system}\n\n{user}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if self.debug_mode:
            print(
                f"Ollama API Call - Model: {self.model}, URL: {self.base_url}/api/generate"
            )
            print(f"Payload: {payload}")
            print("-" * 50)

        with console.status(
            f"[bold green]Generating with Ollama... using {self.model}", spinner="dots"
        ):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()

                result = response.json()
                content = result.get("response", "").strip()

                if not content:
                    raise ValueError("Empty response from Ollama API")
                content_str: str = str(content)

                if self.debug_mode:
                    print(f"Ollama Response received ({len(content_str)} chars)")
                    print(f"Response: {content_str}")
                    print("-" * 50)

                return content_str

            except requests.exceptions.RequestException as e:
                print(f"Ollama API Error: {e}")
                raise RuntimeError(f"Ollama API error: {e}") from e
            except json.JSONDecodeError as e:
                print(f"Ollama JSON Error: {e}")
                raise RuntimeError(f"Invalid JSON response from Ollama: {e}") from e
