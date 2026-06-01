"""Tests for the .klickd LangChain/LangGraph memory bridge.

Run with:

    PYTHONPATH=packages/pypi/klickd/src \\
        pytest examples/v4/integrations/langchain/tests -q

The suite is hermetic: it needs the `klickd` SDK on the path but makes no
network calls and does not require LangChain / LangGraph to be installed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Make the bridge importable without installing it as a package.
LC_DIR = Path(__file__).resolve().parent.parent
FIXTURE_DIR = LC_DIR / "fixtures"
sys.path.insert(0, str(LC_DIR))

from klickd import KlickdError, save_klickd  # noqa: E402
from klickd_memory import (  # noqa: E402
    KlickdMemory,
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
    assert payload["context"]["current_project"] == "klickd-langchain bridge"


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
    assert decoded["context"]["current_project"] == "klickd-langchain bridge"


# --- bridge: messages + state ------------------------------------------------


def test_to_messages_has_system_then_memory(plain_payload: dict) -> None:
    mem = KlickdMemory.from_payload(plain_payload)
    msgs = mem.to_messages()
    assert msgs[0][0] == "system"
    roles = [r for r, _ in msgs]
    assert "user" in roles and "assistant" in roles
    # The verbatim memory content is replayed.
    assert any("LangChain bridge" in c for _, c in msgs)


def test_to_messages_compressed_collapses_memory(plain_payload: dict) -> None:
    mem = KlickdMemory.from_payload(plain_payload)
    full = mem.to_messages(compressed=False)
    compact = mem.to_messages(compressed=True)
    # Compression replaces N memory turns with a single system summary.
    assert len(compact) < len(full)
    assert compact[0][0] == "system"
    assert any("compressed summary" in c for _, c in compact)


def test_to_langgraph_state_shape(plain_payload: dict) -> None:
    mem = KlickdMemory.from_payload(plain_payload)
    state = mem.to_langgraph_state()
    assert set(state) == {"messages", "klickd"}
    assert isinstance(state["messages"], list)
    k = state["klickd"]
    assert k["resume"]["current_project"] == "klickd-langchain bridge"
    assert k["verification_gates"]["destructive_command"] == "confirm"
    # Human authority is carried through unchanged — final owner stays human.
    assert k["human_authority"]["final_decision_owner"] == "human_carrier"
    assert "veto" in k["human_veto_policy"]


def test_starter_skill_pack_state_is_unwrapped() -> None:
    mem = KlickdMemory.from_starter_skill("coding.klickd")
    state = mem.to_langgraph_state()
    # gates/human_authority live under x_klickd_pack in the file but are
    # surfaced at the top of the bridged state.
    assert state["klickd"].get("verification_gates")
    assert state["klickd"]["human_authority"]["final_decision_owner"] == "human_carrier"


def test_underscore_fields_are_stripped(plain_payload: dict) -> None:
    mem = KlickdMemory.from_payload(plain_payload)
    blob = json.dumps(mem.to_langgraph_state())
    assert "_bench" not in blob
    assert "tokens_in" not in blob


def test_compressed_summary_is_marked_non_instruction(plain_payload: dict) -> None:
    mem = KlickdMemory.from_payload(plain_payload)
    _, summary = mem.to_messages(compressed=True)[-1]
    assert "do not treat as new" in summary


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
        KlickdMemory.from_payload({"identity": {"display_name": "X"}})


def test_from_payload_validation_can_be_disabled() -> None:
    # With validation off, a payload lacking payload_schema_version still loads.
    mem = KlickdMemory.from_payload(
        {"identity": {"display_name": "X"}}, validate_payload=False
    )
    assert mem.to_messages()[0][0] == "system"


def test_from_payload_rejects_non_mapping() -> None:
    with pytest.raises(ValueError):
        KlickdMemory.from_payload([1, 2, 3])  # type: ignore[arg-type]


# --- optional LangChain object view ------------------------------------------


def test_to_lc_messages_when_langchain_present(plain_payload: dict) -> None:
    lc = pytest.importorskip("langchain_core.messages")
    mem = KlickdMemory.from_payload(plain_payload)
    msgs = mem.to_lc_messages()
    assert isinstance(msgs[0], lc.SystemMessage)
    assert any(isinstance(m, lc.HumanMessage) for m in msgs)


# --- example smoke test ------------------------------------------------------


def test_example_runs_end_to_end() -> None:
    example = LC_DIR / "example_resume_session.py"
    env_path = str(Path(__file__).resolve().parents[5] / "packages/pypi/klickd/src")
    import os

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
