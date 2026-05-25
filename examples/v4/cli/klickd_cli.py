#!/usr/bin/env python3
"""klickd_cli — minimal path-based loader for .klickd v4.0.0 files.

This is a non-normative demo (R4-PV-1) showing the smallest useful
program built on top of the official package:

    pip install klickd==4.0.0
    python klickd_cli.py path/to/profile.klickd

For encrypted envelopes:

    python klickd_cli.py path/to/profile.klickd --passphrase '...'

The script prints a compact summary of the payload (identity, domain,
key context fields) and exits 0 on success, non-zero on any load or
validation error. No network calls. No telemetry. No secrets written
to disk.

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from klickd import load_klickd, __version__ as klickd_version
except ImportError:  # pragma: no cover - import-time message only
    print(
        "ERROR: the 'klickd' package is not installed.\n"
        "Install with:  pip install klickd==4.0.0",
        file=sys.stderr,
    )
    raise SystemExit(2)


def load_klickd_any(file_bytes: bytes, passphrase: str | None = None) -> dict:
    """Decode a .klickd file regardless of envelope form.

    `klickd.load_klickd` targets the encrypted envelope (cipher + kdf +
    ciphertext). Plain payloads (`encrypted: false`) are valid `.klickd`
    files too — historically loaded with `json.load`. This helper accepts
    either: if the bytes parse as a plain payload, it returns them; if
    they look like an envelope, it delegates to the SDK.
    """
    try:
        obj = json.loads(file_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"file is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON must be an object")
    if obj.get("encrypted") is True or "ciphertext" in obj:
        return load_klickd(file_bytes, passphrase=passphrase)
    return obj


def _summarise(payload: dict) -> str:
    """Return a short human-readable summary of a decoded payload."""
    identity = payload.get("identity") or {}
    context = payload.get("context") or {}
    knowledge = payload.get("knowledge") or {}
    gates = payload.get("verification_gates") or {}

    lines = [
        f"klickd_version        : {payload.get('klickd_version', '(unknown)')}",
        f"payload_schema_version: {payload.get('payload_schema_version', '(unknown)')}",
        f"domain                : {payload.get('domain', '(unset)')}",
        f"profile_kind          : {payload.get('profile_kind', '(unset)')}",
        f"display_name          : {identity.get('display_name', '(unset)')}",
        f"language              : {identity.get('language', '(unset)')}",
    ]
    if context.get("current_project"):
        lines.append(f"current_project       : {context['current_project']}")
    if context.get("current_state"):
        lines.append(f"current_state         : {context['current_state']}")
    if knowledge.get("expertise_level"):
        lines.append(f"expertise_level       : {knowledge['expertise_level']}")
    if gates:
        n_gates = len(gates.get("gates", [])) if isinstance(gates, dict) else 0
        lines.append(f"verification_gates    : {n_gates} declared")
    if payload.get("user_preferences"):
        snippet = payload["user_preferences"].strip().splitlines()[0][:80]
        lines.append(f"user_preferences      : {snippet}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="klickd_cli",
        description="Load a .klickd v4.0.0 profile and print a summary.",
    )
    p.add_argument("path", type=Path, help="Path to a .klickd file")
    p.add_argument(
        "--passphrase",
        default=None,
        help="Passphrase if the envelope is encrypted",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print the decoded payload as pretty JSON instead of a summary",
    )
    p.add_argument(
        "--strip-underscore",
        action="store_true",
        help="Drop '_'-prefixed debug/benchmark keys before printing (SPEC §29)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.path.is_file():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 2

    try:
        payload = load_klickd_any(args.path.read_bytes(), passphrase=args.passphrase)
    except Exception as exc:  # noqa: BLE001 — surface SDK error type + message
        print(f"ERROR: load_klickd failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.strip_underscore:
        payload = {k: v for k, v in payload.items() if not k.startswith("_")}

    print(f"# klickd-cli — package klickd=={klickd_version}")
    print(f"# source: {args.path}")
    print()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(_summarise(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
