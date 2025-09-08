"""OpenAI-compatible LLM provider."""

import os

from openai import OpenAI
from rich.console import Console

from .base import BaseProvider

console = Console()


class OpenAIProvider(BaseProvider):
    """OpenAI-compatible LLM provider using the OpenAI Python client."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        timeout: int = 60,
    ):
        super().__init__(timeout)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.model = model
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
        )

    def generate(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> str:
        """Generate text using OpenAI API."""
        if self.debug_mode:
            print(
                f"OpenAI API Call - Model: {self.model}, Max tokens: {max_tokens}, Temp: {temperature}"
            )

        # create and start spinner
        with console.status("[bold blue]Generating with OpenAI...", spinner="dots"):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response from OpenAI API")
                content_str: str = str(content)

                if self.debug_mode:
                    print(f"OpenAI Response received ({len(content_str)} chars)")
                    print(f"Response: {content_str}")
                    print("-" * 50)

                return content_str.strip()

            except Exception as e:
                print(f"OpenAI API Error: {e}")
                raise RuntimeError(f"OpenAI API error: {e}") from e
