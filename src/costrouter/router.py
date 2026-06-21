"""The router: classify -> route -> call -> verify -> (escalate) -> record.

Cost accounting is honest: if an escalation happens, the actual cost includes
*both* the failed cheap call and the escalated call. The baseline (counterfactual)
is the cost of answering with the baseline model in a single call.
"""

from __future__ import annotations

import inspect
import uuid
from typing import Protocol

from loguru import logger

from costrouter.classifier.heuristic import HeuristicClassifier
from costrouter.config import RouterConfig
from costrouter.models import Completion, CostRecord, RoutingDecision
from costrouter.pricing import cost_usd, tier_cost
from costrouter.providers.base import Provider


class Verifier(Protocol):
    def verify(self, prompt: str, completion: Completion) -> float: ...


class HeuristicVerifier:
    """Cheap confidence proxy: penalize empty, refusal-y, or too-short answers."""

    _REFUSALS = (
        "i'm not sure", "i am not sure", "i don't know", "i do not know",
        "i cannot", "i can't", "as an ai",
    )

    def __init__(self, min_len: int = 15) -> None:
        self.min_len = min_len

    def verify(self, prompt: str, completion: Completion) -> float:
        text = completion.text.strip().lower()
        if not text:
            return 0.0
        if any(r in text for r in self._REFUSALS):
            return 0.3
        if len(text) < self.min_len:
            return 0.4
        return 0.9


class Router:
    def __init__(
        self,
        config: RouterConfig,
        provider: Provider,
        classifier=None,
        verifier: Verifier | None = None,
        confidence_bar: float = 0.6,
    ) -> None:
        self.config = config
        self.provider = provider
        self.classifier = classifier or HeuristicClassifier()
        self.verifier = verifier or HeuristicVerifier()
        self.confidence_bar = confidence_bar

    async def _classify(self, prompt: str):
        result = self.classifier.classify(prompt)
        if inspect.isawaitable(result):
            return await result
        return result

    async def route(
        self, prompt: str, request_id: str | None = None
    ) -> tuple[Completion, CostRecord]:
        request_id = request_id or uuid.uuid4().hex[:12]
        policy = self.config.policy

        level = await self._classify(prompt)
        tier = self.config.tier_by_name(policy.tier_for(level))
        decision = RoutingDecision(
            level=level, chosen_tier=tier.name,
            reason=f"level={level} -> tier={tier.name}",
        )

        completion = await self.provider.generate(prompt, tier.model)
        actual_cost = tier_cost(completion.usage, tier)

        escalations = 0
        if policy.verify:
            while (
                self.verifier.verify(prompt, completion) < self.confidence_bar
                and escalations < policy.max_escalations
            ):
                tier = self.config.tier_by_name(policy.escalate_to)
                logger.info("escalating request {} to {}", request_id, tier.name)
                completion = await self.provider.generate(prompt, tier.model)
                actual_cost += tier_cost(completion.usage, tier)
                escalations += 1
                decision.escalated = True
                decision.chosen_tier = tier.name
                decision.reason += f"; escalated->{tier.name} (low confidence)"

        baseline = self.config.tier_by_model(self.config.baseline_model)
        if baseline is not None:
            baseline_cost = cost_usd(
                completion.usage.input_tokens, completion.usage.output_tokens,
                baseline.price_input, baseline.price_output,
            )
        else:
            baseline_cost = actual_cost
        savings_pct = (
            100.0 * (baseline_cost - actual_cost) / baseline_cost if baseline_cost > 0 else 0.0
        )

        record = CostRecord(
            request_id=request_id,
            usage=completion.usage,
            actual_cost=actual_cost,
            baseline_cost=baseline_cost,
            savings_pct=savings_pct,
            decision=decision,
        )
        logger.debug("routed {} via {} (saved {:.1f}%)", request_id, tier.name, savings_pct)
        return completion, record
