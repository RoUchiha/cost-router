"""Provider abstraction: real SDKs are import-safe; MockProvider runs offline."""

from costrouter.providers.mock import MockProvider

__all__ = ["MockProvider"]
