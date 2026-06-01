"""Tests for the xAI/Grok .klickd adapter (examples/v4/integrations/xai_grok).

Hermetic: requires only `klickd` (already a repo dependency). The `openai`
client is NOT imported and no network / provider call is made. Covers the
three paths from issue #109:

* load   — starter skill + persona decode via the public SDK accessors
* bridge — system prompt + chat-message bridge shape
* error  — invalid name / non-object payload / empty prompt / missing key

Run::

    PYTHONPATH=packages/pypi/klickd/src pytest tests/test_xai_grok_adapter.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
XAI_DIR = REPO_ROOT / "examples/v4/integrations/xai_grok"
PERSONA = REPO_ROOT / "examples/v4/personas/05-rpg-gamer-en.klickd"


def _import(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"could not load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def helper():
    return _import("klickd_xai", XAI_DIR / "klickd_xai.py")


@pytest.fixture(scope="module")
def example():
    # The example inserts its own dir on sys.path so `import klickd_xai` works.
    return _import("xai_resume_chat_example", XAI_DIR / "resume_chat_example.py")


# --- load --------------------------------------------------------------------


def test_load_starter_skill_via_sdk(helper):
    payload = helper.load_starter_skill("coding.klickd")
    assert payload["x_klickd_pack"]["pack"] == "x.klickd/coding"
    assert payload.get("encrypted") is False


def test_load_persona_path(helper):
    payload = helper.load_klickd_path(PERSONA)
    assert payload["context"]["current_project"]


def test_load_encrypted_roundtrip(helper):
    from klickd import save_klickd

    payload = helper.load_klickd_path(PERSONA)
    blob = save_klickd(payload, "demo-passphrase-12", domain="entertainment_gaming")
    decoded = helper._load_any(blob, passphrase="demo-passphrase-12")
    assert decoded["context"]["current_project"] == payload["context"]["current_project"]


# --- bridge ------------------------------------------------------------------


def test_persona_system_prompt_resumes_context(helper):
    prompt = helper.klickd_to_system_prompt(helper.load_klickd_path(PERSONA))
    assert "Resume context:" in prompt
    assert "current_project:" in prompt


def test_starter_pack_system_prompt_surfaces_gates(helper):
    prompt = helper.klickd_to_system_prompt(helper.load_starter_skill("coding.klickd"))
    assert "x.klickd/coding" in prompt
    assert "never override 'block'" in prompt
    assert "Memory scope:" in prompt


def test_system_prompt_strips_underscore_fields(helper):
    payload = {"user_preferences": "be terse", "_benchmark": {"tokens_in": 42}}
    prompt = helper.klickd_to_system_prompt(payload)
    assert "be terse" in prompt
    assert "_benchmark" not in prompt
    assert "42" not in prompt


def test_messages_are_openai_compatible_shape(helper):
    payload = helper.load_klickd_path(PERSONA)
    messages = helper.klickd_to_messages(payload, "Let's continue.")
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "Let's continue."}
    assert all(set(m) == {"role", "content"} for m in messages)


def test_messages_omit_user_turn_when_none(helper):
    payload = helper.load_klickd_path(PERSONA)
    messages = helper.klickd_to_messages(payload)
    assert len(messages) == 1
    assert messages[0]["role"] == "system"


def test_injection_target_prepends_guard(helper):
    payload = {"injection_target": "both", "user_preferences": "be terse"}
    prompt = helper.klickd_to_system_prompt(payload)
    assert prompt.startswith("SECURITY:")


def test_example_dry_run_builds_messages(example):
    rc = example.run_check(starter=None, persona=PERSONA, user_turn="next?")
    assert rc == 0
    persona_msgs = example.build_messages(starter=None, persona=PERSONA, user_turn="next?")
    assert "Resume context:" in persona_msgs[0]["content"]
    pack_msgs = example.build_messages(starter="coding.klickd", persona=None, user_turn="next?")
    assert "x.klickd/coding" in pack_msgs[0]["content"]


# --- error -------------------------------------------------------------------


def test_load_starter_skill_rejects_bad_name(helper):
    with pytest.raises(ValueError):
        helper.load_starter_skill("../etc/passwd")
    with pytest.raises(ValueError):
        helper.load_starter_skill("coding.json")


def test_load_any_rejects_non_object(helper, tmp_path):
    bad = tmp_path / "arr.klickd"
    bad.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError):
        helper.load_klickd_path(bad)


def test_load_bad_json_raises(helper):
    with pytest.raises(Exception):
        helper._load_any(b"{ this is not json")


def test_messages_raise_on_empty_prompt(helper):
    with pytest.raises(ValueError):
        helper.klickd_to_messages({"_only": "debug"}, "hi")


def test_chat_without_api_key_raises(helper, monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        helper.chat(PERSONA, "hi", api_key=None)
