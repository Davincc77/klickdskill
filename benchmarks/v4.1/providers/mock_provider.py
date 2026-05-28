"""Deterministic in-process mock provider for tests and dry-runs.

NEVER makes a network call. Used in unit tests and as the default for
``runner pilot --execute --provider mock`` so the pilot pipeline can be
exercised end-to-end without provider cost.
"""
from __future__ import annotations

import hashlib
import time

from .base import ProviderConfig, ProviderResponse


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class MockProvider:
    """Returns a deterministic synthetic completion derived from the prompt."""
    name = "mock"

    def __init__(self, *, fail_on: str | None = None, latency_ms: int = 3) -> None:
        self._fail_on = fail_on
        self._latency_ms = latency_ms

    def generate(self, system: str, user: str, config: ProviderConfig) -> ProviderResponse:
        if self._fail_on and self._fail_on in user:
            from .base import ProviderError
            raise ProviderError(f"mock failure triggered by token {self._fail_on!r}")
        t0 = time.monotonic()
        digest = hashlib.sha256((system + "\x1f" + user).encode("utf-8")).hexdigest()[:16]
        text = (
            f"[mock:{config.model}] hash={digest} "
            f"echo_len={len(user)} sys_len={len(system)}"
        )
        # Simulate small deterministic latency without sleeping in tests.
        latency_ms = self._latency_ms + int(1000 * (time.monotonic() - t0))
        return ProviderResponse(
            text=text,
            input_tokens=_approx_tokens(system) + _approx_tokens(user),
            output_tokens=_approx_tokens(text),
            latency_ms=latency_ms,
            raw_model=config.model,
            finish_reason="stop",
            provider_metadata={"provider": "mock", "deterministic": True},
        )
