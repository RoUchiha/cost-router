"""OpenAI-compatible FastAPI proxy that transparently routes to the cheapest tier.

POST /v1/chat/completions returns a standard chat-completion body plus routing
headers: X-Router-Tier and X-Router-Savings.
"""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from costrouter.config import RouterConfig, default_config
from costrouter.router import Router


def _extract_prompt(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return str(m.get("content", ""))
    return ""


def create_app(router: Router) -> FastAPI:
    app = FastAPI(title="costrouter", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/v1/chat/completions")
    async def chat_completions(body: dict) -> JSONResponse:
        prompt = _extract_prompt(body.get("messages", []))
        completion, record = await router.route(prompt)
        payload = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": completion.usage.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": completion.text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": completion.usage.input_tokens,
                "completion_tokens": completion.usage.output_tokens,
                "total_tokens": completion.usage.total_tokens,
            },
        }
        headers = {
            "X-Router-Tier": record.decision.chosen_tier,
            "X-Router-Level": record.decision.level,
            "X-Router-Savings": f"{record.savings_pct:.1f}%",
            "X-Router-Escalated": str(record.decision.escalated).lower(),
        }
        return JSONResponse(content=payload, headers=headers)

    return app


def default_app(config_path: str | None = None) -> FastAPI:  # pragma: no cover - wiring
    """Build an app with the real Anthropic provider (needs ANTHROPIC_API_KEY)."""
    from costrouter.providers.anthropic import AnthropicProvider

    config = RouterConfig.load(config_path) if config_path else default_config()
    return create_app(Router(config, AnthropicProvider()))
