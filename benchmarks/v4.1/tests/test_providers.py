"""Provider adapter tests.

Real network calls are forbidden: tests never instantiate Gemini with a
key and never reach the SDK import path. The mock provider is exercised
directly.
"""
from __future__ import annotations

import os

import pytest

from conftest import providers


def test_registry_lists_builtins() -> None:
    mock = providers.get_provider("mock")
    assert mock.name == "mock"
    with pytest.raises(providers.ProviderError):
        providers.get_provider("does-not-exist")


def test_mock_is_deterministic() -> None:
    p1 = providers.MockProvider()
    p2 = providers.MockProvider()
    cfg = providers.ProviderConfig(model="x", temperature=0.0, max_output_tokens=64)
    r1 = p1.generate("sys", "user prompt", cfg)
    r2 = p2.generate("sys", "user prompt", cfg)
    assert r1.text == r2.text
    assert r1.input_tokens == r2.input_tokens
    assert r1.output_tokens == r2.output_tokens
    assert r1.raw_model == "x"
    assert r1.finish_reason == "stop"


def test_mock_responds_to_config_changes() -> None:
    p = providers.MockProvider()
    cfg1 = providers.ProviderConfig(model="m1")
    cfg2 = providers.ProviderConfig(model="m2")
    r1 = p.generate("sys", "u", cfg1)
    r2 = p.generate("sys", "u", cfg2)
    assert r1.text != r2.text
    assert r1.raw_model == "m1"
    assert r2.raw_model == "m2"


def test_gemini_requires_key(monkeypatch) -> None:
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "LLM_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(providers.ProviderError, match="requires an API key"):
        providers.get_provider("gemini")


def test_gemini_never_calls_sdk_when_unconfigured(monkeypatch) -> None:
    """Even with an env key, instantiation must not import the SDK."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-tests")
    g = providers.get_provider("gemini")
    # The client is created lazily; just confirm the adapter exists and
    # that no network/SDK call has been attempted during construction.
    assert g.name == "gemini"
    assert g._client is None  # type: ignore[attr-defined]


def test_mock_failure_path() -> None:
    p = providers.MockProvider(fail_on="trigger_failure")
    cfg = providers.ProviderConfig(model="m")
    with pytest.raises(providers.ProviderError):
        p.generate("sys", "this contains trigger_failure", cfg)
