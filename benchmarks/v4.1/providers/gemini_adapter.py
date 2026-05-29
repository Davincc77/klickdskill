"""Gemini provider adapter for v4.1 pilots.

- Reads the API key from ``GEMINI_API_KEY`` or the generic ``LLM_API_KEY``.
- Default model: ``gemini-2.5-flash``. Configurable via :class:`ProviderConfig`.
- The ``google-genai`` SDK is imported lazily so unit tests (which use the
  mock provider) never require it to be installed.
- The adapter never logs the API key and never echoes the key into a
  response or manifest. Logging of full prompts/outputs is the runner's
  responsibility, not the adapter's.

NOTE: tests in this PR mock this provider; CI never makes a real call.
"""
from __future__ import annotations

import time
from typing import Any

from .base import (
    ProviderConfig,
    ProviderError,
    ProviderResponse,
    TransientProviderError,
    env_api_key,
    is_transient_error,
)

DEFAULT_MODEL = "gemini-2.5-flash"
_ENV_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "LLM_API_KEY")


class GeminiProvider:
    name = "gemini"

    def __init__(self, *, api_key: str | None = None) -> None:
        key = api_key or env_api_key(*_ENV_KEYS)
        if not key:
            raise ProviderError(
                "Gemini provider requires an API key in one of: "
                + ", ".join(_ENV_KEYS)
            )
        self._api_key = key
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from google import genai  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - SDK absent in tests
            raise ProviderError(
                "google-genai SDK not installed. Install with `pip install google-genai`."
            ) from exc
        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate(self, system: str, user: str, config: ProviderConfig) -> ProviderResponse:
        client = self._ensure_client()
        gen_config: dict[str, Any] = {
            "temperature": config.temperature,
            "max_output_tokens": config.max_output_tokens,
            "top_p": config.top_p,
        }
        # Per-request timeout: google-genai accepts HttpOptions(timeout=<ms>)
        # in the per-call config. Without this the SDK can hang indefinitely
        # on a stalled TLS read with no client-side deadline (observed on
        # bundle_index=4 of Test B where the call step ran >80 min before
        # the workflow was cancelled).
        timeout_ms = max(1000, int(config.timeout_s * 1000))
        http_options: dict[str, Any] = {"timeout": timeout_ms}
        t0 = time.monotonic()
        try:  # pragma: no cover - exercised only with real SDK/network
            resp = client.models.generate_content(
                model=config.model,
                contents=user,
                config={
                    "system_instruction": system,
                    "http_options": http_options,
                    **gen_config,
                },
            )
        except Exception as exc:
            # Surface timeouts as transient so the retry loop can recover.
            if _is_timeout_error(exc) or is_transient_error(exc):
                raise TransientProviderError(
                    f"gemini transient call failure: {exc!s}"
                ) from exc
            raise ProviderError(f"gemini call failed: {exc!s}") from exc
        latency_ms = int((time.monotonic() - t0) * 1000)
        return _normalise_response(resp, config.model, latency_ms)


def _is_timeout_error(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    if "timeout" in name:
        return True
    msg = str(exc).lower()
    return "timeout" in msg or "timed out" in msg or "deadline" in msg


def _normalise_response(resp: Any, model: str, latency_ms: int) -> ProviderResponse:  # pragma: no cover
    text = getattr(resp, "text", "") or ""
    usage = getattr(resp, "usage_metadata", None)
    input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
    output_tokens = getattr(usage, "candidates_token_count", None) if usage else None
    finish_reason = None
    candidates = getattr(resp, "candidates", None) or []
    if candidates:
        finish_reason = getattr(candidates[0], "finish_reason", None)
        if finish_reason is not None:
            finish_reason = str(finish_reason)
    return ProviderResponse(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        raw_model=model,
        finish_reason=finish_reason,
        provider_metadata={"provider": "gemini"},
    )
