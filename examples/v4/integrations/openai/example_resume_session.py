#!/usr/bin/env python3
"""Cross-session resume example for the .klickd OpenAI context bridge.

Two modes:

  --check / dry-run (DEFAULT) — runs end-to-end from a clean checkout with
      **no network and no openai install required**. It seeds memory from the
      bundled `coding` starter skill, saves an encrypted portable `.klickd`
      profile to a temp file (session 1), then loads it back through the
      bridge and prints the OpenAI message list + request kwargs that *would*
      be sent (session 2). No API key, no LLM call.

  --live — additionally makes one real `chat.completions.create` call. Requires
      `pip install openai` and `OPENAI_API_KEY` in the environment. Skipped
      automatically (with a clear message) if either is missing.

The demo passphrase below is hardcoded **only because this is a throwaway temp
file**. Never hardcode or commit a real passphrase: the trusted local runtime
decrypts the file, never the model.

Run:
    PYTHONPATH=packages/pypi/klickd/src \\
        python examples/v4/integrations/openai/example_resume_session.py            # dry-run
    PYTHONPATH=packages/pypi/klickd/src \\
        python examples/v4/integrations/openai/example_resume_session.py --live     # real call

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Allow running directly from the repo checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from klickd import save_klickd  # noqa: E402
from klickd_openai import KlickdOpenAI, load_starter_skill  # noqa: E402

# Demo-only passphrase for the throwaway temp profile. See module docstring.
_DEMO_PASSPHRASE = "demo-passphrase-not-secret"
_MODEL = "gpt-4o"


def session_one(out_path: Path) -> None:
    """Seed memory from a starter skill and save a portable profile."""
    print("=== Session 1: seed + save ===")
    payload = load_starter_skill("coding.klickd")

    payload["memory"] = [
        {
            "id": "00000000-0000-4000-a000-000000000001",
            "ts": "2026-05-26T09:00:00Z",
            "role": "user",
            "content": "We are wiring .klickd memory into an OpenAI chat app.",
            "modality": "text",
        },
        {
            "id": "00000000-0000-4000-a000-000000000002",
            "ts": "2026-05-26T09:03:00Z",
            "role": "assistant",
            "content": "Loader + bridge drafted. Next: resume across sessions.",
            "modality": "text",
        },
    ]
    payload["context"] = {
        "current_project": "klickd OpenAI bridge",
        "current_state": "bridge drafted; verifying cross-session resume",
        "resume_trigger": "user says 'continue'",
    }

    file_bytes = save_klickd(payload, _DEMO_PASSPHRASE, domain="software_engineering")
    out_path.write_bytes(file_bytes)
    print(f"saved encrypted portable profile -> {out_path} ({len(file_bytes)} bytes)\n")


def session_two(in_path: Path, *, live: bool) -> None:
    """Fresh load: rebuild OpenAI messages + request from the saved profile."""
    print("=== Session 2: load + resume ===")
    bridge = KlickdOpenAI.from_path(in_path, passphrase=_DEMO_PASSPHRASE)

    if bridge.schema_warnings:
        print(f"(non-fatal schema findings: {len(bridge.schema_warnings)})")

    print("\n-- resume context --")
    print(json.dumps(bridge.resume_context(), indent=2))

    print("\n-- OpenAI messages (role -> content preview) --")
    messages = bridge.to_messages()
    for msg in messages:
        content = msg["content"]
        preview = content if len(content) <= 100 else content[:97] + "..."
        print(f"  [{msg['role']}] {preview}")

    print("\n-- human authority (carried through unchanged) --")
    print(json.dumps(bridge.human_authority(), indent=2))

    request = bridge.to_request(
        model=_MODEL,
        user_input="continue",
        temperature=0,
    )
    print("\n-- chat.completions.create kwargs (dry-run, not sent) --")
    print(f"  model: {request['model']}")
    print(f"  messages: {len(request['messages'])}")
    print(f"  temperature: {request.get('temperature')}")

    if live:
        _run_live(bridge)
    else:
        print("\n(dry-run: no network call. Pass --live to call the API.)")


def _run_live(bridge: KlickdOpenAI) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n(--live requested but OPENAI_API_KEY is unset — skipping real call)")
        return
    try:
        import openai  # noqa: F401
    except ImportError:
        print("\n(--live requested but openai is not installed — skipping real call)")
        return
    print("\n-- live OpenAI call --")
    resp = bridge.create(model=_MODEL, user_input="continue", temperature=0)
    print(resp.choices[0].message.content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="make one real OpenAI call (needs openai + OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="explicit dry-run (default); no network call",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp) / "resume.klickd"
        session_one(profile)
        session_two(profile, live=args.live)

    print("\nDone. Context resumed across sessions from a portable .klickd file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
