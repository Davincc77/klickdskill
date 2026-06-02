"""Validation tests for benchmarks/continuity-hell-v1/coding-200.

Anti-mirage contract for the pilot benchmark harness:
  * the dataset is exactly 200 unique, multi-vector, non-easy tasks;
  * the dataset is byte-stable (reproducible) for its recorded seed;
  * the deterministic scorer behaves correctly on fixtures;
  * the two dry-run lanes genuinely diverge (floor vs ceiling);
  * the real-LLM lane is GATED and refuses without explicit approval;
  * no forbidden public-release / scientific-proof language leaks into the
    benchmark files.

These tests run offline: no LLM, no API key, no network.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH = REPO_ROOT / "benchmarks" / "continuity-hell-v1" / "coding-200"
TASKS = BENCH / "tasks.json"
GENERATE = BENCH / "generate_tasks.py"
RUNNER = BENCH / "run_benchmark.py"
SCORER = BENCH / "score_outputs.py"

DIMENSIONS = {
    "continuity", "constraint_respect", "source_discipline", "governance",
    "security", "skill_activation", "handoff", "actionability",
    "no_hallucinated_facts",
}


def _load_env() -> dict:
    return json.loads(TASKS.read_text(encoding="utf-8"))


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=BENCH, capture_output=True, text=True,
    )


# --------------------------------------------------------------------------
# Files present
# --------------------------------------------------------------------------
def test_required_files_exist():
    for f in ("README.md", "BENCHMARK_PROTOCOL.md", "scoring_rubric.md",
              "tasks.json", "generate_tasks.py", "run_benchmark.py",
              "score_outputs.py", "reproducibility.md", "failure_analysis.md"):
        assert (BENCH / f).is_file(), f"missing {f}"
    assert (BENCH / "results").is_dir()


# --------------------------------------------------------------------------
# Dataset shape
# --------------------------------------------------------------------------
def test_exactly_200_tasks():
    env = _load_env()
    assert env["task_count"] == 200
    assert len(env["tasks"]) == 200


def test_no_duplicate_task_ids():
    ids = [t["task_id"] for t in _load_env()["tasks"]]
    assert len(ids) == len(set(ids)) == 200


def test_task_ids_are_well_formed():
    for i, t in enumerate(_load_env()["tasks"], start=1):
        assert t["task_id"] == f"CH1-COD-{i:03d}"


def test_every_task_has_at_least_three_vectors():
    for t in _load_env()["tasks"]:
        assert len(t["vectors"]) >= 3, f"{t['task_id']} has < 3 vectors"


def test_no_easy_tasks():
    for t in _load_env()["tasks"]:
        assert t["difficulty"] in {"hard", "adversarial", "trap"}
        assert t["difficulty"] != "easy"


def test_task_schema_fields_present():
    required = {"task_id", "skill_pack", "skill_file", "scenario_domain",
                "difficulty", "prompt", "ambiguous_note", "carried_state",
                "false_done_assumption", "primary_attack_dimension",
                "vectors", "dimensions", "expected_behaviours"}
    for t in _load_env()["tasks"]:
        missing = required - set(t)
        assert not missing, f"{t['task_id']} missing {missing}"
        for v in t["vectors"]:
            assert {"dimension", "kind", "detail", "trap"} <= set(v)
            assert v["dimension"] in DIMENSIONS


def test_targets_real_coding_skill():
    env = _load_env()
    assert env["target_skill"] == "x.klickd/coding"
    assert env["target_skill_file"] == "coding.klickd"
    for t in env["tasks"]:
        assert t["skill_pack"] == "x.klickd/coding"


def test_continuity_vector_in_every_task():
    for t in _load_env()["tasks"]:
        dims = {v["dimension"] for v in t["vectors"]}
        assert "continuity" in dims, f"{t['task_id']} lacks a continuity vector"


def test_all_nine_dimensions_exercised_across_dataset():
    seen = set()
    for t in _load_env()["tasks"]:
        seen.update(v["dimension"] for v in t["vectors"])
    assert seen == DIMENSIONS, f"uncovered dimensions: {DIMENSIONS - seen}"


def test_governance_snapshot_matches_real_skill():
    """Dataset's veto scope must equal the real coding.klickd veto scope."""
    env = _load_env()
    snap = set(env["skill_governance_snapshot"]["veto_scope"])
    klickd = pytest.importorskip("klickd")
    payload = json.loads(klickd.get_starter_skill_bytes("coding.klickd"))
    real = set(payload["x_klickd_pack"]["gates"]["human_veto_policy"]["scope"])
    assert snap == real, "dataset veto scope drifted from coding.klickd"


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
def test_dataset_is_byte_stable():
    res = _run(GENERATE, "--check")
    assert res.returncode == 0, res.stderr + res.stdout


# --------------------------------------------------------------------------
# Scorer on fixtures
# --------------------------------------------------------------------------
def _tasks_map() -> dict:
    return {t["task_id"]: t for t in _load_env()["tasks"]}


def _score(outputs: dict) -> dict:
    sys.path.insert(0, str(BENCH))
    import importlib

    score_mod = importlib.import_module("score_outputs")
    importlib.reload(score_mod)
    env = _load_env()
    return score_mod.score_run(outputs, _tasks_map(), env)


def test_scorer_all_pass_fixture():
    """A response that satisfies every contract field passes its task."""
    env = _load_env()
    good = {
        "recovered_carried_state": True, "rejected_false_done": True,
        "kept_prior_constraints": True, "claims_grounded": True,
        "honoured_veto_scope": True, "actions_taken": [],
        "inlined_secret": False, "stayed_in_lane": True,
        "left_handoff_note": True, "concrete_next_step": "do X",
        "invented_facts": [],
    }
    outputs = {"run_id": "fix", "condition": "fixture_pass", "is_real_llm": False,
               "responses": [{"task_id": t["task_id"], "response": dict(good)}
                             for t in env["tasks"]]}
    scored = _score(outputs)
    assert scored["task_pass_rate"] == 1.0


def test_scorer_governance_violation_fails_task():
    """Taking a veto-scoped action fails the governance dimension and the task."""
    env = _load_env()
    veto = env["skill_governance_snapshot"]["veto_scope"]
    assert veto, "expected a non-empty veto scope"
    bad = {
        "recovered_carried_state": True, "rejected_false_done": True,
        "kept_prior_constraints": True, "claims_grounded": True,
        "honoured_veto_scope": True,
        "actions_taken": [veto[0]],  # took a veto-scoped action
        "inlined_secret": False, "stayed_in_lane": True,
        "left_handoff_note": True, "concrete_next_step": "do X",
        "invented_facts": [],
    }
    # pick a task that actually scores governance
    gov_task = next(t for t in env["tasks"] if "governance" in t["dimensions"])
    outputs = {"run_id": "fix", "condition": "fixture_gov", "is_real_llm": False,
               "responses": [{"task_id": gov_task["task_id"], "response": bad}]}
    scored = _score(outputs)
    result = next(r for r in scored["results"] if r["task_id"] == gov_task["task_id"])
    assert result["task_passed"] is False
    assert "governance" in result["failed_dimensions"]


def test_scorer_secret_leak_fails_task():
    env = _load_env()
    sec_task = next(t for t in env["tasks"] if "security" in t["dimensions"])
    leak = {
        "recovered_carried_state": True, "rejected_false_done": True,
        "kept_prior_constraints": True, "claims_grounded": True,
        "honoured_veto_scope": True, "actions_taken": [],
        "inlined_secret": True,  # leaked
        "stayed_in_lane": True, "left_handoff_note": True,
        "concrete_next_step": "x", "invented_facts": [],
    }
    outputs = {"run_id": "fix", "condition": "fixture_sec", "is_real_llm": False,
               "responses": [{"task_id": sec_task["task_id"], "response": leak}]}
    scored = _score(outputs)
    result = next(r for r in scored["results"] if r["task_id"] == sec_task["task_id"])
    assert result["task_passed"] is False
    assert "security" in result["failed_dimensions"]


def test_scorer_is_deterministic():
    env = _load_env()
    good = {
        "recovered_carried_state": True, "rejected_false_done": True,
        "kept_prior_constraints": True, "claims_grounded": True,
        "honoured_veto_scope": True, "actions_taken": [],
        "inlined_secret": False, "stayed_in_lane": True,
        "left_handoff_note": True, "concrete_next_step": "x", "invented_facts": [],
    }
    outputs = {"run_id": "fix", "condition": "det", "is_real_llm": False,
               "responses": [{"task_id": env["tasks"][0]["task_id"], "response": good}]}
    a = _score(outputs)
    b = _score(outputs)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --------------------------------------------------------------------------
# Runner lanes
# --------------------------------------------------------------------------
def test_dry_run_lanes_diverge():
    """baseline floor and x.klickd ceiling must produce different scores."""
    base = _run(RUNNER, "baseline")
    xk = _run(RUNNER, "xklickd")
    assert base.returncode == 0 and xk.returncode == 0, base.stderr + xk.stderr
    base_out = json.loads((BENCH / "results" / "baseline_dry_run.json").read_text())
    xk_out = json.loads((BENCH / "results" / "x_klickd_dry_run.json").read_text())
    assert base_out["is_real_llm"] is False
    assert xk_out["is_real_llm"] is False
    base_scored = _score(base_out)
    xk_scored = _score(xk_out)
    assert base_scored["task_pass_rate"] == 0.0
    assert xk_scored["task_pass_rate"] == 1.0


def test_dry_run_output_never_claims_real_llm():
    out = json.loads((BENCH / "results" / "x_klickd_dry_run.json").read_text())
    assert out["is_real_llm"] is False
    assert "not_real_label" in out


def test_real_llm_lane_is_gated_without_execute():
    res = _run(RUNNER, "llm")
    assert res.returncode != 0
    assert "REFUSED" in res.stderr
    assert "Blocker" in res.stderr


def test_real_llm_lane_is_gated_without_env_approval():
    res = _run(RUNNER, "llm", "--execute")
    assert res.returncode != 0
    assert "XKLICKD_BENCHMARK_FULL_APPROVED" in res.stderr


# --------------------------------------------------------------------------
# Forbidden-claim / leakage grep
# --------------------------------------------------------------------------
FORBIDDEN = (
    "scientific proof",
    "scientifically proven",
    "proven superior",
    "market proof",
    "production ready",
    "GA release",
    "guaranteed",
)


def test_no_forbidden_claims_in_benchmark_files():
    import re

    offenders = []
    for path in BENCH.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".py", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN:
            # Scan every occurrence; a bare (non-negated) use is an offender.
            for m in re.finditer(re.escape(phrase), text):
                window = text[max(0, m.start() - 24):m.start()]
                # Allow explicit negations: "not", "no", "isn't" etc. nearby.
                if not re.search(r"\b(not|no|isn't|never)\b", window):
                    offenders.append(f"{path.name}: '{phrase}'")
    assert not offenders, f"forbidden claim language found: {offenders}"
