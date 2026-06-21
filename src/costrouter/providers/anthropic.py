"""Anthropic provider. Import-safe without the SDK or an API key — the SDK is
imported lazily inside generate()."""

from __future__ import annotations

import os

from costrouter.models import Completion, Usage


class AnthropicProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> Completion:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        from anthropic import AsyncAnthropic  # lazy import

        client = AsyncAnthropic(api_key=self.api_key)
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        usage = Usage(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=model,
        )
        return Completion(text=text, usage=usage)
