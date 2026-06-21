"""Deterministic provider for tests and the demo.

Models can be flagged "low quality" so the verifier fails them — this is how we
exercise the escalation path without a live API.
"""

from __future__ import annotations

from collections.abc import Iterable

from costrouter.models import Completion, Usage
from costrouter.pricing import estimate_tokens


class MockProvider:
    def __init__(
        self,
        scripted: dict[str, str] | None = None,
        low_quality_models: Iterable[str] | None = None,
    ) -> None:
        self.scripted = scripted or {}
        self.low_quality_models = set(low_quality_models or [])
        self.calls: list[tuple[str, str]] = []

    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> Completion:
        self.calls.append((model, prompt))
        if model in self.scripted:
            text = self.scripted[model]
        elif model in self.low_quality_models:
            text = "I'm not sure."  # short refusal -> low verifier confidence
        else:
            text = f"Here is a complete answer to: {prompt[:60]}"
        usage = Usage(
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(text),
            model=model,
        )
        return Completion(text=text, usage=usage)
