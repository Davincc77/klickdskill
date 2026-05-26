"""Test wrapper for RFC-009 Chimera Draft scaffold checks.

Invokes docs/rfcs/chimera/tests/check_chimera.py and exposes one pytest test
per check, so reviewers running `pytest tests/` see the eight RFC-009
sub-checks individually rather than as a single subprocess result.

Skipped if jsonschema>=4.18 is not available.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = REPO_ROOT / "docs" / "rfcs" / "chimera" / "tests" / "check_chimera.py"


def _import_check_module():
    spec = importlib.util.spec_from_file_location("rfc009_check_chimera", CHECK_SCRIPT)
    assert spec and spec.loader, f"could not load {CHECK_SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jsonschema = pytest.importorskip("jsonschema", minversion="4.18")


@pytest.fixture(scope="module")
def checks():
    return _import_check_module()


def test_rfc009_json_validity(checks):
    errs = checks.check_json_validity()
    assert not errs, errs


def test_rfc009_schema_validates_fixture(checks):
    errs = checks.check_schema_validates_fixture()
    assert not errs, errs


def test_rfc009_negative_fixtures_fail(checks):
    errs = checks.check_negative_fixtures()
    assert not errs, errs


def test_rfc009_skos_resolves_fixture_refs(checks):
    errs = checks.check_skos_resolves()
    assert not errs, errs


def test_rfc009_bundle_hash_integrity(checks):
    errs = checks.check_bundle_hashes()
    assert not errs, errs


def test_rfc009_no_pii_in_fixture(checks):
    errs = checks.check_pii_guard()
    assert not errs, errs


def test_rfc009_no_persona_as_pack_wording(checks):
    errs = checks.check_banned_wording()
    assert not errs, errs


def test_rfc009_markdown_links_resolve(checks):
    errs = checks.check_markdown_links()
    assert not errs, errs
