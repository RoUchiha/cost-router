"""Shared fixtures."""

from __future__ import annotations

import pytest

from costrouter.config import default_config
from costrouter.providers.mock import MockProvider
from costrouter.router import Router


@pytest.fixture
def config():
    return default_config()


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def router(config, mock_provider):
    return Router(config, mock_provider)
