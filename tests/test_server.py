"""Gate 7: the FastAPI proxy returns a well-formed completion + routing headers.

The provider is mocked directly (MockProvider), so no live HTTP is needed; this
is the offline equivalent of a respx-mocked integration test.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from costrouter.config import default_config
from costrouter.providers.mock import MockProvider
from costrouter.router import Router
from costrouter.server import create_app


def _client() -> TestClient:
    router = Router(default_config(), MockProvider())
    return TestClient(create_app(router))


def test_health():
    assert _client().get("/health").json() == {"status": "ok"}


def test_chat_completion_shape_and_headers():
    client = _client()
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["usage"]["total_tokens"] > 0
    # Routing headers present.
    assert resp.headers["x-router-tier"] == "cheap"  # "hi" is trivial
    assert "x-router-savings" in resp.headers
    assert resp.headers["x-router-level"] == "trivial"


def test_chat_completion_hard_routes_to_mid():
    client = _client()
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Explain why the sky is blue in detail."}]},
    )
    assert resp.headers["x-router-tier"] == "mid"
