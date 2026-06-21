"""Gradio live demo for costrouter.

Two tabs:
  1. "Route one prompt" — see the classified complexity, chosen tier, model, and
     cost vs a frontier-only baseline.
  2. "Batch workload"  — route a mixed workload and see blended savings + tier mix.

Runs the deterministic MockProvider — no API keys. Deployable to HF Spaces.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import gradio as gr  # noqa: E402
import pandas as pd  # noqa: E402

from costrouter.config import default_config  # noqa: E402
from costrouter.providers.mock import MockProvider  # noqa: E402
from costrouter.router import Router  # noqa: E402
from costrouter.telemetry import Telemetry  # noqa: E402

ROUTER = Router(default_config(), MockProvider())

DEMO_WORKLOAD = [
    "hi", "what is the capital of France?", "who wrote Hamlet?", "define osmosis",
    "Give me a short summary of Romeo and Juliet.",
    "Translate 'good morning' into Spanish.",
    "List three uses for baking soda.",
    "Explain why the sky is blue in detail.",
    "Write a function to reverse a linked list in Python.",
    "Compare microservices and monoliths with trade-offs.",
    "Design a scalable ride-sharing backend.",
    "Analyze the causes of the 2008 financial crisis.",
]


def route_one(prompt: str) -> str:
    if not prompt.strip():
        return "Enter a prompt."
    _, rec = asyncio.run(ROUTER.route(prompt))
    d = rec.decision
    return (
        f"### Routed to **{d.chosen_tier}** ({rec.usage.model})\n"
        f"- **Complexity:** {d.level}\n"
        f"- **Escalated:** {d.escalated}\n"
        f"- **Actual cost:** ${rec.actual_cost:.6f}\n"
        f"- **Frontier-only baseline:** ${rec.baseline_cost:.6f}\n"
        f"- **Savings:** 🟢 **{rec.savings_pct:.1f}%**"
    )


def run_batch():
    tel = Telemetry()
    rows = []

    async def _go():
        for p in DEMO_WORKLOAD:
            _, rec = await ROUTER.route(p)
            tel.add(rec)
            rows.append({
                "prompt": p[:48],
                "level": rec.decision.level,
                "tier": rec.decision.chosen_tier,
                "savings %": round(rec.savings_pct, 1),
            })

    asyncio.run(_go())
    rep = tel.report()
    summary = (
        f"### Blended result over {rep.requests} requests\n"
        f"- **Actual spend:** ${rep.total_actual_cost:.4f}\n"
        f"- **Baseline (frontier-only):** ${rep.total_baseline_cost:.4f}\n"
        f"- **Total savings:** 🟢 **{rep.savings_pct:.1f}%**\n"
        f"- **Tier mix:** {rep.tier_distribution}"
    )
    return summary, pd.DataFrame(rows)


with gr.Blocks(title="LLM Cost Router", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 💸 LLM Cost Router\n"
        "Routes each request to the **cheapest model that can satisfy it** — "
        "classify complexity → route to a tier → verify → escalate only if needed. "
        "Savings are measured against a frontier-only baseline (`claude-opus-4-8`).\n\n"
        "_Offline demo: a deterministic mock provider stands in for the real models._"
    )
    with gr.Tab("Route one prompt"):
        with gr.Row():
            q = gr.Textbox(label="Prompt", placeholder="what is the capital of France?", scale=4)
            btn = gr.Button("Route", variant="primary", scale=1)
        gr.Examples(
            ["what is the capital of France?", "Explain why the sky is blue in detail.",
             "Write a function to sort a list in Python.", "hi"],
            inputs=q,
        )
        out = gr.Markdown()
        btn.click(route_one, q, out)
        q.submit(route_one, q, out)

    with gr.Tab("Batch workload"):
        gr.Markdown("Route a mixed workload (trivial → hard) and see blended savings.")
        bbtn = gr.Button("Run batch", variant="primary")
        bout = gr.Markdown()
        bdf = gr.Dataframe(label="Per-request routing")
        bbtn.click(run_batch, None, [bout, bdf])


if __name__ == "__main__":
    demo.launch()
