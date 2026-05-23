"""Hermes plugin skeleton — .klickd context-cost POC.

STATUS: experimental. The exact Hermes plugin API surface is not pinned by
this scaffold. The functions below are intentionally framework-agnostic so
they import cleanly without a Hermes install. Where the local Hermes API is
uncertain the integration points are marked with ``TODO(hermes-api)``.

Hard rules (mirrored in skill/SKILL.md and the wrapper script):
- No provider API calls.
- No paid resources.
- No network requests.
- No secrets.
- No SPEC / schema / SDK edits.
- No publishing / tagging / releasing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_NAME = "klickd-context-cost"
PLUGIN_VERSION = "0.0.1-experimental"

# Repo-relative path to the wrapper. Resolved lazily so importing this module
# never touches the filesystem.
WRAPPER_RELPATH = Path("integrations/hermes/scripts/run_context_cost_benchmark.py")


def _repo_root() -> Path:
    """Best-effort locate the repo root.

    Walks upward from this file looking for a ``benchmarks/context_cost``
    directory. Falls back to CWD. No subprocess calls (``git`` may not be
    present in the Hermes runtime).
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "benchmarks" / "context_cost").is_dir():
            return parent
    return Path.cwd()


def _safety_preflight(context: dict[str, Any] | None) -> list[str]:
    """Return a list of human-readable refusals; empty list = OK to proceed.

    The host is expected to call this before invoking the skill. Refusals are
    advisory strings; the host decides how to surface them.
    """
    refusals: list[str] = []
    context = context or {}

    if context.get("network_allowed"):
        refusals.append("network access is not permitted by this plugin")
    if context.get("provider_api_calls_allowed"):
        refusals.append("provider API calls are not permitted by this plugin")
    if context.get("paid_resources_allowed"):
        refusals.append("paid resources are not permitted by this plugin")

    # If a .klickd payload was attached, refuse to proceed if it looks like it
    # carries secrets. This is a coarse heuristic; the skill itself does the
    # real work. We only check obvious field names.
    klickd_payload = context.get("klickd_payload")
    if isinstance(klickd_payload, dict):
        suspicious = {"api_key", "secret", "token", "password", "private_key"}
        if suspicious.intersection(klickd_payload.keys()):
            refusals.append(
                "klickd payload appears to contain secrets; refusing to proceed"
            )

    return refusals


def _run_wrapper(check_only: bool = False) -> dict[str, Any]:
    """Invoke the wrapper script and return its summary.

    No network. No provider calls. Subprocess only runs the local wrapper,
    which in turn only runs the local dry-run runner.
    """
    root = _repo_root()
    wrapper = root / WRAPPER_RELPATH
    if not wrapper.is_file():
        return {
            "ok": False,
            "error": f"wrapper not found at {wrapper}",
        }

    cmd = [sys.executable, str(wrapper)]
    if check_only:
        cmd.append("--check")

    completed = subprocess.run(  # noqa: S603 — local script, no shell
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "wrapper": str(wrapper),
    }


def on_skill_invoke(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Advisory pre-invoke hook.

    TODO(hermes-api): wire this to the host's actual pre-invoke hook name and
    return shape. For now the host can call it directly and inspect the
    ``refusals`` list.
    """
    refusals = _safety_preflight(context)
    return {
        "plugin": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "allow": not refusals,
        "refusals": refusals,
    }


def on_skill_complete(result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Advisory post-invoke hook.

    Echoes the artifact paths back to the host so subsequent steps can consult
    them instead of re-running the dry-run benchmark.

    TODO(hermes-api): wire this to the host's actual post-invoke hook.
    """
    result = result or {}
    return {
        "plugin": PLUGIN_NAME,
        "artifact_hint": (
            "benchmarks/context_cost/results/<YYYY-MM-DD>/ — see report.md, "
            "summary.csv, raw_runs.jsonl, artifacts/"
        ),
        "result_passthrough": result,
    }


def run_benchmark(check_only: bool = False) -> dict[str, Any]:
    """Public callable the skill uses to drive the dry-run benchmark."""
    return _run_wrapper(check_only=check_only)


def register(host: Any | None = None) -> dict[str, Any]:
    """Plugin entry point referenced by ``plugin.yaml``.

    TODO(hermes-api): the real Hermes host likely passes a registration object
    with ``register_hook`` / ``register_skill`` methods. We feature-detect them
    and fall back to a no-op so this import is safe under any host (or none).
    """
    registered: list[str] = []

    if host is not None:
        for hook_name, hook_fn in (
            ("on_skill_invoke", on_skill_invoke),
            ("on_skill_complete", on_skill_complete),
        ):
            register_hook = getattr(host, "register_hook", None)
            if callable(register_hook):
                try:
                    register_hook(hook_name, hook_fn)
                    registered.append(hook_name)
                except Exception:  # noqa: BLE001 — never block import on host errors
                    pass

    return {
        "plugin": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "registered_hooks": registered,
        "experimental": True,
    }


__all__ = [
    "PLUGIN_NAME",
    "PLUGIN_VERSION",
    "on_skill_invoke",
    "on_skill_complete",
    "run_benchmark",
    "register",
]
