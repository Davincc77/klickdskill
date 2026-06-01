#!/usr/bin/env python3
"""Cross-session resume example for the .klickd LangChain/LangGraph bridge.

Runs end-to-end from a clean checkout with **no network and no LangChain
install required**:

  Session 1  — start from the bundled `coding` starter skill, append two
               conversation turns, and save an encrypted portable `.klickd`
               profile to a temp file (this is the "soul" the user carries
               between hosts).
  Session 2  — in a fresh process-like scope, load that file back through the
               bridge (decrypting locally with the passphrase) and rebuild the
               LangChain messages + LangGraph state, proving the context
               resumes.

The demo passphrase below is hardcoded **only because this is a throwaway
temp file**. Never hardcode or commit a real passphrase: the trusted local
runtime decrypts the file, never the model.

If `langchain-core` (and optionally `langgraph`) are installed, the example
also builds real LangChain message objects and a tiny LangGraph that echoes
the resumed state. Without them, it prints the dependency-free
`(role, content)` tuples and the plain state dict instead.

No provider API key is used — there is no LLM call. The point is the portable
*memory*, not a chat completion.

Run:
    PYTHONPATH=packages/pypi/klickd/src \\
        python examples/v4/integrations/langchain/example_resume_session.py

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Allow running directly from the repo checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from klickd import save_klickd  # noqa: E402
from klickd_memory import KlickdMemory, load_starter_skill  # noqa: E402

# Demo-only passphrase for the throwaway temp profile. See module docstring.
_DEMO_PASSPHRASE = "demo-passphrase-not-secret"


def session_one(out_path: Path) -> None:
    """Seed memory from a starter skill and save a portable profile."""
    print("=== Session 1: seed + save ===")
    payload = load_starter_skill("coding.klickd")

    # The starter skill carries no chat memory; we append two turns the way a
    # host would after a working session, plus a resume context block.
    payload["memory"] = [
        {
            "id": "00000000-0000-4000-a000-000000000001",
            "ts": "2026-05-26T09:00:00Z",
            "role": "user",
            "content": "We are wiring .klickd memory into a LangGraph agent.",
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
        "current_project": "klickd LangChain/LangGraph bridge",
        "current_state": "bridge drafted; verifying cross-session resume",
        "resume_trigger": "user says 'continue'",
    }

    # Persist an encrypted portable profile via the SDK. The passphrase is
    # demo-only (throwaway temp file); a real carrier supplies their own.
    file_bytes = save_klickd(payload, _DEMO_PASSPHRASE, domain="software_engineering")
    out_path.write_bytes(file_bytes)
    print(f"saved encrypted portable profile -> {out_path} ({len(file_bytes)} bytes)\n")


def session_two(in_path: Path) -> None:
    """Fresh load: rebuild messages + state from the saved profile."""
    print("=== Session 2: load + resume ===")
    mem = KlickdMemory.from_path(in_path, passphrase=_DEMO_PASSPHRASE)

    if mem.schema_warnings:
        print(f"(non-fatal schema findings: {len(mem.schema_warnings)})")

    print("\n-- resume context --")
    print(json.dumps(mem.resume_context(), indent=2))

    print("\n-- LangChain messages (role, content) --")
    for role, content in mem.to_messages():
        preview = content if len(content) <= 100 else content[:97] + "..."
        print(f"  [{role}] {preview}")

    print("\n-- LangGraph state --")
    state = mem.to_langgraph_state()
    print(f"  messages: {len(state['messages'])}")
    print(f"  klickd.resume: {state['klickd'].get('resume')}")
    print(f"  klickd.verification_gates: {state['klickd'].get('verification_gates')}")
    print(f"  klickd.human_authority: {state['klickd'].get('human_authority')}")

    _maybe_run_langchain(mem)
    _maybe_run_langgraph(mem)


def _maybe_run_langchain(mem: KlickdMemory) -> None:
    try:
        import langchain_core  # noqa: F401
    except ImportError:
        print("\n(langchain-core not installed — skipping real message objects)")
        return
    msgs = mem.to_lc_messages()
    print(f"\n-- langchain-core message objects: {len(msgs)} "
          f"({type(msgs[0]).__name__} first) --")


def _maybe_run_langgraph(mem: KlickdMemory) -> None:
    try:
        from langgraph.graph import END, START, StateGraph  # type: ignore
        from typing_extensions import TypedDict
    except ImportError:
        print("(langgraph not installed — skipping graph demo)")
        return

    class S(TypedDict):
        messages: list
        klickd: dict

    def resume_node(state: S) -> S:
        # A real node would call an LLM here, honoring state["klickd"] gates
        # in the HOST (not the model). We just confirm the state arrived.
        return state

    graph = StateGraph(S)
    graph.add_node("resume", resume_node)
    graph.add_edge(START, "resume")
    graph.add_edge("resume", END)
    app = graph.compile()
    result = app.invoke(mem.to_langgraph_state())
    print(f"\n-- langgraph run ok: {len(result['messages'])} messages in state --")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp) / "resume.klickd"
        session_one(profile)
        session_two(profile)
    print("\nDone. Context resumed across sessions from a portable .klickd file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
