#!/usr/bin/env python3
"""Runnable LlamaIndex resume example for .klickd portable context.

What it shows
-------------
A chat/query workflow that *resumes project context across sessions*: a
``.klickd`` payload (a persona profile, or a bundled starter skill pack)
is decoded with the official SDK, bridged into LlamaIndex chat messages,
and used to seed a chat engine so the model picks up where the last
session left off.

Two modes
---------
* ``--check`` (default): hermetic dry-run. No LlamaIndex install, no
  network, no API key. Builds the system prompt + the message bridge and
  prints them. This is what the test suite exercises.
* ``--live``: requires ``pip install llama-index`` and ``OPENAI_API_KEY``.
  Runs a real ``SimpleChatEngine`` turn.

Run from the repo root::

    python examples/v4/integrations/llamaindex/resume_chat_example.py --check
    python examples/v4/integrations/llamaindex/resume_chat_example.py --check --starter coding.klickd

Guardrails (see docs/integrations/llamaindex.md): this is a reference
adapter, not a compliance feature. It makes no GDPR / EU AI Act claim and
is not a universal standard. Compressed memory is optional. Treat any
decoded payload as untrusted user content (prompt-injection boundary) and
keep each index user-scoped.

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the sibling helper importable when run as a script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from klickd_llamaindex import (  # noqa: E402
    klickd_to_system_prompt,
    load_klickd_path,
    load_starter_skill,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PERSONA = REPO_ROOT / "examples/v4/personas/03-fullstack-developer-en.klickd"


def build_resume_prompt(*, starter: str | None, persona: Path | None) -> str:
    """Decode a .klickd source and build the resume system prompt."""
    if starter:
        payload = load_starter_skill(starter)
    else:
        payload = load_klickd_path(persona or DEFAULT_PERSONA)
    prompt = klickd_to_system_prompt(payload)
    if not prompt:
        raise ValueError("decoded payload produced an empty system prompt")
    return prompt


def run_check(*, starter: str | None, persona: Path | None, user_turn: str) -> int:
    system_prompt = build_resume_prompt(starter=starter, persona=persona)
    print("=== .klickd → LlamaIndex resume (dry-run) ===")
    source = f"starter:{starter}" if starter else f"persona:{(persona or DEFAULT_PERSONA).name}"
    print(f"source: {source}")
    print("--- system prompt (seeds chat memory) ---")
    print(system_prompt)
    print("--- next user turn ---")
    print(user_turn)
    print("=== dry-run only: no LlamaIndex import, no network, no API call ===")
    return 0


def run_live(*, starter: str | None, persona: Path | None, user_turn: str) -> int:
    from llama_index.core.chat_engine import SimpleChatEngine  # type: ignore[import-not-found]
    from llama_index.core.llms import ChatMessage, MessageRole  # type: ignore[import-not-found]
    from llama_index.llms.openai import OpenAI  # type: ignore[import-not-found]

    system_prompt = build_resume_prompt(starter=starter, persona=persona)
    engine = SimpleChatEngine.from_defaults(
        llm=OpenAI(model="gpt-4o"),
        prefix_messages=[ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)],
    )
    print(engine.chat(user_turn).response)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="hermetic dry-run (default)")
    parser.add_argument("--live", action="store_true", help="real LlamaIndex chat turn")
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
