#!/usr/bin/env python3
"""klickd-copilot-bridge — local CLI pre-step for GitHub / M365 Copilot.

Reads a `.klickd` v4 profile from disk, decrypts it locally if needed
(passphrase prompted from a TTY — never read from environment variables
or argv in this script), runs it through the schema-tolerant context
builder, and writes a sanitized system/context block to either:

  * stdout (default), so the user can pipe it into ``pbcopy`` / ``xclip``
    and paste it into a Copilot Chat session, **or**
  * a file via ``--out PATH``, e.g. ``--out .copilot-context.md``.

What this script is NOT:

  * It does **not** call any Copilot, OpenAI, Anthropic, or other
    provider API. There is no network I/O.
  * It does **not** persist the decrypted payload anywhere.
  * It does **not** accept the passphrase via ``--passphrase`` or
    ``$KLICKD_PASSPHRASE``. Passphrases come from an interactive prompt
    (``getpass``) only. This is deliberate to avoid passphrases ending
    up in shell history, CI logs, or process listings.

Usage
-----

    python klickd_copilot_bridge.py path/to/profile.klickd
    python klickd_copilot_bridge.py path/to/profile.klickd --out ctx.md
    python klickd_copilot_bridge.py path/to/profile.klickd --dry-run

``--dry-run`` skips decryption entirely and emits a context block built
from any plain (``encrypted: false``) fields only — useful for testing
the redaction pipeline without exposing a passphrase.

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Any

# Allow running directly from the repo without installing as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from context_builder import build_context_block  # noqa: E402

try:
    from klickd import load_klickd  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — surfaced at runtime only
    load_klickd = None  # type: ignore[assignment]


def _read_envelope(path: Path) -> tuple[dict[str, Any], bytes]:
    """Read a `.klickd` file as bytes + parsed envelope dict."""
    raw = path.read_bytes()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"ERROR: {path} is not valid UTF-8 JSON: {exc}")
    if not isinstance(obj, dict):
        raise SystemExit(f"ERROR: top-level JSON in {path} must be an object")
    return obj, raw


def _is_encrypted(envelope: dict[str, Any]) -> bool:
    return envelope.get("encrypted") is True or "ciphertext" in envelope


def _decrypt(envelope_bytes: bytes, passphrase: str) -> dict[str, Any]:
    if load_klickd is None:
        raise SystemExit(
            "ERROR: the 'klickd' package is required for encrypted profiles.\n"
            "Install with:  pip install klickd>=4.0.0"
        )
    return load_klickd(envelope_bytes, passphrase=passphrase)


def _prompt_passphrase() -> str:
    if not sys.stdin.isatty():
        raise SystemExit(
            "ERROR: encrypted profile requires a passphrase, but stdin is "
            "not a TTY. Run this script from an interactive terminal — "
            "this bridge intentionally refuses to read the passphrase "
            "from --passphrase, $KLICKD_PASSPHRASE, or stdin to avoid "
            "leaking it into shell history or logs."
        )
    return getpass.getpass("Passphrase for .klickd profile (not echoed): ")


def load_payload(path: Path, *, dry_run: bool) -> dict[str, Any]:
    """Load a `.klickd` payload from disk.

    In ``dry_run`` mode, encrypted envelopes are returned as-is (envelope
    keys only) without any decryption attempt, so the redaction pipeline
    can be exercised without a passphrase.
    """
    envelope, raw = _read_envelope(path)
    if not _is_encrypted(envelope):
        return envelope
    if dry_run:
        # Strip the ciphertext blob so the builder doesn't try to format it.
        envelope = {
            k: v for k, v in envelope.items()
            if k not in ("ciphertext", "kdf", "cipher")
        }
        envelope.setdefault(
            "user_preferences",
            "[dry-run] encrypted payload not decoded; only envelope metadata shown.",
        )
        return envelope
    passphrase = _prompt_passphrase()
    try:
        return _decrypt(raw, passphrase)
    finally:
        # Best-effort: clear the local reference. Python strings are
        # immutable so this cannot truly zero memory, but it removes the
        # only name binding we control.
        passphrase = ""  # noqa: F841


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="klickd-copilot-bridge",
        description=(
            "Export a sanitized system/context block from a local .klickd v4 "
            "profile, suitable for user-mediated paste into GitHub Copilot "
            "Chat or for a VS Code extension to inject."
        ),
    )
    p.add_argument("path", type=Path, help="Path to a .klickd v4 profile")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the context block to PATH instead of stdout",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Skip decryption; build a context block from envelope-level "
            "fields only. Useful for testing the redaction pipeline."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.path.is_file():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 2

    try:
        payload = load_payload(args.path, dry_run=args.dry_run)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — surface SDK error type + message
        print(
            f"ERROR: failed to load {args.path}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    block = build_context_block(payload)

    if args.out is not None:
        args.out.write_text(block, encoding="utf-8")
        print(
            f"# wrote {len(block)} chars of sanitized context to {args.out}",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
