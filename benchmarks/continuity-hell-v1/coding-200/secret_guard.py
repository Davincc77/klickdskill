#!/usr/bin/env python3
"""Secret-safety guardrails for the Continuity-Hell v1 / coding-200 harness.

SECRET-SAFETY CONTRACT
----------------------
Provider API keys live ONLY in the private environment / a secret manager. They
must never be committed, logged, written to results/artifacts, or printed. This
module is the single place that enforces that, so the runner and the artifact
scanner share one definition of "what a secret looks like" and "how to redact".

It provides three things:

  * ``scan_text`` / ``scan_obj`` — detect probable secrets (provider key
    formats, generic high-entropy tokens, and any *live* env var value) in a
    string or JSON-able object, returning structured findings WITHOUT ever
    echoing the secret itself.
  * ``redact`` — replace any detected secret with a stable ``[REDACTED:<kind>]``
    marker, so an output envelope can be made safe before it is written.
  * ``preflight_env`` / ``assert_clean`` — verify a required provider env var
    exists (without printing its value) and that a built payload is
    secret-clean before/after a dry-run or real run.

Everything here is offline, deterministic, and prints only redacted findings.
"""
from __future__ import annotations

import math
import os
import re
from typing import Any

# Env vars that, if present, hold a real provider secret. Their *values* must
# never appear in any output. Keep in sync with run_benchmark's preflight gate.
PROVIDER_KEY_ENV_VARS: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "LLM_API_KEY",
)

# Known provider key shapes. These are intentionally broad: a false positive is
# cheap (we redact a non-secret), a false negative leaks a key.
_KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("openai_project_key", re.compile(r"sk-proj-[A-Za-z0-9_\-]{16,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("google_key", re.compile(r"AIza[0-9A-Za-z_\-]{16,}")),
    ("groq_key", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.=]{16,}")),
    ("authorization_header", re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']?\S{12,}")),
)

# Env var names whose *value* (not just key shape) we hunt for in payloads.
# This catches a secret even if its format is unknown to the patterns above.
_MIN_LIVE_VALUE_LEN = 8

# A generic high-entropy token: long, mixed alnum, no whitespace. Used as a
# backstop. Tuned to avoid flagging ordinary identifiers / hashes that the
# benchmark legitimately records (run ids, sha sums are handled by allowlist).
_GENERIC_TOKEN = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")
_ALLOWLIST_PREFIXES = (
    "CH1-COD-",          # task ids
    "baseline_dry_run",  # run ids / conditions
    "x_klickd_dry_run",
    "llm_x_klickd",
)


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _redaction_marker(kind: str) -> str:
    return f"[REDACTED:{kind}]"


def _live_env_secrets() -> dict[str, str]:
    """Map of {env_var: value} for present provider keys. Never logged."""
    out: dict[str, str] = {}
    for name in PROVIDER_KEY_ENV_VARS:
        val = os.environ.get(name)
        if val and len(val) >= _MIN_LIVE_VALUE_LEN:
            out[name] = val
    return out


def scan_text(text: str, *, live_env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Return findings for one string. Each finding records kind + redacted
    preview only; the raw secret is NEVER included.
    """
    if not isinstance(text, str) or not text:
        return []
    findings: list[dict[str, Any]] = []
    env = _live_env_secrets() if live_env is None else live_env

    # 1) Live env var values are the highest-severity match.
    for name, value in env.items():
        if value and value in text:
            findings.append({
                "kind": "live_env_value",
                "env_var": name,
                "preview": _redaction_marker(f"env:{name}"),
            })

    # 2) Known provider key shapes.
    for kind, pat in _KEY_PATTERNS:
        if pat.search(text):
            findings.append({"kind": kind, "preview": _redaction_marker(kind)})

    # 3) Generic high-entropy backstop.
    for m in _GENERIC_TOKEN.finditer(text):
        tok = m.group(0)
        if any(tok.startswith(p) for p in _ALLOWLIST_PREFIXES):
            continue
        if _shannon_entropy(tok) >= 3.5:
            findings.append({"kind": "high_entropy_token", "preview": _redaction_marker("high_entropy_token")})
    return findings


def scan_obj(obj: Any, *, live_env: dict[str, str] | None = None,
             _path: str = "") -> list[dict[str, Any]]:
    """Recursively scan a JSON-able object. Findings carry a JSON-ish path and
    redacted previews only.
    """
    env = _live_env_secrets() if live_env is None else live_env
    findings: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            # A key literally named after a provider env var is suspicious.
            if isinstance(k, str) and k in PROVIDER_KEY_ENV_VARS:
                findings.append({
                    "kind": "secret_env_key_serialized",
                    "path": f"{_path}.{k}" if _path else k,
                    "preview": _redaction_marker(f"key:{k}"),
                })
            findings.extend(scan_obj(v, live_env=env, _path=f"{_path}.{k}" if _path else str(k)))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            findings.extend(scan_obj(v, live_env=env, _path=f"{_path}[{i}]"))
    elif isinstance(obj, str):
        for f in scan_text(obj, live_env=env):
            f = dict(f)
            f["path"] = _path
            findings.append(f)
    return findings


def redact(obj: Any, *, live_env: dict[str, str] | None = None) -> Any:
    """Return a copy of ``obj`` with any detected secret replaced by a stable
    marker. Strings are rewritten; dict keys named after provider env vars are
    dropped entirely (a secret should never be a serialized field).
    """
    env = _live_env_secrets() if live_env is None else live_env
    if isinstance(obj, dict):
        out: dict[Any, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and k in PROVIDER_KEY_ENV_VARS:
                out[k] = _redaction_marker(f"key:{k}")
                continue
            out[k] = redact(v, live_env=env)
        return out
    if isinstance(obj, list):
        return [redact(v, live_env=env) for v in obj]
    if isinstance(obj, tuple):
        return tuple(redact(v, live_env=env) for v in obj)
    if isinstance(obj, str):
        return redact_text(obj, live_env=env)
    return obj


def redact_text(text: str, *, live_env: dict[str, str] | None = None) -> str:
    if not isinstance(text, str) or not text:
        return text
    env = _live_env_secrets() if live_env is None else live_env
    out = text
    # Replace live env values first (most specific), then known shapes.
    for name, value in env.items():
        if value:
            out = out.replace(value, _redaction_marker(f"env:{name}"))
    for kind, pat in _KEY_PATTERNS:
        out = pat.sub(_redaction_marker(kind), out)
    return out


def preflight_env(required_any: tuple[str, ...] = PROVIDER_KEY_ENV_VARS) -> dict[str, Any]:
    """Verify a required provider env var EXISTS without printing its value.

    Returns a report with the names of present vars and a boolean. The value is
    never read into the report.
    """
    present = [n for n in required_any if os.environ.get(n)]
    return {
        "checked": list(required_any),
        "present_env_vars": present,   # names only, never values
        "has_provider_key": bool(present),
    }


def assert_clean(obj: Any, *, label: str = "payload",
                 live_env: dict[str, str] | None = None) -> None:
    """Raise SecretLeakError if ``obj`` contains any detected secret.

    The error message contains only redacted previews and paths — never the
    secret itself.
    """
    findings = scan_obj(obj, live_env=live_env)
    if findings:
        summary = "; ".join(
            f"{f.get('path', '?')}:{f['kind']}={f['preview']}" for f in findings
        )
        raise SecretLeakError(f"{label} is not secret-clean: {summary}")


class SecretLeakError(RuntimeError):
    """Raised when a payload or artifact contains a detected secret."""
