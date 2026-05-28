"""Provider adapters for v4.1 benchmark execution.

All adapters conform to the :class:`base.LLMProvider` protocol. The runner
selects a provider by name; tests use the in-process mock provider so no
network calls are ever issued from CI.
"""
from __future__ import annotations

from .base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderResponse,
    TransientProviderError,
    get_provider,
    is_transient_error,
    register_provider,
)
from .mock_provider import MockProvider

__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderResponse",
    "TransientProviderError",
    "MockProvider",
    "get_provider",
    "is_transient_error",
    "register_provider",
]
