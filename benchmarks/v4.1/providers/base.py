"""Provider adapter base types and registry.

Fairness: every adapter MUST honour the same :class:`ProviderConfig`
(model, temperature, max_output_tokens) so that Test A conditions only
differ in the supplied context, not in generation parameters.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class ProviderError(RuntimeError):
    """Raised by any adapter on a call failure.

    Adapters that can distinguish transient infrastructure failures from
    permanent ones should raise :class:`TransientProviderError` for the
    transient case so the executor only retries on conditions where a
    retry could plausibly succeed.
    """


class TransientProviderError(ProviderError):
    """Subclass marking a transient/retryable provider failure.

    Examples: HTTP 429/500/502/503/504, gRPC ``UNAVAILABLE`` /
    ``RESOURCE_EXHAUSTED``, connection resets, read timeouts.
    Auth/config/quota-exceeded-permanent errors must remain plain
    :class:`ProviderError` so the executor does not waste retries on them.
    """


# HTTP status codes and provider error tokens that should be treated as
# transient by the classifier below.
_TRANSIENT_HTTP_CODES = (408, 425, 429, 500, 502, 503, 504)
_TRANSIENT_TOKENS = (
    "unavailable",
    "resource_exhausted",
    "resource exhausted",
    "rate limit",
    "rate-limit",
    "rate_limit",
    "ratelimit",
    "deadline_exceeded",
    "deadline exceeded",
    "internal error",
    "internal server error",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "temporarily unavailable",
    "try again",
    "overloaded",
    "high demand",
    "timeout",
    "timed out",
    "connection reset",
    "connection aborted",
    "econnreset",
    "etimedout",
)


def is_transient_error(exc: BaseException) -> bool:
    """Classify an exception as transient (retryable) or not.

    Inspects:
    - ``status_code`` / ``code`` / ``http_status`` attributes if present
    - the exception's ``str()`` for known transient tokens (case-insensitive)

    This is conservative on purpose: anything that does not match a
    known transient signal is treated as non-transient so we do not
    retry auth/permission/quota-permanent errors.
    """
    for attr in ("status_code", "http_status", "status"):
        v = getattr(exc, attr, None)
        if isinstance(v, int) and v in _TRANSIENT_HTTP_CODES:
            return True
    code = getattr(exc, "code", None)
    if isinstance(code, int) and code in _TRANSIENT_HTTP_CODES:
        return True
    if isinstance(code, str) and code.lower() in {t.lower() for t in _TRANSIENT_TOKENS}:
        return True
    text = str(exc).lower()
    for code in _TRANSIENT_HTTP_CODES:
        # Match the bare status code as a token (avoid matching "500ms").
        if f" {code} " in f" {text} " or f"({code})" in text or f"http {code}" in text or f"status {code}" in text:
            return True
    for tok in _TRANSIENT_TOKENS:
        if tok in text:
            return True
    return False


@dataclass(frozen=True)
class ProviderConfig:
    """Generation parameters that must be identical across conditions.

    A run is only fair if every condition for a given (user, prompt_family)
    is generated with the same model and decoding parameters. The runner
    instantiates one ProviderConfig per pilot and reuses it for every call.
    """
    model: str
    temperature: float = 0.2
    max_output_tokens: int = 512
    top_p: float = 1.0
    timeout_s: float = 60.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "top_p": self.top_p,
            "timeout_s": self.timeout_s,
            "extra": dict(self.extra),
        }


@dataclass(frozen=True)
class ProviderResponse:
    """Normalised response shape across adapters."""
    text: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    raw_model: str
    finish_reason: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    """Minimal protocol for benchmark adapters."""
    name: str

    def generate(self, system: str, user: str, config: ProviderConfig) -> ProviderResponse:
        ...


_REGISTRY: dict[str, Callable[..., LLMProvider]] = {}


def register_provider(name: str, factory: Callable[..., LLMProvider]) -> None:
    _REGISTRY[name] = factory


def get_provider(name: str, **kwargs: Any) -> LLMProvider:
    if name not in _REGISTRY:
        available = sorted(_REGISTRY)
        raise ProviderError(
            f"Unknown provider {name!r}. Registered providers: {available}"
        )
    return _REGISTRY[name](**kwargs)


def env_api_key(*candidates: str) -> str | None:
    """Return the first non-empty env var from ``candidates``."""
    for name in candidates:
        v = os.environ.get(name)
        if v:
            return v
    return None


# Built-in registrations happen at import time of providers/__init__.py via
# the explicit imports below. Adapters are imported lazily so missing
# optional SDKs do not crash unrelated runs.
def _register_builtins() -> None:
    from .mock_provider import MockProvider
    from .gemini_adapter import GeminiProvider

    register_provider("mock", MockProvider)
    register_provider("gemini", GeminiProvider)


_register_builtins()
