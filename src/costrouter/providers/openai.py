"""OpenAI provider. Import-safe without the SDK or an API key (lazy import)."""

from __future__ import annotations

import os

from costrouter.models import Completion, Usage


class OpenAIProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> Completion:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI  # lazy import

        client = AsyncOpenAI(api_key=self.api_key)
        resp = await client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content or ""
        usage = Usage(
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            model=model,
        )
        return Completion(text=text, usage=usage)
