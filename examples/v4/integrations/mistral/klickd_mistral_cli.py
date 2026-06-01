"""CLI for the Mistral x .klickd bridge.

Two modes:

  --dry-run (default)  Build and print the Mistral request (system prompt +
                       messages) as JSON. No network, no SDK, no API key.
  --live               Actually call Mistral. Requires `pip install mistralai`
                       and MISTRAL_API_KEY. Off by default so the common path
                       stays hermetic and free.

Examples:

    python klickd_mistral_cli.py fixtures/resume_session.klickd
    python klickd_mistral_cli.py profile.klickd --message "Let's continue."
    python klickd_mistral_cli.py profile.klickd --replay-memory
    python klickd_mistral_cli.py profile.klickd --live --message "Hi"

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running directly without installing this folder as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from klickd_mistral import (  # noqa: E402
    DEFAULT_MODEL,
    chat,
    klickd_to_messages,
    load_klickd_path,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mistral x .klickd context bridge")
    parser.add_argument("profile", help="path to a .klickd file (plain or encrypted)")
    parser.add_argument(
        "--message",
        default="Let's continue.",
        help="the live user turn to append (default: 'Let's continue.')",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Mistral model id")
    parser.add_argument(
        "--passphrase",
        default=None,
        help="passphrase for an encrypted .klickd envelope",
    )
    parser.add_argument(
        "--replay-memory",
        action="store_true",
        help="replay memory[] turns verbatim (off = compressed default)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="build the request locally and print it; no network (default)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="call the Mistral API (needs mistralai + MISTRAL_API_KEY)",
    )
    args = parser.parse_args(argv)

    if not Path(args.profile).is_file():
        print(f"error: file not found: {args.profile}", file=sys.stderr)
        return 2

    try:
        if args.live:
            reply = chat(
                args.profile,
                args.message,
                model=args.model,
                passphrase=args.passphrase,
                replay_memory=args.replay_memory,
            )
            print(reply)
            return 0

        payload = load_klickd_path(args.profile, passphrase=args.passphrase)
        messages = klickd_to_messages(
            payload, args.message, replay_memory=args.replay_memory
        )
        request = {"model": args.model, "messages": messages}
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return 0
    except ImportError:
        print(
            "error: --live needs the Mistral SDK. Run: pip install mistralai",
            file=sys.stderr,
        )
        return 1
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
