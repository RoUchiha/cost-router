"""Deterministic complexity classifier.

Signals (cheap and explainable, no model call):
  - "hard" markers: reasoning / code / math / design / multi-step language.
  - length: long prompts skew hard.
  - "trivial": very short, no hard markers, simple factual/greeting.
Everything else is "simple".
"""

from __future__ import annotations

import re

from costrouter.models import Level
from costrouter.pricing import estimate_tokens

# Phrases that signal genuine reasoning / generation difficulty.
_HARD_MARKERS = (
    "explain why", "step by step", "step-by-step", "walk me through", "analyze",
    "analyse", "compare", "trade-off", "tradeoff", "design", "architect",
    "prove", "derive", "optimize", "optimise", "refactor", "debug",
    "write a function", "write code", "implement", "algorithm", "strategy",
    "pros and cons", "in detail", "comprehensive", "summarize the following",
    "reason about", "evaluate", "critique",
)
_CODE_MARKERS = ("```", "def ", "class ", "select ", "import ", "function(", "regex", " sql")
_MATH_MARKERS = ("integral", "derivative", "equation", "solve for", "calculate the", "probability")

_GREETING = re.compile(r"^(hi|hello|hey|thanks|thank you|yo|sup)\b", re.IGNORECASE)


class HeuristicClassifier:
    def __init__(self, hard_token_threshold: int = 80, trivial_token_threshold: int = 12) -> None:
        self.hard_token_threshold = hard_token_threshold
        self.trivial_token_threshold = trivial_token_threshold

    def classify(self, prompt: str) -> Level:
        text = prompt.lower().strip()
        tokens = estimate_tokens(prompt)

        # Strong "hard" signals dominate regardless of length.
        if any(m in text for m in _HARD_MARKERS):
            return "hard"
        if any(m in text for m in _CODE_MARKERS):
            return "hard"
        if any(m in text for m in _MATH_MARKERS):
            return "hard"
        # Multiple questions / multi-part requests.
        if text.count("?") >= 2 or " and then " in text:
            return "hard"
        # Long prompts are usually non-trivial.
        if tokens > self.hard_token_threshold:
            return "hard"

        # Trivial: short greetings or tiny factual lookups.
        if _GREETING.match(text):
            return "trivial"
        if tokens <= self.trivial_token_threshold and text.count("?") <= 1:
            return "trivial"

        return "simple"
