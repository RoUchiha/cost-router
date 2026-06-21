"""Token estimation and dollar-cost computation.

Token counting uses tiktoken's cl100k_base as a provider-agnostic estimator;
exact tokenization varies by model, so this is an estimate (documented).
"""

from __future__ import annotations

from functools import lru_cache

from costrouter.models import ModelTier, Usage


@lru_cache(maxsize=1)
def _encoder():
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:  # pragma: no cover - fallback path
        return None


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string."""
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text))
    # Fallback: ~4 chars/token heuristic.
    return max(1, len(text) // 4)


def cost_usd(
    input_tokens: int, output_tokens: int, price_input: float, price_output: float
) -> float:
    """Cost in USD given per-1M-token prices."""
    return (input_tokens / 1_000_000) * price_input + (output_tokens / 1_000_000) * price_output


def tier_cost(usage: Usage, tier: ModelTier) -> float:
    return cost_usd(usage.input_tokens, usage.output_tokens, tier.price_input, tier.price_output)
