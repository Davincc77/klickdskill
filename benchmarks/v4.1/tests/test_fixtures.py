"""Fixture count and determinism tests."""
from __future__ import annotations

import json
from pathlib import Path

from conftest import generator


def test_fixture_counts_small(tmp_path: Path) -> None:
    m = generator.generate(seed=4242, n_users=5, sessions_per_user=4, out_dir=tmp_path)
    # 5 users, 6 families, 3 conditions = 90 Test A runs
    assert m["counts"]["personas"] == 5
    assert m["counts"]["test_a_runs"] == 5 * 6 * 3
    assert m["counts"]["test_b_sessions"] == 5 * 4


def test_fixture_counts_full_scale(tmp_path: Path) -> None:
    # 500 users, 10 sessions/user -> 5000 sessions.
    # 500 users * 6 families * 3 conditions = 9000 Test A run specs.
    m = generator.generate(seed=4242, n_users=500, sessions_per_user=10, out_dir=tmp_path)
    assert m["counts"]["personas"] == 500
    assert m["counts"]["test_b_sessions"] == 5000
    assert m["counts"]["test_a_runs"] == 500 * 6 * 3


def test_determinism_same_seed(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    m1 = generator.generate(seed=4242, n_users=10, sessions_per_user=4, out_dir=a)
    m2 = generator.generate(seed=4242, n_users=10, sessions_per_user=4, out_dir=b)
    for key in ("personas", "test_a_runs", "test_b_sessions"):
        assert m1["files"][key]["sha256"] == m2["files"][key]["sha256"], key


def test_determinism_different_seed(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    m1 = generator.generate(seed=4242, n_users=10, sessions_per_user=4, out_dir=a)
    m2 = generator.generate(seed=9999, n_users=10, sessions_per_user=4, out_dir=b)
    assert m1["files"]["personas"]["sha256"] != m2["files"]["personas"]["sha256"]


def test_fixture_files_are_jsonl(tmp_path: Path) -> None:
    generator.generate(seed=4242, n_users=3, sessions_per_user=4, out_dir=tmp_path)
    for fname in ("personas.jsonl", "test_a_runs.jsonl", "test_b_sessions.jsonl"):
        path = tmp_path / fname
        for line in path.read_text().splitlines():
            assert line.strip(), f"empty line in {fname}"
            json.loads(line)
