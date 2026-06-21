"""Gate 4: routing + cost record correctness (no escalation)."""

from __future__ import annotations

import pytest

from costrouter.config import default_config
from costrouter.providers.mock import MockProvider
from costrouter.router import Router


@pytest.mark.asyncio
async def test_trivial_routes_to_cheap():
    router = Router(default_config(), MockProvider())
    _, record = await router.route("hi")
    assert record.decision.level == "trivial"
    assert record.decision.chosen_tier == "cheap"
    assert not record.decision.escalated


@pytest.mark.asyncio
async def test_hard_routes_to_mid():
    router = Router(default_config(), MockProvider())
    _, record = await router.route("Explain why the sky is blue in detail.")
    assert record.decision.level == "hard"
    assert record.decision.chosen_tier == "mid"


@pytest.mark.asyncio
async def test_cost_record_savings_positive_for_cheap():
    router = Router(default_config(), MockProvider())
    _, record = await router.route("hi")
    assert record.actual_cost < record.baseline_cost
    assert record.savings_pct > 0
    assert record.saved == pytest.approx(record.baseline_cost - record.actual_cost)
