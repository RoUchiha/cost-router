"""Classifier protocol -> a complexity Level."""

from __future__ import annotations

from typing import Protocol

from costrouter.models import Level


class ComplexityClassifier(Protocol):
    def classify(self, prompt: str) -> Level: ...
