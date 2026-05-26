"""Pytest wrapper for examples/v4/chimera-packs/ verifier.

Exposes one pytest test per offline check in scripts/verify_chimera_packs.py.
No network, no provider calls, no paid resources.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_chimera_packs.py"


def _import_verifier():
    spec = importlib.util.spec_from_file_location("verify_chimera_packs", SCRIPT_PATH)
    assert spec and spec.loader, f"could not load {SCRIPT_PATH}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def verifier():
    return _import_verifier()


def test_json_valid(verifier):
    errs = verifier.check_json_valid()
    assert not errs, errs


def test_v40_envelope(verifier):
    errs = verifier.check_v40_envelope()
    assert not errs, errs


def test_chimera_required_fields(verifier):
    errs = verifier.check_chimera_required_fields()
    assert not errs, errs


def test_no_pii(verifier):
    errs = verifier.check_no_pii()
    assert not errs, errs


def test_no_host_skill_fields(verifier):
    errs = verifier.check_no_host_skill_fields()
    assert not errs, errs


def test_no_persona_only_fields(verifier):
    errs = verifier.check_no_persona_only_fields()
    assert not errs, errs


def test_forbidden_fields_literal(verifier):
    errs = verifier.check_forbidden_fields_literal()
    assert not errs, errs


def test_hash_stable(verifier):
    errs = verifier.check_hash_stable()
    assert not errs, errs
