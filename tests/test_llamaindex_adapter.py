"""Tests for the LlamaIndex .klickd adapter (examples/v4/integrations/llamaindex).

Hermetic: requires only `klickd` (already a repo dependency). LlamaIndex is
NOT imported and no network/provider call is made. Covers three paths from
issue #104:

* load   — starter skill + persona decode via the public SDK accessors
* bridge — system prompt + chat-message bridge shape
* error  — invalid name / non-object payload / empty prompt

Run: pytest tests/test_llamaindex_adapter.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LLI_DIR = REPO_ROOT / "examples/v4/integrations/llamaindex"
PERSONA = REPO_ROOT / "examples/v4/personas/03-fullstack-developer-en.klickd"


def _import(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"could not load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def helper():
    return _import("klickd_llamaindex", LLI_DIR / "klickd_llamaindex.py")


@pytest.fixture(scope="module")
def example():
    # The example inserts its own dir on sys.path so `import klickd_llamaindex` works.
    return _import("resume_chat_example", LLI_DIR / "resume_chat_example.py")


# --- load --------------------------------------------------------------------


def test_load_starter_skill_via_sdk(helper):
    payload = helper.load_starter_skill("coding.klickd")
    assert payload["x_klickd_pack"]["pack"] == "x.klickd/coding"
    assert payload.get("encrypted") is False


def test_load_persona_path(helper):
    payload = helper.load_klickd_path(PERSONA)
    assert payload["context"]["current_project"]


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


def test_doc_records_carry_section_metadata(helper):
    payload = helper.load_klickd_path(PERSONA)
    records = helper._doc_records(payload)
    sections = {r["metadata"]["section"] for r in records}
    assert "context" in sections
    assert all(r["metadata"]["source"] == "klickd" for r in records)


def test_example_dry_run_builds_prompt(example):
    rc = example.run_check(starter=None, persona=PERSONA, user_turn="next?")
    assert rc == 0
    assert "Resume context:" in example.build_resume_prompt(starter=None, persona=PERSONA)
    assert "x.klickd/coding" in example.build_resume_prompt(starter="coding.klickd", persona=None)


# --- error -------------------------------------------------------------------


def test_load_starter_skill_rejects_bad_name(helper):
    from klickd import get_starter_skill_bytes  # noqa: F401 — ensure SDK present

    with pytest.raises(ValueError):
        helper.load_starter_skill("../etc/passwd")
    with pytest.raises(ValueError):
        helper.load_starter_skill("coding.json")


def test_load_any_rejects_non_object(helper, tmp_path):
    bad = tmp_path / "arr.klickd"
    bad.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError):
        helper.load_klickd_path(bad)


def test_example_raises_on_empty_prompt(example, monkeypatch):
    # A payload with no injectable fields must not silently produce an empty seed.
    # The example binds `load_klickd_path` into its own namespace, so patch there.
    monkeypatch.setattr(example, "load_klickd_path", lambda *a, **k: {"_only": "debug"})
    with pytest.raises(ValueError):
        example.build_resume_prompt(starter=None, persona=PERSONA)
