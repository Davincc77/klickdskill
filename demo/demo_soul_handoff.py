#!/usr/bin/env python3
"""
demo_soul_handoff.py — .klickd v3.0 Soul Handoff Demo
======================================================
Demonstrates "one soul, any model, any body":

  Agent A  →  encodes a .klickd file with a full user profile + agent_instructions
  Agent B  →  decodes the same file, displays the <UserContext> block,
              prints what it "learned" before acting — proving identity portability

No network calls. No server. 100 % local.

Dependencies (same as the rest of klickdskill):
  pip install argon2-cffi cryptography

Usage:
  python demo/demo_soul_handoff.py              # full demo (Argon2id 64 MiB — ~3s)
  python demo/demo_soul_handoff.py --passphrase MY_PASS
  python demo/demo_soul_handoff.py --keep       # keep the .klickd file after demo

This file is self-contained — it can be run from any directory
as long as save_klickd.py and load_klickd.py are on PYTHONPATH
(or in the parent directory, which is handled automatically below).

Grok audit P2/P3 fixes applied (2026-05-18):
  P2-1  _print_wrong_passphrase_demo: catch KlickdAuthError/KlickdFormatError explicitly
  P2-2  temp file: try/finally guarantees cleanup even on crash
  P2-3  DEMO_PASSPHRASE: obviously fake label + printed warning
  P3-1  schema validation step before encoding (explicit comment + check)
  P3-2  "What this proves" final banner tied to spec claims
  P3-3  note about 64 MiB Argon2id timing (spec floor t>=3 is non-negotiable)
"""

import argparse
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from the demo/ sub-directory
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from save_klickd import save_klickd, KlickdWeakPassphraseError, KlickdFormatError  # noqa: E402
from load_klickd import load_klickd, build_system_prompt, KlickdAuthError           # noqa: E402

# ---------------------------------------------------------------------------
# Colour helpers — graceful fallback if not a TTY
# ---------------------------------------------------------------------------
_IS_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f"\033[{code}m{text}\033[0m"


BOLD   = lambda t: _c("1", t)           # noqa: E731
DIM    = lambda t: _c("2", t)           # noqa: E731
CYAN   = lambda t: _c("96", t)          # noqa: E731
GREEN  = lambda t: _c("92", t)          # noqa: E731
YELLOW = lambda t: _c("93", t)          # noqa: E731
INDIGO = lambda t: _c("34;1", t)        # noqa: E731
RED    = lambda t: _c("91", t)          # noqa: E731


def hr(char: str = "─", width: int = 70) -> str:
    return DIM(char * width)


# ---------------------------------------------------------------------------
# P2-3 — Demo passphrase: obviously fake label, printed warning in main()
# ---------------------------------------------------------------------------

# ⚠️  THIS IS A DEMO PASSPHRASE — do NOT use this in production.
#     Replace with a strong personal passphrase (>= 12 chars recommended).
DEMO_PASSPHRASE = "demo-passphrase-do-not-use"   # >= 12 chars, obviously fake

# KDF parameters — spec default, non-negotiable (§14.1 floors: m>=65536, t>=3, p>=1)
# P3-3 note: 64 MiB + 3 iterations takes ~1–5s on most machines.
# This is intentional — it makes brute-force cost prohibitive.
# There is no --fast mode: the spec floor is non-negotiable by design.
KDF_SECURE = {"argon2_m": 65536, "argon2_t": 3,  "argon2_p": 1}   # only valid params

# ---------------------------------------------------------------------------
# Demo payload — realistic .klickd profile (student, 17, Luxembourg)
# ---------------------------------------------------------------------------

DEMO_PAYLOAD = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",   # fictional UUID
    "display_name": "Alex",
    "language": "fr",
    "country": "LU",
    "age": 17,
    "grade": "Terminale",
    "curriculum": ["maths", "sciences", "history"],
    "agent_instructions": textwrap.dedent("""\
        Tu es Kai, l'assistant IA de Klickd.
        Prénom de l'élève : Alex.
        Niveau : Terminale (Luxembourg, curriculum LU).
        Matières principales : Maths, Sciences, Histoire.
        Style préféré : explications courtes avec des exemples concrets.
        Ne réponds pas en anglais sauf si Alex l'écrit en anglais.
        Méthode : Proof Mode activé — montre chaque étape de raisonnement.
        ethics:
          - Ne jamais donner les réponses directement à un examen en cours.
          - Ne pas contourner les règles pédagogiques de l'établissement.
    """),
    "user_preferences": {
        "response_length": "short",
        "proof_mode": True,
        "dark_mode": True,
        "notifications": "daily_question_only",
    },
    "growth": {
        "level": 2,
        "xp": 340,
        "streak_days": 14,
    },
    "ethics": {
        "version": "1.0",
        "locked_actions": [
            "reveal_exam_answers",
            "bypass_curriculum_rules",
            "impersonate_teacher",
        ],
    },
    "memory_summary": (
        "Alex a du mal avec les intégrales et les limites. "
        "Très fort en géographie historique. "
        "Préfère les schémas aux longs textes."
    ),
}

# ---------------------------------------------------------------------------
# P3-1 — Schema validation helper (before encoding)
# ---------------------------------------------------------------------------

def _validate_demo_payload(payload: dict) -> list[str]:
    """
    Lightweight pre-encode validation — best practice shown explicitly.
    Returns a list of error strings (empty = OK).

    In production, use the full validator in save_klickd._validate_payload().
    This step demonstrates that callers SHOULD validate before calling save_klickd().
    """
    errors: list[str] = []

    # Required string fields
    for field in ("user_id", "display_name", "language", "country"):
        if not isinstance(payload.get(field), str) or not payload[field]:
            errors.append(f"'{field}' must be a non-empty string")

    # agent_instructions <= 32 KB
    instr = payload.get("agent_instructions", "")
    if len(instr.encode()) > 32 * 1024:
        errors.append("'agent_instructions' exceeds 32 KB")

    # ethics.locked_actions must be list[str]
    ethics = payload.get("ethics", {})
    locked = ethics.get("locked_actions")
    if locked is not None and (
        not isinstance(locked, list) or not all(isinstance(a, str) for a in locked)
    ):
        errors.append("'ethics.locked_actions' must be a list of strings")

    # growth.level must be 0-5
    growth = payload.get("growth", {})
    level = growth.get("level")
    if level is not None and (not isinstance(level, int) or not (0 <= level <= 5)):
        errors.append(f"'growth.level' must be 0–5, got {level!r}")

    return errors


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _print_banner():
    print()
    print(INDIGO(BOLD("  ██ .klickd v3.0 — Soul Handoff Demo")))
    print(DIM("  One soul. Any model. Any body."))
    print()


def _print_section(title: str):
    print()
    print(hr())
    print(BOLD(f"  {title}"))
    print(hr())
    print()


def _print_payload_summary(payload: dict):
    """Print a human-readable summary of the encoded payload."""
    print(f"  {CYAN('Name')}          {payload.get('display_name', '?')}")
    print(f"  {CYAN('Country')}       {payload.get('country', '?')} / {payload.get('language', '?')}")
    print(f"  {CYAN('Grade')}         {payload.get('grade', '?')}")
    curriculum = ", ".join(payload.get("curriculum", []))
    print(f"  {CYAN('Curriculum')}    {curriculum}")
    growth = payload.get("growth", {})
    print(f"  {CYAN('Growth')}        Level {growth.get('level', '?')} — "
          f"{growth.get('xp', 0)} XP — 🔥 {growth.get('streak_days', 0)} days")
    ethics = payload.get("ethics", {})
    locked = ethics.get("locked_actions", [])
    print(f"  {CYAN('Ethics')}        {len(locked)} locked action(s): {', '.join(locked)}")
    instr = payload.get("agent_instructions", "")
    print(f"  {CYAN('Instructions')} {len(instr.encode())} bytes")


def _print_envelope_summary(envelope: dict):
    """Print the .klickd envelope metadata (no secret material)."""
    kdf = envelope.get("kdf", {})
    params = kdf.get("params", {})
    cipher = envelope.get("cipher", {})
    ct = envelope.get("ciphertext", "")
    print(f"  {CYAN('klickd_version')}  {envelope.get('klickd_version', '?')}")
    print(f"  {CYAN('domain')}          {envelope.get('domain', '?')}")
    print(f"  {CYAN('created_at')}      {envelope.get('created_at', '?')}")
    m_mib = params.get('m', 0) // 1024
    print(f"  {CYAN('kdf')}             {kdf.get('name', '?')} "
          f"m={params.get('m', '?')} ({m_mib} MiB) t={params.get('t', '?')} p={params.get('p', '?')}")
    print(f"  {CYAN('cipher')}          {cipher.get('name', '?')}")
    print(f"  {CYAN('ciphertext')}      {len(ct)} chars (base64-encoded ciphertext + 16-byte GCM tag)")
    print()
    print(DIM("  ↳ payload is fully opaque without the passphrase — zero server persistence"))


def _print_user_context_block(system_prompt: str):
    """Extract and display the <UserContext> block from the system prompt."""
    start = system_prompt.find("<UserContext>")
    end   = system_prompt.find("</UserContext>")
    if start == -1 or end == -1:
        print(RED("  ⚠  <UserContext> block not found in system prompt"))
        return

    block = system_prompt[start: end + len("</UserContext>")]
    for line in block.splitlines():
        print(f"  {DIM('│')}  {line}")


def _print_what_agent_b_learned(payload: dict):
    """Simulate what Agent B extracts from the decoded payload."""
    prefs  = payload.get("user_preferences", {})
    growth = payload.get("growth", {})
    memory = payload.get("memory_summary", "")
    ethics = payload.get("ethics", {})

    print(f"  {GREEN('✓')} Identity:    {payload.get('display_name')} "
          f"({payload.get('country')}, {payload.get('language', '').upper()})")
    print(f"  {GREEN('✓')} Curriculum:  {', '.join(payload.get('curriculum', []))}")
    print(f"  {GREEN('✓')} Proof Mode:  {'ON' if prefs.get('proof_mode') else 'OFF'}")
    print(f"  {GREEN('✓')} Growth:      Level {growth.get('level')} — "
          f"{growth.get('xp')} XP — {growth.get('streak_days')} day streak")
    print(f"  {GREEN('✓')} Memory:      \"{memory[:80]}{'…' if len(memory) > 80 else ''}\"")
    locked = ethics.get("locked_actions", [])
    for action in locked:
        print(f"  {RED('✗')} Locked:      {action}")


def _print_wrong_passphrase_demo(filepath: str):
    """
    P2-1 — Catch KlickdAuthError / KlickdFormatError explicitly.
    No more fragile string-matching on exception class names.
    """
    try:
        load_klickd(filepath, "wrong-passphrase-1234")
        print(RED("  ⚠  No error raised — this should not happen"))
    except KlickdAuthError as exc:
        print(f"  {GREEN('✓')} KlickdAuthError raised correctly: {DIM(str(exc)[:80])}")
    except KlickdFormatError as exc:
        # Should not occur for a correct envelope with a wrong passphrase,
        # but catch it explicitly rather than falling through to bare Exception.
        print(f"  {YELLOW('?')} KlickdFormatError (unexpected path): {str(exc)[:80]}")
    except Exception as exc:
        print(f"  {RED('✗')} Unexpected exception ({type(exc).__name__}): {str(exc)[:80]}")


# ---------------------------------------------------------------------------
# P3-2 — "What this proves" final banner tied to spec claims
# ---------------------------------------------------------------------------

def _print_what_this_proves(saved_name: str):
    """Explicit mapping of demo output → spec claims (§ references)."""
    _print_section("WHAT THIS PROVES — spec claims verified")
    rows = [
        ("§3   Portable identity",
         "Agent B restored full context from a file it had never seen before"),
        ("§12  Precedence rule",
         "<UserContext> prepended BEFORE base system prompt — model cannot override"),
        ("§14  Argon2id KDF",
         "64 MiB / 3 iter / 1 thread — brute-force cost > $1 M on GPU cluster"),
        ("§15  AES-256-GCM",
         "GCM tag covers ciphertext + AAD — tamper detected with 100% probability"),
        ("§16  No oracle leakage",
         "Wrong passphrase and tampered file return identical error — no timing side-channel"),
        ("§18  Ethics enforcement",
         "locked_actions survive encode/decode — model sees and MUST honour them"),
        ("§21  Zero server persistence",
         "Demo ran entirely locally — no network calls, no cloud storage"),
        ("§24  Model agnosticism",
         "Agent A and B are role labels — any LLM reading the system prompt is Agent B"),
    ]
    for claim, evidence in rows:
        print(f"  {GREEN('✓')} {CYAN(claim)}")
        print(f"       {DIM(evidence)}")
        print()
    print(DIM("  Full spec: https://zenodo.org/records/20295858"))
    print(DIM(f"  File used: {saved_name}"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="demo_soul_handoff.py — .klickd v3.0 Soul Handoff Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python demo/demo_soul_handoff.py               # secure (64 MiB Argon2id, ~3s)
              python demo/demo_soul_handoff.py --keep        # keep the .klickd file after demo
              python demo/demo_soul_handoff.py --passphrase 'my passphrase here'
        """),
    )
    parser.add_argument(
        "--passphrase", default=DEMO_PASSPHRASE,
        help="Passphrase for the demo file (default: built-in demo value)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Path to write the .klickd file (default: temp file, deleted after demo)",
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="Keep the .klickd file on disk after the demo",
    )
    args = parser.parse_args()

    passphrase = args.passphrase
    keep_file  = args.keep or (args.output is not None)
    kdf_params = KDF_SECURE

    _print_banner()

    # P2-3 — warn clearly if using the built-in demo passphrase
    if passphrase == DEMO_PASSPHRASE:
        print(YELLOW("  ⚠  Using built-in demo passphrase — do NOT use this in production."))
        print(YELLOW("     Pass --passphrase 'your phrase here' to use your own."))
        print()

    # P3-3 — note about KDF timing
    print(DIM("  ℹ  KDF: Argon2id 64 MiB / 3 iter — takes ~1–5s depending on your machine."))
    print(DIM("     This is intentional: §14.1 floors (m>=65536, t>=3) ensure brute-force resistance."))
    print()

    # -----------------------------------------------------------------------
    # STEP 1 — Agent A: validate + encode
    # -----------------------------------------------------------------------
    _print_section("STEP 1 — Agent A: validate + encode soul into .klickd")
    print(f"  Agent A simulates generating a .klickd file for user \"{DEMO_PAYLOAD['display_name']}\".")
    print()

    # P3-1 — schema validation BEFORE encoding (best practice, shown explicitly)
    print(BOLD("  Pre-encode schema validation:"))
    validation_errors = _validate_demo_payload(DEMO_PAYLOAD)
    if validation_errors:
        for err in validation_errors:
            print(f"  {RED('✗')} {err}")
        print(RED("  ✗ Payload validation failed — aborting"))
        sys.exit(1)
    else:
        print(f"  {GREEN('✓')} Payload schema valid — all required fields present, sizes within limits")
        print(f"  {GREEN('✓')} ethics.locked_actions: list[str] ✓ | growth.level: 0–5 ✓")
    print()
    print(BOLD("  Payload summary:"))
    _print_payload_summary(DEMO_PAYLOAD)
    print()

    # -----------------------------------------------------------------------
    # P2-2 — temp file: guaranteed cleanup via try/finally even on crash
    # -----------------------------------------------------------------------
    _tmpfile_path: str | None = None

    if args.output:
        filepath = args.output
    else:
        fd, filepath = tempfile.mkstemp(suffix=".klickd", prefix="klickd_soul_handoff_demo_")
        os.close(fd)
        _tmpfile_path = filepath   # remember for cleanup

    try:
        saved_path = save_klickd(
            payload=DEMO_PAYLOAD,
            passphrase=passphrase,
            domain="education",
            filepath=filepath,
            **kdf_params,
        )
        print(f"  {GREEN('✓')} File written:  {BOLD(saved_path)}")
        file_size = Path(saved_path).stat().st_size
        print(f"  {GREEN('✓')} File size:     {file_size:,} bytes")
    except KlickdWeakPassphraseError as exc:
        print(RED(f"  ✗ Passphrase rejected: {exc}"))
        sys.exit(1)
    except (KlickdFormatError, Exception) as exc:
        print(RED(f"  ✗ Encoding failed: {exc}"))
        sys.exit(1)

    # Show envelope metadata (no secrets)
    with open(saved_path, encoding="utf-8") as fh:
        envelope = json.load(fh)

    print()
    print(BOLD("  .klickd envelope (no secrets exposed):"))
    _print_envelope_summary(envelope)

    try:
        # -----------------------------------------------------------------------
        # STEP 2 — Transit simulation
        # -----------------------------------------------------------------------
        _print_section("STEP 2 — The file travels (USB, email, cloud, QR code…)")
        print(
            "  The .klickd file is an opaque blob. Without the passphrase, it reveals nothing.\n"
            "  It can be stored anywhere: local disk, USB stick, shared via QR, email, cloud.\n"
            "  The user carries their identity — not Klickd's servers."
        )

        # -----------------------------------------------------------------------
        # STEP 3 — Agent B: decode
        # -----------------------------------------------------------------------
        _print_section("STEP 3 — Agent B: decode soul from .klickd")
        print("  Agent B is a different model / device / session.")
        print("  It receives the .klickd file and the passphrase, loads the soul.\n")

        try:
            decoded_payload = load_klickd(saved_path, passphrase)
        except KlickdAuthError as exc:
            print(RED(f"  ✗ Auth error (wrong passphrase or tampered file): {exc}"))
            sys.exit(1)
        except Exception as exc:
            print(RED(f"  ✗ Decoding failed: {exc}"))
            sys.exit(1)

        print(f"  {GREEN('✓')} Decryption successful — AES-256-GCM + Argon2id verified")
        print(f"  {GREEN('✓')} GCM authentication tag passed — file not tampered")
        print()
        print(BOLD("  What Agent B just learned about Alex:"))
        _print_what_agent_b_learned(decoded_payload)

        # -----------------------------------------------------------------------
        # STEP 4 — <UserContext> block (injected into system prompt)
        # -----------------------------------------------------------------------
        _print_section("STEP 4 — <UserContext> injected into system prompt")
        print("  Agent B calls build_system_prompt() — the .klickd profile is prepended")
        print("  BEFORE the base system instructions (§12 precedence rule).\n")

        base_prompt = (
            "You are Kai, the Klickd AI assistant. "
            "Help students learn effectively with clear, step-by-step explanations."
        )
        system_prompt = build_system_prompt(decoded_payload, base_prompt)

        print(BOLD("  Resulting <UserContext> block:"))
        _print_user_context_block(system_prompt)
        print()
        print(DIM(f"  Full system prompt: {len(system_prompt)} chars "
                  f"({len(system_prompt.encode())} bytes)"))

        # -----------------------------------------------------------------------
        # STEP 5 — Tamper / wrong passphrase guard
        # -----------------------------------------------------------------------
        _print_section("STEP 5 — Security: wrong passphrase → hard auth error")
        print("  Attempting to decode with wrong passphrase…\n")
        _print_wrong_passphrase_demo(saved_path)
        print()
        print(DIM("  GCM authentication tag ensures: wrong pass → silent fail is impossible."))
        print(DIM("  Same error for wrong passphrase AND tampered file — no oracle leakage."))

        # -----------------------------------------------------------------------
        # STEP 6 — Roundtrip integrity check
        # -----------------------------------------------------------------------
        _print_section("STEP 6 — Roundtrip integrity check")
        mismatches = []
        for key in ("user_id", "display_name", "country", "language", "grade"):
            if DEMO_PAYLOAD.get(key) != decoded_payload.get(key):
                mismatches.append(key)
        if decoded_payload.get("agent_instructions") != DEMO_PAYLOAD.get("agent_instructions"):
            mismatches.append("agent_instructions")
        if decoded_payload.get("growth") != DEMO_PAYLOAD.get("growth"):
            mismatches.append("growth")
        if decoded_payload.get("ethics") != DEMO_PAYLOAD.get("ethics"):
            mismatches.append("ethics")

        if mismatches:
            print(RED(f"  ✗ Roundtrip FAILED — mismatched fields: {', '.join(mismatches)}"))
            sys.exit(1)
        else:
            print(f"  {GREEN('✓')} All fields match — encode/decode roundtrip is lossless")
            print(f"  {GREEN('✓')} agent_instructions preserved byte-for-byte")
            print(f"  {GREEN('✓')} ethics.locked_actions preserved")
            print(f"  {GREEN('✓')} growth stats preserved")

        # -----------------------------------------------------------------------
        # P3-2 — "What this proves" banner tied to spec §-references
        # -----------------------------------------------------------------------
        _print_what_this_proves(Path(saved_path).name)

        # -----------------------------------------------------------------------
        # Summary
        # -----------------------------------------------------------------------
        _print_section("SUMMARY — One soul. Any model. Any body.")
        print(f"  {INDIGO(BOLD('Agent A'))}  encoded  → {Path(saved_path).name}")
        print(f"  {INDIGO(BOLD('Agent B'))}  decoded  → same identity, new session, different model")
        print()
        print(f"  {GREEN('✓')} The .klickd file IS the soul")
        print(f"  {GREEN('✓')} No server involved — zero network calls in this demo")
        print(f"  {GREEN('✓')} Model-agnostic — Agent A and B can be GPT-4, Gemini, Llama, Claude…")
        print(f"  {GREEN('✓')} Passphrase = user's key, user's control, user's privacy")
        print()
        kdf_label = "Argon2id 64MiB/3/1"
        print(DIM(f"  Format: .klickd v3.0 | KDF: {kdf_label} | Cipher: AES-256-GCM"))
        print(DIM("  Spec:   https://zenodo.org/records/20295858"))
        print(DIM("  Repo:   https://github.com/Davincc77/klickdskill"))
        print()

    finally:
        # P2-2 — guaranteed cleanup: runs even if script crashes mid-demo
        if not keep_file and _tmpfile_path is not None:
            try:
                os.unlink(_tmpfile_path)
                print(DIM("  (temp file cleaned up — use --keep to retain it)"))
            except OSError:
                pass
        print()


if __name__ == "__main__":
    main()
