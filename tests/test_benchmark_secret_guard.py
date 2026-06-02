"""Secret-safety tests for the Continuity-Hell v1 / coding-200 harness.

These verify the mandatory guardrails before any future real LLM run:
  * fake provider keys / auth headers / high-entropy tokens are DETECTED;
  * detected secrets are REDACTED to a stable marker (raw value gone);
  * a *live* provider env var value is never serialized into an output;
  * the runner refuses to write an envelope that still contains a secret;
  * preflight reports only env var NAMES, never values;
  * the standalone artifact scanner exits non-zero on a planted fake secret
    and zero on clean artifacts.

All tests are offline and use FAKE secrets and a controlled FAKE env var. They
never read or print the real provider key that may be in the environment.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH = REPO_ROOT / "benchmarks" / "continuity-hell-v1" / "coding-200"
RUNNER = BENCH / "run_benchmark.py"
SCANNER = REPO_ROOT / "scripts" / "check_benchmark_secret_leakage.py"

sys.path.insert(0, str(BENCH))
import secret_guard  # noqa: E402

# Obvious fakes — shaped like real keys but never valid.
FAKE_ANTHROPIC = "sk-ant-" + "A0a1B2c3D4e5F6g7H8i9J0k1L2"
FAKE_OPENAI = "sk-" + "ABCDEFGHIJKLMNOPQRSTUVWX1234567890"
FAKE_GOOGLE = "AIza" + "SyA0B1C2D3E4F5G6H7I8J9K0L1M2N3O4P5"
FAKE_BEARER = "Authorization: Bearer abcdef0123456789ABCDEF0123456789"


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------
@pytest.mark.parametrize("blob,expect_kind", [
    (FAKE_ANTHROPIC, "anthropic_key"),
    (FAKE_OPENAI, "openai_key"),
    (FAKE_GOOGLE, "google_key"),
    (FAKE_BEARER, "bearer_token"),
])
def test_detects_known_key_shapes(blob, expect_kind):
    findings = secret_guard.scan_text(f"prefix {blob} suffix", live_env={})
    kinds = {f["kind"] for f in findings}
    assert expect_kind in kinds, f"expected {expect_kind} in {kinds}"
    # The raw secret must never appear in a finding.
    for f in findings:
        assert blob not in json.dumps(f)


def test_clean_text_has_no_findings():
    clean = "Recovered carried state; run_id=baseline_dry_run-20260602T0000Z; task CH1-COD-001."
    assert secret_guard.scan_text(clean, live_env={}) == []


def test_detects_live_env_value_by_value_not_shape():
    """A secret whose *format* is unknown is still caught if it equals a live
    provider env var value."""
    secret = "totally-custom-not-a-known-shape-value-123456"
    findings = secret_guard.scan_text(
        f"leaked: {secret}", live_env={"LLM_API_KEY": secret})
    kinds = {f["kind"] for f in findings}
    assert "live_env_value" in kinds
    for f in findings:
        assert secret not in json.dumps(f)


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------
def test_redact_text_removes_raw_secret():
    out = secret_guard.redact_text(f"key={FAKE_ANTHROPIC}", live_env={})
    assert FAKE_ANTHROPIC not in out
    assert "[REDACTED:anthropic_key]" in out


def test_redact_obj_drops_serialized_env_key_field():
    obj = {"model": "x", "ANTHROPIC_API_KEY": FAKE_ANTHROPIC, "nested": [FAKE_OPENAI]}
    red = secret_guard.redact(obj, live_env={})
    dumped = json.dumps(red)
    assert FAKE_ANTHROPIC not in dumped
    assert FAKE_OPENAI not in dumped
    assert red["ANTHROPIC_API_KEY"].startswith("[REDACTED:")
    assert "[REDACTED:openai_key]" in dumped


def test_redact_removes_live_env_value_anywhere():
    secret = "live-secret-value-abcdef-987654"
    obj = {"free_text": f"oops {secret}", "list": [{"deep": secret}]}
    red = secret_guard.redact(obj, live_env={"OPENAI_API_KEY": secret})
    assert secret not in json.dumps(red)


# --------------------------------------------------------------------------
# assert_clean
# --------------------------------------------------------------------------
def test_assert_clean_raises_on_secret_and_redacts_message():
    secret = "live-value-to-keep-out-of-errors-555"
    with pytest.raises(secret_guard.SecretLeakError) as ei:
        secret_guard.assert_clean(
            {"x": f"boom {secret}"}, live_env={"LLM_API_KEY": secret})
    assert secret not in str(ei.value)


def test_assert_clean_passes_on_clean_payload():
    secret_guard.assert_clean(
        {"run_id": "baseline_dry_run-x", "model": None}, live_env={})


# --------------------------------------------------------------------------
# Preflight is value-blind
# --------------------------------------------------------------------------
def test_preflight_reports_names_not_values(monkeypatch):
    secret = "preflight-secret-value-do-not-leak-321"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    report = secret_guard.preflight_env()
    assert report["has_provider_key"] is True
    assert "ANTHROPIC_API_KEY" in report["present_env_vars"]
    assert secret not in json.dumps(report)


def test_preflight_no_key(monkeypatch):
    for name in secret_guard.PROVIDER_KEY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    report = secret_guard.preflight_env()
    assert report["has_provider_key"] is False
    assert report["present_env_vars"] == []


# --------------------------------------------------------------------------
# Runner refuses to serialize a live env var value
# --------------------------------------------------------------------------
def _run_runner(env: dict | None, *args: str) -> subprocess.CompletedProcess[str]:
    import os

    full_env = dict(os.environ)
    # Strip any real provider key so the subprocess can't accidentally use it.
    for name in secret_guard.PROVIDER_KEY_ENV_VARS:
        full_env.pop(name, None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=BENCH, capture_output=True, text=True, env=full_env,
    )


def test_dry_run_artifact_never_contains_env_value(tmp_path):
    """Even if a provider key is set, the written dry-run artifact must not
    contain its value."""
    secret = "subprocess-live-secret-value-7777777"
    out = tmp_path / "xk.json"
    res = _run_runner({"ANTHROPIC_API_KEY": secret}, "xklickd", "--out", str(out))
    assert res.returncode == 0, res.stderr
    text = out.read_text(encoding="utf-8")
    assert secret not in text
    # And the value must not have leaked to stdout/stderr either.
    assert secret not in res.stdout + res.stderr


def test_preflight_mode_is_value_blind(tmp_path):
    secret = "subprocess-preflight-secret-888888"
    res = _run_runner({"ANTHROPIC_API_KEY": secret}, "preflight")
    assert secret not in res.stdout + res.stderr
    assert "ANTHROPIC_API_KEY" in res.stdout  # name reported
    assert res.returncode == 0


# --------------------------------------------------------------------------
# Standalone artifact scanner
# --------------------------------------------------------------------------
def test_scanner_clean_dir_exits_zero(tmp_path):
    (tmp_path / "ok.json").write_text(
        json.dumps({"run_id": "baseline_dry_run-x", "model": None}) + "\n")
    res = subprocess.run(
        [sys.executable, str(SCANNER), str(tmp_path)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "no secret leakage" in res.stdout


def test_scanner_planted_fake_key_exits_nonzero(tmp_path):
    planted = tmp_path / "leak.json"
    planted.write_text(json.dumps({"oops": FAKE_ANTHROPIC}) + "\n")
    res = subprocess.run(
        [sys.executable, str(SCANNER), str(tmp_path)],
        capture_output=True, text=True,
    )
    assert res.returncode == 1
    assert "SECRET LEAKAGE DETECTED" in res.stderr
    # Scanner must not echo the raw secret.
    assert FAKE_ANTHROPIC not in res.stdout + res.stderr


def test_scanner_default_results_dir_is_clean():
    res = subprocess.run(
        [sys.executable, str(SCANNER)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
