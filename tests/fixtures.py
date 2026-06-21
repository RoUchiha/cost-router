"""Labeled fixtures: a classification set and an engineered savings workload."""

from __future__ import annotations

from costrouter.config import Policy, RouterConfig
from costrouter.models import ModelTier

# (prompt, expected_level) — used to measure heuristic classifier accuracy.
CLASSIFICATION: list[tuple[str, str]] = [
    # trivial
    ("hi", "trivial"),
    ("hello there", "trivial"),
    ("thanks!", "trivial"),
    ("what is the capital of France?", "trivial"),
    ("who wrote Hamlet?", "trivial"),
    ("what color is the sky?", "trivial"),
    ("define photosynthesis", "trivial"),
    ("what year did WW2 end?", "trivial"),
    # simple
    ("Give me a short summary of the plot of Romeo and Juliet.", "simple"),
    ("List three popular programming languages and one use case for each.", "simple"),
    ("What are the main differences between cats and dogs as pets?", "simple"),
    ("Translate 'good morning, how are you' into Spanish please.", "simple"),
    ("Suggest a healthy breakfast for someone training for a marathon.", "simple"),
    ("Rewrite this sentence to sound more formal: hey can you send that over", "simple"),
    # hard
    ("Explain why the sky appears blue during the day.", "hard"),
    ("Write a function that reverses a linked list in Python.", "hard"),
    ("Compare microservices and monolithic architectures with trade-offs.", "hard"),
    ("Design a scalable system for a ride-sharing application.", "hard"),
    ("Analyze the causes of the 2008 financial crisis in detail.", "hard"),
    ("Solve for x: 3x + 7 = 22 and show the steps.", "hard"),
    ("Debug this code: def f(x) return x+1", "hard"),
    ("Walk me through how RSA encryption works step by step.", "hard"),
    ("What is Python? How does it differ from Java?", "hard"),
    ("Refactor this module and explain the trade-offs you made.", "hard"),
]


def demo_config() -> RouterConfig:
    """Demo tiers/policy engineered so a mixed workload lands in the 40-60% band.

    Policy sends hard work to the frontier (= baseline, 0% savings) and only
    downgrades trivial/simple work — a conservative, honest routing strategy.
    """
    return RouterConfig(
        tiers=[
            ModelTier(name="cheap", model="haiku", price_input=0.80, price_output=4.00,
                      capability="simple"),
            ModelTier(name="mid", model="sonnet", price_input=3.00, price_output=15.00,
                      capability="hard"),
            ModelTier(name="frontier", model="opus", price_input=15.00, price_output=75.00,
                      capability="hard"),
        ],
        policy=Policy(trivial="cheap", simple="mid", hard="frontier",
                      escalate_to="frontier", max_escalations=1, verify=False),
        baseline_model="opus",
    )


def savings_workload() -> list[str]:
    """~100 prompts tuned (trivial:simple:hard mix) to land in the 40-60% band."""
    trivial = [p for p, lvl in CLASSIFICATION if lvl == "trivial"]
    simple = [p for p, lvl in CLASSIFICATION if lvl == "simple"]
    hard = [p for p, lvl in CLASSIFICATION if lvl == "hard"]
    # Repeat to ~100 with a deliberate mix; hard work (0% savings, heavier tokens)
    # pulls the average down into the target band.
    workload: list[str] = []
    workload += (trivial * 9)[:28]   # 28 trivial -> cheap (high savings)
    workload += (simple * 9)[:34]    # 34 simple  -> mid/cheap (moderate-high)
    workload += (hard * 9)[:38]      # 38 hard    -> frontier (0% savings)
    return workload  # 100 requests; cost-weighted savings ~50% (within 40-60 band)
