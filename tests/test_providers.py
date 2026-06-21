"""Gate 2: mock returns scripted output + usage; real providers import-safe."""

from __future__ import annotations

import pytest

from costrouter.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_scripted_and_usage():
    p = MockProvider(scripted={"haiku": "scripted answer"})
    c = await p.generate("a question", "haiku")
    assert c.text == "scripted answer"
    assert c.usage.input_tokens > 0 and c.usage.output_tokens > 0
    assert ("haiku", "a question") in p.calls


@pytest.mark.asyncio
async def test_mock_low_quality():
    p = MockProvider(low_quality_models=["haiku"])
    c = await p.generate("q", "haiku")
    assert "not sure" in c.text.lower()


def test_real_providers_import_safe_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from costrouter.providers.anthropic import AnthropicProvider
    from costrouter.providers.openai import OpenAIProvider

    assert AnthropicProvider().api_key is None
    assert OpenAIProvider().api_key is None


@pytest.mark.asyncio
async def test_real_provider_errors_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from costrouter.providers.anthropic import AnthropicProvider

    with pytest.raises(RuntimeError):
        await AnthropicProvider().generate("q", "claude-haiku-4-5-20251001")
