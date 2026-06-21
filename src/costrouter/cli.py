"""Typer CLI: route / bench / serve."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from costrouter.config import RouterConfig, default_config
from costrouter.providers.mock import MockProvider
from costrouter.router import Router
from costrouter.telemetry import Telemetry

app = typer.Typer(add_completion=False, help="Route LLM requests to the cheapest capable model.")
console = Console()


@app.callback()
def _configure() -> None:
    logger.remove()
    logger.add(sys.stderr, level=os.environ.get("COSTROUTER_LOG_LEVEL", "WARNING"))


def _build_router(config_path: str | None, provider_name: str) -> Router:
    config = RouterConfig.load(config_path) if config_path else default_config()
    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "anthropic":
        from costrouter.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
    elif provider_name == "openai":
        from costrouter.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
    else:
        raise typer.BadParameter(f"unknown provider: {provider_name}")
    return Router(config, provider)


@app.command()
def route(
    prompt: str = typer.Option(..., "--prompt"),
    config: str = typer.Option(None, "--config"),
    provider: str = typer.Option("mock", "--provider", help="mock|anthropic|openai"),
) -> None:
    """Route a single prompt; print the decision and cost."""
    router = _build_router(config, provider)
    completion, record = asyncio.run(router.route(prompt))
    d = record.decision
    console.print(f"[bold]Level:[/bold] {d.level}  [bold]Tier:[/bold] {d.chosen_tier}"
                  f"  [bold]Escalated:[/bold] {d.escalated}")
    console.print(f"[bold]Model:[/bold] {record.usage.model}")
    console.print(f"[bold]Actual:[/bold] ${record.actual_cost:.6f}  "
                  f"[bold]Baseline:[/bold] ${record.baseline_cost:.6f}  "
                  f"[bold green]Savings:[/bold green] {record.savings_pct:.1f}%")
    console.print(f"[dim]{completion.text}[/dim]")


@app.command()
def bench(
    file: str = typer.Option(..., "--file", help="JSONL with one {\"prompt\": ...} per line"),
    config: str = typer.Option(None, "--config"),
    provider: str = typer.Option("mock", "--provider"),
) -> None:
    """Route a batch workload and print a savings report."""
    router = _build_router(config, provider)
    telemetry = Telemetry()
    lines = Path(file).read_text(encoding="utf-8").strip().splitlines()

    async def _run() -> None:
        for line in lines:
            prompt = json.loads(line)["prompt"]
            _, record = await router.route(prompt)
            telemetry.add(record)

    asyncio.run(_run())
    rep = telemetry.report()
    table = Table(title="Cost Router — Savings Report", header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Requests", str(rep.requests))
    table.add_row("Actual spend", f"${rep.total_actual_cost:.4f}")
    table.add_row("Baseline spend", f"${rep.total_baseline_cost:.4f}")
    table.add_row("Saved", f"${rep.total_saved:.4f}")
    table.add_row("Savings", f"[bold green]{rep.savings_pct:.1f}%[/bold green]")
    table.add_row("Escalations", str(rep.escalations))
    dist = ", ".join(f"{k}={v}" for k, v in rep.tier_distribution.items())
    table.add_row("Tier distribution", dist)
    console.print(table)


@app.command()
def serve(
    port: int = typer.Option(8000, "--port"),
    config: str = typer.Option(None, "--config"),
    provider: str = typer.Option("anthropic", "--provider"),
) -> None:  # pragma: no cover - server entrypoint
    """Run the OpenAI-compatible routing proxy."""
    import uvicorn

    from costrouter.server import create_app

    router = _build_router(config, provider)
    uvicorn.run(create_app(router), host="0.0.0.0", port=port)


if __name__ == "__main__":
    app()
