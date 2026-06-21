"""Gate 5: verify + single-escalation behavior."""

from __future__ import annotations

import pytest

from costrouter.config import default_config
from costrouter.providers.mock import MockProvider
from costrouter.router import Router


@pytest.mark.asyncio
async def test_low_quality_triggers_single_escalation():
    cfg = default_config()  # verify=True, max_escalations=1, hard->mid, escalate->frontier
    cheap_model = cfg.tier_by_name("cheap").model
    provider = MockProvider(low_quality_models=[cheap_model])
    router = Router(cfg, provider)

    _, record = await router.route("hi")  # trivial -> cheap (low quality) -> escalate
    assert record.decision.escalated is True
    assert record.decision.chosen_tier == "frontier"
    # exactly two provider calls: cheap, then frontier
    assert len(provider.calls) == 2
    assert provider.calls[0][0] == cheap_model


@pytest.mark.asyncio
async def test_max_escalations_respected():
    cfg = default_config()
    # Make BOTH cheap and the escalation target low quality -> still only 1 escalation.
    provider = MockProvider(low_quality_models=[
        cfg.tier_by_name("cheap").model,
        cfg.tier_by_name("frontier").model,
    ])
    router = Router(cfg, provider)
    _, record = await router.route("hi")
    assert record.decision.escalated is True
    assert len(provider.calls) == 2  # initial + exactly one escalation


@pytest.mark.asyncio
async def test_no_escalation_when_quality_ok():
    provider = MockProvider()
    router = Router(default_config(), provider)
    _, record = await router.route("hi")
    assert record.decision.escalated is False
    assert len(provider.calls) == 1
