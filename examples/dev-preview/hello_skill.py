#!/usr/bin/env python3
"""Dev-preview smoke test: load one x.klickd skill as model context.

No API key, no account, no network, no passphrase. This proves the SDK is
installed and can turn a bundled `.klickd` artifact into structured context
that an agent could drop into a system prompt.

Run:
    python examples/dev-preview/hello_skill.py

Exit code 0 = the SDK loaded a starter skill and a v4.1 skill pack and the
pack's bytes hash-verified against the published manifest.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        import klickd
    except ModuleNotFoundError:
        print(
            "klickd is not installed. From a fresh clone run:\n"
            "    python -m venv .venv && source .venv/bin/activate\n"
            "    pip install -e .",
            file=sys.stderr,
        )
        return 1

    print(f"klickd SDK version: {klickd.__version__}")

    # 1. A starter skill is a plain (unencrypted) payload on purpose, so it
    #    parses with plain JSON -- no passphrase, no LLM call.
    payload = json.loads(klickd.get_starter_skill_bytes("coding.klickd"))
    pack = payload["x_klickd_pack"]
    assert payload["encrypted"] is False, "starter skills are plain payloads"
    assert pack["pack"] == "x.klickd/coding"
    print(f"Loaded starter skill: {pack['pack']} (encrypted={payload['encrypted']})")

    # 2. Load one of the 42 v4.1 candidate skill packs and hash-verify it
    #    against the manifest. `artifact_loaded` only means the bytes were
    #    read and hashed in-process -- it does NOT mean any assistant has
    #    natively adopted the pack.
    skill = klickd.load_xklickd_skill_pack("llm-agent-engineering")
    assert skill["artifact_loaded"], "pack bytes were not loaded"
    assert skill["sha256_matches_manifest"], "pack hash did not match manifest"
    print(
        f"Loaded + hash-verified skill pack: {skill['pack']} "
        f"(tier={skill['tier']}, bytes={skill['bytes']})"
    )

    print("\nOK: dev-preview smoke test passed (no API key required).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
