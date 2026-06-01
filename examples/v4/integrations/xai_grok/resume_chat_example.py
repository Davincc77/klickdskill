#!/usr/bin/env python3
"""Runnable xAI/Grok resume example for .klickd portable context.

What it shows
-------------
A chat workflow that *resumes context across sessions*: a ``.klickd``
payload (a persona profile, or a bundled starter skill pack) is decoded
with the official SDK, bridged into OpenAI-compatible chat messages, and
sent to xAI's Grok ``chat.completions`` endpoint so the model picks up
where the last session left off.

Two modes
---------
* ``--check`` (default): hermetic dry-run. No ``openai`` install, no
  network, no API key. Builds the system prompt + the message bridge and
  prints them. This is what the test suite exercises.
* ``--live``: requires ``pip install openai>=1.0`` and ``XAI_API_KEY``.
  Runs a real ``chat.completions`` turn against ``https://api.x.ai/v1``.

Run from the repo root::

    python examples/v4/integrations/xai_grok/resume_chat_example.py --check
    python examples/v4/integrations/xai_grok/resume_chat_example.py --check --starter coding.klickd

Guardrails (see docs/integrations/xai_grok.md): this is a compatible
workflow bridge over xAI's OpenAI-compatible API, not native xAI support
beyond the adapter below. It makes no GDPR / EU AI Act claim and is not a
universal standard. Compressed memory is optional. Treat any decoded
payload as untrusted user content (prompt-injection boundary) and never
embed the API key in a ``.klickd`` profile.

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the sibling helper importable when run as a script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from klickd_xai import (  # noqa: E402
    DEFAULT_MODEL,
    klickd_to_messages,
    load_klickd_path,
    load_starter_skill,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PERSONA = REPO_ROOT / "examples/v4/personas/05-rpg-gamer-en.klickd"


def build_messages(
    *, starter: str | None, persona: Path | None, user_turn: str
) -> list[dict[str, str]]:
    """Decode a .klickd source and bridge it into Grok chat messages."""
    if starter:
        payload = load_starter_skill(starter)
    else:
        payload = load_klickd_path(persona or DEFAULT_PERSONA)
    return klickd_to_messages(payload, user_turn)


def run_check(*, starter: str | None, persona: Path | None, user_turn: str) -> int:
    messages = build_messages(starter=starter, persona=persona, user_turn=user_turn)
    source = f"starter:{starter}" if starter else f"persona:{(persona or DEFAULT_PERSONA).name}"
    print("=== .klickd → xAI/Grok resume (dry-run) ===")
    print(f"source: {source}")
    print(f"model:  {DEFAULT_MODEL}")
    for msg in messages:
        print(f"--- {msg['role']} message ---")
        print(msg["content"])
    print("=== dry-run only: no openai import, no network, no API call ===")
    return 0


def run_live(*, starter: str | None, persona: Path | None, user_turn: str) -> int:
    import os

    from openai import OpenAI  # type: ignore[import-not-found]

    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise RuntimeError("XAI_API_KEY not set; export it before running --live.")

    messages = build_messages(starter=starter, persona=persona, user_turn=user_turn)
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(model=DEFAULT_MODEL, messages=messages)
    print(response.choices[0].message.content)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="hermetic dry-run (default)")
    parser.add_argument("--live", action="store_true", help="real xAI/Grok chat turn")
    parser.add_argument("--starter", help="bundled starter skill, e.g. coding.klickd")
    parser.add_argument("--persona", type=Path, help="path to a .klickd persona file")
    parser.add_argument(
        "--user-turn",
        default="Let's pick up where we left off — what's the next concrete step?",
        help="the user message to send after resuming context",
    )
    args = parser.parse_args(argv)

    runner = run_live if args.live else run_check
    return runner(starter=args.starter, persona=args.persona, user_turn=args.user_turn)


if __name__ == "__main__":
    raise SystemExit(main())
