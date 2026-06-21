"""CLI smoke tests (route / bench) via Typer CliRunner, offline mock provider."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from costrouter.cli import app

runner = CliRunner()


def test_route_trivial_prints_savings():
    result = runner.invoke(app, ["route", "--prompt", "what is the capital of France?"])
    assert result.exit_code == 0
    assert "cheap" in result.stdout
    assert "Savings" in result.stdout


def test_route_hard_routes_mid():
    result = runner.invoke(
        app, ["route", "--prompt", "Explain why the sky is blue in detail and compare theories."]
    )
    assert result.exit_code == 0
    assert "mid" in result.stdout


def test_bench_reports(tmp_path):
    wl = tmp_path / "workload.jsonl"
    prompts = [
        "hi",
        "what is the capital of France?",
        "Design a scalable system and explain trade-offs.",
    ]
    wl.write_text("\n".join(json.dumps({"prompt": p}) for p in prompts), encoding="utf-8")
    result = runner.invoke(app, ["bench", "--file", str(wl)])
    assert result.exit_code == 0
    assert "Savings Report" in result.stdout
    assert "Requests" in result.stdout


def test_unknown_provider_errors():
    result = runner.invoke(app, ["route", "--prompt", "hi", "--provider", "bogus"])
    assert result.exit_code != 0
