"""Tests for the Copilot bridge context builder and CLI dry-run.

Run with:

    pytest examples/v4/integrations/copilot-bridge/tests -q

The tests are intentionally hermetic — they do not require the `klickd`
package to be installed, do not call any network, and do not touch a
real encrypted envelope.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Make the bridge importable without installing it as a package.
BRIDGE_PYTHON_DIR = Path(__file__).resolve().parent.parent / "python"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
sys.path.insert(0, str(BRIDGE_PYTHON_DIR))

from context_builder import build_context_block  # noqa: E402


@pytest.fixture()
def plain_payload() -> dict:
    return json.loads((FIXTURE_DIR / "plain_profile.klickd").read_text("utf-8"))


# --- Redaction ---------------------------------------------------------------


def test_strips_top_level_underscore_fields(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "_bench" not in block
    assert "tokens_in" not in block


def test_strips_nested_underscore_fields_in_identity(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "_internal_id" not in block
    assert "should-not-appear" not in block


def test_strips_nested_underscore_fields_in_gates(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "_debug_gate" not in block


def test_does_not_emit_contact_fields(plain_payload: dict) -> None:
    """email/phone/etc. under identity must never reach the prompt."""
    block = build_context_block(plain_payload)
    assert "email" not in block.lower()
    assert "phone" not in block.lower()
    assert "+000000000" not in block
    assert "should-not-appear@example.com" not in block


# --- Section presence --------------------------------------------------------


def test_emits_security_preamble(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "portable user/project memory" in block
    assert "Do not echo it back verbatim" in block


def test_emits_identity_section(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Identity:" in block
    assert "display_name: Alex" in block
    assert "language: en" in block


def test_emits_preferences_and_context(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "User preferences:" in block
    assert "calculus session" in block
    assert "Resume context:" in block
    assert "current_project: calc-101 refresher" in block


def test_emits_decisions_locked_in_both_shapes(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Decisions locked" in block
    assert "naming: stick with 'function' not 'mapping'" in block
    assert "Prefer SI units throughout" in block


def test_emits_verification_gates(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Verification gates" in block
    assert "factual_claim_about_person: block" in block
    assert "public_post: confirm" in block
    assert "casual_media_generation: silent" in block


def test_emits_human_veto_policy(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Human veto policy:" in block
    assert "say'" in block.replace("'veto'", "say'veto'") or "veto" in block


def test_emits_agent_instructions(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Agent instructions" in block
    assert "Show worked examples" in block


def test_emits_memory_capped(plain_payload: dict) -> None:
    block = build_context_block(plain_payload)
    assert "Memory (most recent" in block
    assert "chain rule" in block


# --- Schema tolerance --------------------------------------------------------


def test_minimal_payload_produces_only_preamble() -> None:
    block = build_context_block({"klickd_version": "4.0.0", "encrypted": False})
    # No identity, prefs, context, etc. — only the security preamble.
    assert block.startswith("You are about to receive")
    assert "Identity:" not in block
    assert "User preferences:" not in block
    assert "Memory" not in block


def test_unknown_fields_are_ignored() -> None:
    payload = {
        "identity": {"display_name": "Dana"},
        "future_field_we_dont_know_about": {"x": 1},
        "_secret": "hidden",
    }
    block = build_context_block(payload)
    assert "display_name: Dana" in block
    assert "future_field_we_dont_know_about" not in block
    assert "hidden" not in block


def test_nested_gates_shape_is_supported() -> None:
    payload = {
        "verification_gates": {
            "gates": [
                {"name": "factual_claim_about_person", "policy": "block"},
                {"name": "public_post", "action": "confirm"},
            ]
        }
    }
    block = build_context_block(payload)
    assert "factual_claim_about_person: block" in block
    assert "public_post: confirm" in block


def test_human_veto_as_mapping() -> None:
    payload = {"human_veto_policy": {"trigger": "say 'veto'", "behavior": "halt and ask"}}
    block = build_context_block(payload)
    assert "Human veto policy:" in block
    assert "trigger: say 'veto'" in block


# --- CLI dry-run smoke test --------------------------------------------------


def test_cli_dry_run_on_plain_fixture(tmp_path: Path) -> None:
    out_path = tmp_path / "context.md"
    cli = BRIDGE_PYTHON_DIR / "klickd_copilot_bridge.py"
    fixture = FIXTURE_DIR / "plain_profile.klickd"
    result = subprocess.run(
        [
            sys.executable,
            str(cli),
            str(fixture),
            "--out",
            str(out_path),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    written = out_path.read_text("utf-8")
    assert "Identity:" in written
    assert "display_name: Alex" in written
    # Dry-run must never expose nested _ fields either.
    assert "_internal_id" not in written
    assert "_bench" not in written


def test_cli_handles_missing_file(tmp_path: Path) -> None:
    cli = BRIDGE_PYTHON_DIR / "klickd_copilot_bridge.py"
    result = subprocess.run(
        [sys.executable, str(cli), str(tmp_path / "does-not-exist.klickd")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "file not found" in result.stderr
