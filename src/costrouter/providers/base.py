"""Provider protocol. A provider turns (prompt, model) into a Completion+usage."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from costrouter.models import Completion


@runtime_checkable
class Provider(Protocol):
    async def generate(self, prompt: str, model: str, max_tokens: int = 512) -> Completion: ...
