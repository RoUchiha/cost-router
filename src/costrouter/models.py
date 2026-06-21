"""Pydantic v2 models for routing, usage, and cost accounting."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["trivial", "simple", "hard"]

# Ordered capability ladder. A tier can satisfy any level <= its capability.
LEVEL_ORDER: dict[str, int] = {"trivial": 0, "simple": 1, "hard": 2}


class ModelTier(BaseModel):
    """A routable model with its price and the hardest level it can satisfy."""

    name: str
    model: str
    price_input: float = Field(description="USD per 1M input tokens")
    price_output: float = Field(description="USD per 1M output tokens")
    capability: Level = "hard"


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class Completion(BaseModel):
    """A provider's response plus the usage it incurred."""

    text: str
    usage: Usage


class RoutingDecision(BaseModel):
    level: Level
    chosen_tier: str
    reason: str
    escalated: bool = False


class CostRecord(BaseModel):
    request_id: str
    usage: Usage
    actual_cost: float
    baseline_cost: float
    savings_pct: float
    decision: RoutingDecision

    @property
    def saved(self) -> float:
        return self.baseline_cost - self.actual_cost
