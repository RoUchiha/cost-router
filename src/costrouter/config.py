"""Config: model tiers, routing policy, pricing — loaded from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from costrouter.models import Level, ModelTier


class Policy(BaseModel):
    """Maps a complexity level to a tier name, plus escalation behavior."""

    trivial: str
    simple: str
    hard: str
    escalate_to: str
    max_escalations: int = 1
    verify: bool = True

    def tier_for(self, level: Level) -> str:
        return {"trivial": self.trivial, "simple": self.simple, "hard": self.hard}[level]


class RouterConfig(BaseModel):
    tiers: list[ModelTier] = Field(default_factory=list)
    policy: Policy
    baseline_model: str

    def tier_by_name(self, name: str) -> ModelTier:
        for t in self.tiers:
            if t.name == name:
                return t
        raise KeyError(f"unknown tier: {name}")

    def tier_by_model(self, model: str) -> ModelTier | None:
        for t in self.tiers:
            if t.model == model:
                return t
        return None

    @classmethod
    def load(cls, path: str | Path) -> RouterConfig:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(**data)


def default_config() -> RouterConfig:
    """A sensible default Anthropic tier ladder (haiku -> sonnet -> opus)."""
    return RouterConfig(
        tiers=[
            ModelTier(name="cheap", model="claude-haiku-4-5-20251001",
                      price_input=0.80, price_output=4.00, capability="simple"),
            ModelTier(name="mid", model="claude-sonnet-4-6",
                      price_input=3.00, price_output=15.00, capability="hard"),
            ModelTier(name="frontier", model="claude-opus-4-8",
                      price_input=15.00, price_output=75.00, capability="hard"),
        ],
        policy=Policy(trivial="cheap", simple="cheap", hard="mid",
                      escalate_to="frontier", max_escalations=1, verify=True),
        baseline_model="claude-opus-4-8",
    )
