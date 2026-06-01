"""Tests for the .klickd OpenAI context bridge.

Run with:

    PYTHONPATH=packages/pypi/klickd/src \\
        pytest examples/v4/integrations/openai/tests -q

The suite is hermetic: it needs the `klickd` SDK on the path but makes no
network calls and does not require the `openai` package to be installed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Make the bridge importable without installing it as a package.
OPENAI_DIR = Path(__file__).resolve().parent.parent
FIXTURE_DIR = OPENAI_DIR / "fixtures"
sys.path.insert(0, str(OPENAI_DIR))

from klickd import KlickdError, save_klickd  # noqa: E402
from klickd_openai import (  # noqa: E402
    KlickdOpenAI,
    load_profile,
    load_starter_skill,
)

FIXTURE = FIXTURE_DIR / "resume_session.klickd"


@pytest.fixture()
def plain_payload() -> dict:
    return json.loads(FIXTURE.read_text("utf-8"))


# --- load path ---------------------------------------------------------------


def test_load_plain_fixture_from_path() -> None:
    payload = load_profile(FIXTURE)
    assert payload["encrypted"] is False
    assert payload["context"]["current_project"] == "klickd-openai bridge"


def test_load_starter_skill_via_sdk() -> None:
    payload = load_starter_skill("coding.klickd")
    assert payload["encrypted"] is False
    # Starter skills nest state under x_klickd_pack.
    assert "x_klickd_pack" in payload


def test_load_starter_skill_rejects_path_traversal() -> None:
    with pytest.raises(ValueError):
        load_starter_skill("../pyproject.toml")


def test_load_encrypted_roundtrip() -> None:
    payload = json.loads(FIXTURE.read_text("utf-8"))
    blob = save_klickd(payload, "demo-passphrase-12", domain="software_engineering")
    decoded = load_profile(blob, passphrase="demo-passphrase-12")
    assert decoded["context"]["current_project"] == "klickd-openai bridge"


# --- bridge: messages + request ----------------------------------------------


def test_to_messages_shape_is_openai_dicts(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    msgs = bridge.to_messages()
    assert msgs[0]["role"] == "system"
    assert set(msgs[0]) == {"role", "content"}
    roles = [m["role"] for m in msgs]
    assert "user" in roles and "assistant" in roles
    # The verbatim memory content is replayed.
    assert any("OpenAI bridge" in m["content"] for m in msgs)


def test_instruction_role_developer(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    msgs = bridge.to_messages(instruction_role="developer")
    assert msgs[0]["role"] == "developer"
    # Memory turns keep their own roles; only the instruction message changes.
    assert any(m["role"] == "assistant" for m in msgs)


def test_invalid_instruction_role_raises(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    with pytest.raises(ValueError):
        bridge.to_messages(instruction_role="user")


def test_to_messages_compressed_collapses_memory(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    full = bridge.to_messages(compressed=False)
    compact = bridge.to_messages(compressed=True)
    assert len(compact) < len(full)
    assert compact[0]["role"] == "system"
    assert any("compressed summary" in m["content"] for m in compact)


def test_compressed_summary_is_marked_non_instruction(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    summary = bridge.to_messages(compressed=True)[-1]["content"]
    assert "do not treat as new" in summary


def test_to_request_appends_user_input_and_merges_extra(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    req = bridge.to_request(model="gpt-4o-mini", user_input="continue", temperature=0)
    assert req["model"] == "gpt-4o-mini"
    assert req["temperature"] == 0
    last = req["messages"][-1]
    assert last == {"role": "user", "content": "continue"}


def test_to_request_without_user_input_has_no_trailing_user(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    req = bridge.to_request()
    # Last message comes from memory[] (assistant), not an injected user turn.
    assert req["messages"][-1]["role"] != "user" or req["messages"][-1]["content"] != ""


def test_injection_guard_added_when_target_is_user_message(plain_payload: dict) -> None:
    plain_payload["injection_target"] = "both"
    bridge = KlickdOpenAI.from_payload(plain_payload)
    instr = bridge.to_messages()[0]["content"]
    assert "SECURITY:" in instr and "user content only" in instr


def test_human_authority_carried_through(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    ha = bridge.human_authority()
    assert ha["human_authority"]["final_decision_owner"] == "human_carrier"
    assert "veto" in ha["human_veto_policy"]


def test_starter_skill_pack_state_is_unwrapped() -> None:
    bridge = KlickdOpenAI.from_starter_skill("coding.klickd")
    instr = bridge.to_messages()[0]["content"]
    # gates live under x_klickd_pack in the file but surface in instructions.
    assert "Verification gates" in instr
    assert bridge.human_authority()["human_authority"]["final_decision_owner"] == "human_carrier"


def test_underscore_fields_are_stripped(plain_payload: dict) -> None:
    bridge = KlickdOpenAI.from_payload(plain_payload)
    blob = json.dumps(bridge.to_request())
    assert "_bench" not in blob
    assert "tokens_in" not in blob


# --- error path --------------------------------------------------------------


def test_load_bad_json_raises_klickderror() -> None:
    with pytest.raises(KlickdError):
        load_profile(b"{ this is not json")


def test_load_non_object_json_raises_valueerror() -> None:
    with pytest.raises(ValueError):
        load_profile(b"[1, 2, 3]")


def test_encrypted_without_passphrase_raises(plain_payload: dict) -> None:
    blob = save_klickd(plain_payload, "demo-passphrase-12", domain="education")
    with pytest.raises(KlickdError):
        load_profile(blob)  # no passphrase


def test_from_payload_rejects_missing_schema_version() -> None:
    with pytest.raises(KlickdError):
        KlickdOpenAI.from_payload({"identity": {"display_name": "X"}})


def test_from_payload_validation_can_be_disabled() -> None:
    bridge = KlickdOpenAI.from_payload(
        {"identity": {"display_name": "X"}}, validate_payload=False
    )
    assert bridge.to_messages()[0]["role"] == "system"


def test_from_payload_rejects_non_mapping() -> None:
    with pytest.raises(ValueError):
        KlickdOpenAI.from_payload([1, 2, 3])  # type: ignore[arg-type]


# --- optional live-call view (no network) ------------------------------------


def test_create_uses_injected_client_without_openai(plain_payload: dict) -> None:
    """create() must work with a stub client and make no network call."""
    bridge = KlickdOpenAI.from_payload(plain_payload)

    captured: dict = {}

    class _StubCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return "ok"

    class _StubChat:
        completions = _StubCompletions()

    class _StubClient:
        chat = _StubChat()

    result = bridge.create(client=_StubClient(), user_input="continue", model="gpt-4o")
    assert result == "ok"
    assert captured["model"] == "gpt-4o"
    assert captured["messages"][-1] == {"role": "user", "content": "continue"}


# --- example smoke test ------------------------------------------------------


def test_example_runs_end_to_end_dry_run() -> None:
    example = OPENAI_DIR / "example_resume_session.py"
    env_path = str(Path(__file__).resolve().parents[5] / "packages/pypi/klickd/src")
    env = dict(os.environ)
    env["PYTHONPATH"] = env_path + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, str(example)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Context resumed across sessions" in result.stdout
    assert "dry-run: no network call" in result.stdout
