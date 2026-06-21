"""Gate 6: telemetry on a ~100-request workload lands in the target savings band."""

from __future__ import annotations

import pytest

from costrouter.providers.mock import MockProvider
from costrouter.router import Router
from costrouter.telemetry import Telemetry
from tests.fixtures import demo_config, savings_workload

MIN_SAVINGS, MAX_SAVINGS = 40.0, 60.0


@pytest.mark.asyncio
async def test_savings_in_target_band():
    router = Router(demo_config(), MockProvider())
    tel = Telemetry()
    workload = savings_workload()
    for prompt in workload:
        _, record = await router.route(prompt)
        tel.add(record)

    rep = tel.report()
    assert rep.requests == len(workload)
    assert rep.total_actual_cost < rep.total_baseline_cost
    assert MIN_SAVINGS <= rep.savings_pct <= MAX_SAVINGS, (
        f"savings {rep.savings_pct:.1f}% outside [{MIN_SAVINGS}, {MAX_SAVINGS}]"
    )


@pytest.mark.asyncio
async def test_tier_distribution_recorded():
    router = Router(demo_config(), MockProvider())
    tel = Telemetry()
    for prompt in savings_workload():
        _, record = await router.route(prompt)
        tel.add(record)
    rep = tel.report()
    assert set(rep.tier_distribution) <= {"cheap", "mid", "frontier"}
    assert sum(rep.tier_distribution.values()) == rep.requests
