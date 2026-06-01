"""Tests for the Mistral x .klickd context bridge.

Run with:

    PYTHONPATH=packages/pypi/klickd/src \\
        pytest examples/v4/integrations/mistral/tests -q

The suite is hermetic: it needs the `klickd` SDK on the path but makes no
network calls and does not require the `mistralai` SDK to be installed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

MISTRAL_DIR = Path(__file__).resolve().parent.parent
FIXTURE = MISTRAL_DIR / "fixtures" / "resume_session.klickd"
sys.path.insert(0, str(MISTRAL_DIR))

from klickd import save_klickd  # noqa: E402
from klickd_mistral import (  # noqa: E402
    DEFAULT_MODEL,
    klickd_to_messages,
    klickd_to_system_prompt,
    load_klickd_path,
)


@pytest.fixture()
def payload() -> dict:
    return json.loads(FIXTURE.read_text("utf-8"))


# --- load path ---------------------------------------------------------------


def test_load_plain_fixture_from_path() -> None:
    p = load_klickd_path(FIXTURE)
    assert p["encrypted"] is False
    assert p["context"]["current_project"] == "klickd-mistral bridge"


def test_load_encrypted_roundtrip() -> None:
    blob = save_klickd(
        json.loads(FIXTURE.read_text("utf-8")),
        "demo-passphrase-12",
        domain="software_engineering",
    )
    decoded = load_klickd_path(blob_to_tmp(blob), passphrase="demo-passphrase-12")
    assert decoded["context"]["current_project"] == "klickd-mistral bridge"


def blob_to_tmp(blob: bytes) -> Path:
    import tempfile

    f = tempfile.NamedTemporaryFile(suffix=".klickd", delete=False)
    f.write(blob)
    f.close()
    return Path(f.name)


# --- bridge: system prompt ---------------------------------------------------


def test_system_prompt_includes_preferences_and_context(payload: dict) -> None:
    sp = klickd_to_system_prompt(payload)
    assert "Keep answers concise" in sp
    assert "current_project: klickd-mistral bridge" in sp
    assert "Resume context:" in sp


def test_system_prompt_emits_injection_guard_when_target_both(payload: dict) -> None:
    sp = klickd_to_system_prompt(payload)
    assert sp.startswith("SECURITY:")
    assert "user content only" in sp


def test_system_prompt_omits_guard_for_system_only_target(payload: dict) -> None:
    payload["injection_target"] = "system"
    sp = klickd_to_system_prompt(payload)
    assert not sp.startswith("SECURITY:")


def test_system_prompt_strips_underscore_fields(payload: dict) -> None:
    sp = klickd_to_system_prompt(payload)
    assert "_bench" not in sp
    assert "tokens_in" not in sp


# --- bridge: messages --------------------------------------------------------


def test_messages_shape_system_then_user(payload: dict) -> None:
    msgs = klickd_to_messages(payload, "Let's continue.")
    assert msgs[0]["role"] == "system"
    assert msgs[-1] == {"role": "user", "content": "Let's continue."}
    # Default does not replay memory (compressed-by-default).
    assert [m["role"] for m in msgs] == ["system", "user"]


def test_messages_replay_memory_is_optional(payload: dict) -> None:
    msgs = klickd_to_messages(payload, "go", replay_memory=True)
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user", "assistant", "user"]
    assert any("Mistral bridge for .klickd" in m["content"] for m in msgs)


def test_messages_minimal_payload(payload: dict) -> None:
    msgs = klickd_to_messages({"payload_schema_version": "4.0.0"}, "hi")
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["content"] == "hi"


# --- error path --------------------------------------------------------------


def test_load_bad_json_raises_valueerror() -> None:
    with pytest.raises(ValueError):
        load_klickd_path(blob_to_tmp(b"{ not json"))


def test_load_non_object_json_raises_valueerror() -> None:
    with pytest.raises(ValueError):
        load_klickd_path(blob_to_tmp(b"[1, 2, 3]"))


def test_encrypted_without_passphrase_raises(payload: dict) -> None:
    from klickd import KlickdError

    blob = save_klickd(payload, "demo-passphrase-12", domain="education")
    with pytest.raises(KlickdError):
        load_klickd_path(blob_to_tmp(blob))  # no passphrase


def test_chat_without_api_key_raises(monkeypatch) -> None:
    from klickd_mistral import chat

    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    # mistralai import is lazy; missing key is checked after import, so this
    # only reaches the RuntimeError when the SDK is installed. Skip otherwise.
    pytest.importorskip("mistralai")
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        chat(FIXTURE, "hi", api_key=None)


# --- CLI dry-run smoke test --------------------------------------------------


def _run_cli(args: list[str]):
    cli = MISTRAL_DIR / "klickd_mistral_cli.py"
    import os

    env = dict(os.environ)
    repo_root = Path(__file__).resolve().parents[5]
    env["PYTHONPATH"] = (
        str(repo_root / "packages/pypi/klickd/src")
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )
    return subprocess.run(
        [sys.executable, str(cli), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_dry_run_prints_request() -> None:
    result = _run_cli([str(FIXTURE)])
    assert result.returncode == 0, result.stderr
    req = json.loads(result.stdout)
    assert req["model"] == DEFAULT_MODEL
    assert req["messages"][0]["role"] == "system"
    assert req["messages"][-1]["role"] == "user"
    # Dry-run must never leak _ fields.
    assert "_bench" not in result.stdout


def test_cli_dry_run_replay_memory_flag() -> None:
    result = _run_cli([str(FIXTURE), "--replay-memory"])
    assert result.returncode == 0, result.stderr
    req = json.loads(result.stdout)
    roles = [m["role"] for m in req["messages"]]
    assert "assistant" in roles


def test_cli_missing_file() -> None:
    result = _run_cli([str(MISTRAL_DIR / "nope.klickd")])
    assert result.returncode == 2
    assert "file not found" in result.stderr


def test_cli_live_without_sdk_reports_cleanly() -> None:
    if _mistral_installed():
        pytest.skip("mistralai installed; cannot test the missing-SDK path")
    result = _run_cli([str(FIXTURE), "--live"])
    assert result.returncode == 1
    assert "pip install mistralai" in result.stderr
    assert "Traceback" not in result.stderr


def _mistral_installed() -> bool:
    import importlib.util

    return importlib.util.find_spec("mistralai") is not None


def test_cli_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.klickd"
    bad.write_text("{ not json", encoding="utf-8")
    result = _run_cli([str(bad)])
    assert result.returncode == 1
    assert "error:" in result.stderr
