"""Gate 3: heuristic classifier meets an accuracy target on a labeled set."""

from __future__ import annotations

import pytest

from costrouter.classifier.heuristic import HeuristicClassifier
from costrouter.providers.mock import MockProvider
from tests.fixtures import CLASSIFICATION

ACCURACY_TARGET = 0.80


def test_classifier_accuracy():
    clf = HeuristicClassifier()
    correct = sum(1 for prompt, expected in CLASSIFICATION if clf.classify(prompt) == expected)
    accuracy = correct / len(CLASSIFICATION)
    assert accuracy >= ACCURACY_TARGET, f"accuracy {accuracy:.2f} < {ACCURACY_TARGET}"


def test_classifier_specific_cases():
    clf = HeuristicClassifier()
    assert clf.classify("hi") == "trivial"
    assert clf.classify("Write a function to sort a list") == "hard"
    assert clf.classify("Explain why recursion can cause stack overflow") == "hard"


@pytest.mark.asyncio
async def test_llm_classifier_parses_and_falls_back():
    from costrouter.classifier.llm_router import LLMClassifier

    good = LLMClassifier(MockProvider(scripted={"m": "hard"}), "m")
    assert await good.classify("anything") == "hard"

    # Unparseable model output -> heuristic fallback.
    bad = LLMClassifier(MockProvider(scripted={"m": "banana"}), "m")
    assert await bad.classify("hi") == "trivial"
