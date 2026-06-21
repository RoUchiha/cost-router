"""Optional LLM-based classifier: ask a cheap model to label difficulty.

Mockable via the provider abstraction; falls back to heuristic on parse failure.
"""

from __future__ import annotations

from costrouter.classifier.heuristic import HeuristicClassifier
from costrouter.models import Level
from costrouter.providers.base import Provider

_PROMPT = (
    "Classify the difficulty of the user task as exactly one word: "
    "trivial, simple, or hard.\n\nTASK: {task}\n\nDifficulty:"
)
_VALID = {"trivial", "simple", "hard"}


class LLMClassifier:
    def __init__(self, provider: Provider, model: str) -> None:
        self.provider = provider
        self.model = model
        self._fallback = HeuristicClassifier()

    async def classify(self, prompt: str) -> Level:
        completion = await self.provider.generate(_PROMPT.format(task=prompt), self.model)
        word = completion.text.strip().lower().split()[0] if completion.text.strip() else ""
        if word in _VALID:
            return word  # type: ignore[return-value]
        return self._fallback.classify(prompt)
