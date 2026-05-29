"""Targeted regression probe for bundle_index=4 (b05_drone_mission_ops).

Two known stalls were observed against Gemini for this bundle only (runs
26634227315 and 26637685221, same head SHA, same params). Bundle indices
0..3 of the same wave completed cleanly. This module pins three things:

1.  The bundle_index -> bundle_id mapping is the stable 0..4 order
    (b01_ai_app_launch .. b05_drone_mission_ops), so no off-by-one ever
    lands us on b05 by accident.
2.  When a provider call hangs forever, the bundle executor must NOT
    hang the whole run: the per-future wall-clock cap classifies it as
    ``wall_clock_timeout`` and the batch makes progress.
3.  ``ProviderConfig.timeout_s`` is honoured by the gemini adapter
    (passed through as ``http_options.timeout`` in ms).

These tests use the mock provider plus a hand-rolled "hanging" provider,
so CI never calls Gemini.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import pytest

from conftest import providers, runner, ROOT


# Reuse the loader / namespace helpers from the existing bundle test
# module so we stay in lock-step with how that file boots the runner.
sys.path.insert(0, str(Path(__file__).parent))
from test_pilot_test_b_bundles import (  # noqa: E402
    _gen_fixtures,
    _load_test_b_bundle_modules,
    _ns,
    bundles_mod,
)


def test_bundle_index_4_maps_to_drone_mission_ops() -> None:
    """Guards against off-by-one fixture/order regressions on b05."""
    assert bundles_mod.BUNDLES[4]["bundle_id"] == "b05_drone_mission_ops"
    assert bundles_mod.BUNDLES[4]["title"] == "Drone/Mission Ops"


def test_first_call_for_bundle_index_4_is_scoping_no_memory(
    tmp_path: Path,
) -> None:
    """The very first call sent for bundle_index=4 should be a scoping
    phase / no_memory probe — i.e. tiny prompt, no large context. If this
    ever changes silently the first stall point moves with it.
    """
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=150)
    prompts_bb, executor_bb = _load_test_b_bundle_modules()
    sessions = [
        json.loads(l)
        for l in (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
        if l.strip()
    ]
    b4 = [s for s in sessions if s["bundle_id"] == "b05_drone_mission_ops"]
    b4.sort(key=lambda s: s["session_index"])
    calls = executor_bb.expand_bundle_calls(
        sessions=b4,
        conditions=prompts_bb.TEST_B_BUNDLE_CONDITIONS,
    )
    first = calls[0]
    assert first["bundle_id"] == "b05_drone_mission_ops"
    assert first["session_index"] == 1
    assert first["condition"] == "no_memory"
    assert first["phase_id"] == "p01_scoping"
    # Sanity: prompt is small (no prior context block).
    assert len(first["system"]) + len(first["user"]) < 4_000


class _HangingProvider:
    """Provider whose generate() blocks forever (until process exit)."""

    name = "hang"

    def generate(self, system: str, user: str, config):  # pragma: no cover - never returns
        # Block on a never-set event so the call genuinely hangs.
        threading.Event().wait()


def test_bundle_executor_does_not_deadlock_on_hung_provider(
    tmp_path: Path,
) -> None:
    """The per-future wall-clock cap must classify a hung call and let the
    batch finish. Before the fix this test would block until pytest's own
    timeout and the whole pool's __exit__ would wait forever on the worker.

    We use a tiny fixture (1 bundle, 1 session) and request_timeout_s=1
    with retry_max=0 so the executor's wall-clock cap floor is ~6s.
    """
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=1)
    args = _ns(
        fxt,
        bundle_index=4,
        sessions_per_bundle=1,
        concurrency=2,
        batch_size=12,  # whole bundle (12 conditions) in one batch
        retry_max=0,
        retry_backoff=0.0,
        retry_backoff_max=0.0,
        run_id="b4_hang_unit",
        _provider_instance=_HangingProvider(),
        provider="mock",  # registered name; instance overrides resolution
    )
    # Short per-request timeout so the executor's wall-clock cap is small.
    args.request_timeout_s = 1.0

    t0 = time.monotonic()
    done = threading.Event()
    result: dict = {}

    def _go() -> None:
        try:
            result["rc"] = runner.cmd_pilot_test_b_bundles(args)
        except BaseException as exc:  # noqa: BLE001
            result["err"] = repr(exc)
        finally:
            done.set()

    th = threading.Thread(target=_go, daemon=True)
    th.start()
    # Outer guard: 30s. Cap is ~6s, single batch, so we should finish well
    # under that. The thread itself is daemon, so even on regression the
    # test will not pin CI — pytest will just fail this assertion.
    done.wait(timeout=30)
    elapsed = time.monotonic() - t0
    assert done.is_set(), (
        f"bundle executor did not return within 30s with a hung provider "
        f"(elapsed={elapsed:.1f}s) — wall-clock cap regression"
    )
    assert "err" not in result, result.get("err")
    # All calls should have been recorded as wall-clock timeouts.
    run_dir = ROOT / "results"
    matches = list(run_dir.rglob("b4_hang_unit/errors.jsonl"))
    assert matches, "expected errors.jsonl for the hung-provider run"
    errs = [
        json.loads(l) for l in matches[0].read_text().splitlines() if l.strip()
    ]
    assert errs, "expected at least one error row"
    assert all(
        e["final_error_class"] == "wall_clock_timeout" for e in errs
    ), [e["final_error_class"] for e in errs]


def test_gemini_adapter_passes_timeout_to_http_options() -> None:
    """Regression: the adapter must forward ProviderConfig.timeout_s as
    HttpOptions.timeout (ms). Before the fix it dropped the value.
    """
    from importlib import import_module

    sys.path.insert(0, str(ROOT))
    base = import_module("providers.base")
    gemini_mod = import_module("providers.gemini_adapter")

    captured: dict = {}

    class _FakeModels:
        def generate_content(self, **kwargs):
            captured["config"] = kwargs.get("config")

            class _R:
                text = "ok"
                usage_metadata = None
                candidates = []

            return _R()

    class _FakeClient:
        def __init__(self) -> None:
            self.models = _FakeModels()

    prov = gemini_mod.GeminiProvider(api_key="dummy-not-used")
    prov._client = _FakeClient()
    cfg = base.ProviderConfig(model="gemini-2.5-flash", timeout_s=12.5)
    prov.generate("sys", "user", cfg)
    assert "http_options" in captured["config"]
    assert captured["config"]["http_options"]["timeout"] == 12_500
