"""The harness must never assert Mem0 compatibility."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pytest

from conftest import generator, runner


def test_planned_manifest_disclaims_mem0(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "fxt"
    generator.generate(seed=4242, n_users=3, sessions_per_user=4, out_dir=out)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    runner.cmd_dry_run(argparse.Namespace(fixtures=out))
    plan = next((tmp_path / "results").rglob("planned_run.json"))
    payload = json.loads(plan.read_text())
    assert payload["mem0"]["compatibility_claim"] is False
    assert "no Mem0 compatibility claim" in payload["mem0"]["_note"].lower() \
        or "no mem0 compatibility claim" in payload["mem0"]["_note"].lower()


def test_readme_explicitly_disclaims_mem0() -> None:
    readme = Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text().lower()
    assert "no mem0 compatibility claim" in text


def test_protocol_disclaims_mem0() -> None:
    proto = Path(__file__).resolve().parent.parent / "BENCHMARK_PROTOCOL.md"
    text = proto.read_text().lower()
    assert "no mem0 compatibility claim" in text


def test_no_source_claims_mem0_compat() -> None:
    root = Path(__file__).resolve().parent.parent
    forbidden = re.compile(r"mem0[-_ ]compatible", re.I)
    for py in root.rglob("*.py"):
        if "tests" in py.parts:
            continue
        assert not forbidden.search(py.read_text()), f"{py} claims Mem0 compatibility"
