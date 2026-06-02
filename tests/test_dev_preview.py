"""Tests for examples/dev-preview/ (Day 2 dev-preview quickstart).

Anti-mirage contract: the smoke test and demo must actually run to a clean
exit, the demo must produce the scorecard, and the two demo lanes must
genuinely diverge (otherwise the comparison proves nothing). These tests run
the scripts as the SDK exposes them -- no LLM, no API key, no network.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_PREVIEW = REPO_ROOT / "examples" / "dev-preview"
HELLO = DEV_PREVIEW / "hello_skill.py"
DEMO = DEV_PREVIEW / "run_demo.py"
SCORECARD = DEV_PREVIEW / "results" / "comparison_scorecard.md"

pytest.importorskip("klickd", reason="install with `pip install -e .` from repo root")


def _run(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_dev_preview_scripts_exist():
    for f in (HELLO, DEMO, DEV_PREVIEW / "README.md",
              DEV_PREVIEW / "fixtures" / "interrupted_task.json"):
        assert f.is_file(), f"missing {f}"


def test_hello_skill_runs_clean():
    proc = _run(HELLO)
    assert proc.returncode == 0, proc.stderr
    assert "smoke test passed" in proc.stdout


def test_run_demo_writes_scorecard_and_diverges():
    proc = _run(DEMO)
    assert proc.returncode == 0, proc.stderr
    assert SCORECARD.is_file(), "scorecard was not generated"
    text = SCORECARD.read_text(encoding="utf-8")
    # Lanes must diverge on the headline metrics.
    assert "Baseline (prompt only)" in text
    assert "With x.klickd context" in text
    assert "| 2 | 0 |" in text, "risky-action counts did not diverge as expected"
    # Truth boundary must be present in the generated artifact.
    assert "not a model benchmark" in text.lower()


def test_demo_governance_comes_from_real_skill():
    """The veto scope in the scorecard must match the bundled coding skill."""
    import klickd

    payload = json.loads(klickd.get_starter_skill_bytes("coding.klickd"))
    scope = payload["x_klickd_pack"]["gates"]["human_veto_policy"]["scope"]
    assert SCORECARD.is_file(), "run run_demo.py first"
    text = SCORECARD.read_text(encoding="utf-8")
    for action in scope:
        assert action in text, f"veto scope {action!r} not reflected in scorecard"


def test_dev_preview_makes_no_forbidden_claims():
    """Guard against release/benchmark/internal-leak language in preview docs."""
    forbidden = [
        "v4.2 release",
        "public v4.2",
        "model benchmark proves",
        "outperforms",
        "ga release",
    ]
    for doc in (DEV_PREVIEW / "README.md", SCORECARD):
        if not doc.is_file():
            continue
        low = doc.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in low, f"forbidden phrase {phrase!r} in {doc.name}"
