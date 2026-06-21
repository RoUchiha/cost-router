"""Gate 1: pricing computes correct dollars; config loads tiers."""

from __future__ import annotations

from costrouter.config import RouterConfig, default_config
from costrouter.models import Usage
from costrouter.pricing import cost_usd, estimate_tokens, tier_cost


def test_cost_usd_known_values():
    # 1M input @ $3 + 1M output @ $15 = $18
    assert cost_usd(1_000_000, 1_000_000, 3.0, 15.0) == 18.0
    # 500k input @ $0.80 = $0.40
    assert cost_usd(500_000, 0, 0.80, 4.0) == 0.40


def test_tier_cost():
    cfg = default_config()
    mid = cfg.tier_by_name("mid")
    usage = Usage(input_tokens=1_000_000, output_tokens=0, model=mid.model)
    assert tier_cost(usage, mid) == 3.0


def test_estimate_tokens_nonzero():
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("") >= 0


def test_config_load_yaml(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(
        """
tiers:
  - {name: cheap, model: haiku, price_input: 0.8, price_output: 4.0, capability: simple}
  - {name: mid, model: sonnet, price_input: 3.0, price_output: 15.0, capability: hard}
policy: {trivial: cheap, simple: cheap, hard: mid, escalate_to: mid, max_escalations: 1}
baseline_model: sonnet
""",
        encoding="utf-8",
    )
    cfg = RouterConfig.load(p)
    assert len(cfg.tiers) == 2
    assert cfg.tier_by_name("mid").price_output == 15.0
    assert cfg.policy.tier_for("hard") == "mid"
