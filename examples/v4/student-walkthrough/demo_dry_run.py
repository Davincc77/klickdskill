#!/usr/bin/env python3
"""demo_dry_run — print provider request payloads without any network calls.

Loads `student-multi-provider.klickd`, builds the canonical .klickd system
prompt with the shared helper, and emits the exact `messages` / `system`
payload each of OpenAI, Anthropic, Groq, and xAI Grok would receive. No
SDKs are imported, no environment variables are read, no API keys are
required, no sockets are opened.

Use this for screen-recording the "one profile, four providers" demo
when you do not want to spend (or expose) real credentials, and for
docs/CI checks that the same `.klickd` drives every provider.

Run:

    PYTHONPATH=packages/pypi/klickd/src \\
        python examples/v4/student-walkthrough/demo_dry_run.py

Optional flags:

    --profile PATH    Override the .klickd file (default: bundled student profile)
    --user MSG        Override the user message
    --provider NAME   Print only one provider (openai|anthropic|groq|xai|all)
    --json            Emit a single JSON object instead of pretty sections

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
DEFAULT_PROFILE = HERE / "student-multi-provider.klickd"
DEFAULT_USER_MSG = "I'm stuck — sin(x²). What do I do with the inside?"

PROVIDERS: dict[str, dict[str, str]] = {
    "openai":    {"label": "OpenAI",          "model": "gpt-4o",                    "shape": "openai"},
    "anthropic": {"label": "Anthropic Claude","model": "claude-opus-4-5",           "shape": "anthropic"},
    "groq":      {"label": "Groq",            "model": "llama-3.3-70b-versatile",   "shape": "openai"},
    "xai":       {"label": "xAI Grok",        "model": "grok-2-latest",             "shape": "openai"},
}


def _import_helper() -> Any:
    """Import the shared system-prompt builder without requiring `pip install`."""
    helper_path = REPO / "examples" / "v4" / "integrations" / "langchain" / "klickd_langchain.py"
    spec = importlib.util.spec_from_file_location("klickd_langchain_helper", str(helper_path))
    assert spec and spec.loader, f"could not load {helper_path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_request(shape: str, model: str, system_prompt: str, user_message: str) -> dict[str, Any]:
    """Return the JSON the provider SDK would send — no network call."""
    if shape == "openai":
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        }
    if shape == "anthropic":
        return {
            "model": model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }
    raise ValueError(f"unknown provider shape: {shape}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    p.add_argument("--user", default=DEFAULT_USER_MSG)
    p.add_argument("--provider", default="all",
                   choices=["all", *PROVIDERS.keys()])
    p.add_argument("--json", action="store_true",
                   help="emit a single JSON object instead of pretty sections")
    args = p.parse_args(argv)

    if not args.profile.is_file():
        print(f"ERROR: profile not found: {args.profile}", file=sys.stderr)
        return 2

    helper = _import_helper()
    payload = helper.load_klickd_path(args.profile)
    system_prompt = helper.klickd_to_system_prompt(payload)

    selected = list(PROVIDERS.items()) if args.provider == "all" else [
        (args.provider, PROVIDERS[args.provider])
    ]

    out: dict[str, Any] = {
        "profile": str(args.profile),
        "user_message": args.user,
        "system_prompt": system_prompt,
        "providers": {},
    }
    for name, info in selected:
        out["providers"][name] = {
            "label": info["label"],
            "model": info["model"],
            "request": build_request(info["shape"], info["model"], system_prompt, args.user),
        }

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(f"# .klickd dry-run — {args.profile.name}")
    print(f"# user_message: {args.user}")
    print()
    print("## system_prompt (built from .klickd, identical for all providers)")
    print()
    print(system_prompt)
    print()
    for name, info in selected:
        print(f"## {info['label']} — model={info['model']}")
        print()
        print(json.dumps(out["providers"][name]["request"], indent=2, ensure_ascii=False))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
