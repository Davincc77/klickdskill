#!/usr/bin/env python3
"""
load_klickd.py — .klickd v2 decrypt + memory write
Part of the .klickd open standard (CC0)
https://github.com/Davincc77/klickdskill

Usage:
  python load_klickd.py <file.klickd> <passphrase>
  python load_klickd.py <file.klickd> --no-passphrase   # for encrypted: false files
  echo '{"klickd_version":"2.0",...}' | python load_klickd.py - <passphrase>

Output:
  Writes decrypted fields to /.memory/ (or KLICKD_MEMORY_DIR env var)
  Prints agent_instructions to stdout for system prompt injection
  Exits 0 on success, non-zero on failure
"""

import sys
import os
import json
import base64
import argparse

MEMORY_DIR = os.environ.get("KLICKD_MEMORY_DIR", "/.memory/")


# ── Decryption ────────────────────────────────────────────────────────────────

def decrypt_payload(envelope: dict, passphrase: str) -> dict:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        sys.exit("ERROR: pip install cryptography")

    assert envelope.get("klickd_version") == "2.0", \
        f"Unsupported version: {envelope.get('klickd_version')}"

    salt = base64.b64decode(envelope["salt"])
    iv   = base64.b64decode(envelope["iv"])
    raw  = base64.b64decode(envelope["payload"])

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = kdf.derive(passphrase.encode("utf-8"))

    aesgcm    = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, raw, None)
    return json.loads(plaintext.decode("utf-8"))


def load_payload(envelope: dict, passphrase: str | None) -> dict:
    if envelope.get("encrypted") is False:
        raw = envelope.get("payload")
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)
    if not passphrase:
        sys.exit("ERROR: file is encrypted — provide a passphrase")
    return decrypt_payload(envelope, passphrase)


# ── Memory write ──────────────────────────────────────────────────────────────

def write_to_memory(payload: dict, memory_dir: str = MEMORY_DIR) -> None:
    os.makedirs(memory_dir, exist_ok=True)

    # identity.json
    identity = payload.get("identity", {})
    if identity:
        _write_json(memory_dir, "identity.json", {
            "name":                identity.get("name"),
            "language":            identity.get("language"),
            "timezone":            identity.get("timezone"),
            "communication_style": identity.get("communication_style"),
        })

    # agent_instructions.txt
    instructions = payload.get("agent_instructions", "")
    if instructions:
        with open(os.path.join(memory_dir, "agent_instructions.txt"), "w") as f:
            f.write(instructions)

    # context.json
    context = payload.get("context", {})
    if context:
        _write_json(memory_dir, "context.json", {
            "current_state":    context.get("current_state"),
            "decisions_locked": context.get("decisions_locked", []),
            "artifacts":        context.get("artifacts", []),
            "summary":          context.get("summary"),
        })

    # knowledge.json
    knowledge = payload.get("knowledge", {})
    if knowledge:
        _write_json(memory_dir, "knowledge.json", knowledge)

    # {domain}_profile.json
    domain = payload.get("domain")
    if domain and domain != "general":
        domain_data = payload.get(f"{domain}_profile", {})
        if domain_data:
            _write_json(memory_dir, f"{domain}_profile.json", domain_data)


def _write_json(directory: str, filename: str, data: dict) -> None:
    with open(os.path.join(directory, filename), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=".klickd v2 — decrypt and write to agent memory"
    )
    parser.add_argument(
        "file",
        help="Path to .klickd file, or '-' to read from stdin"
    )
    parser.add_argument(
        "passphrase",
        nargs="?",
        default=None,
        help="Decryption passphrase (omit for encrypted: false files)"
    )
    parser.add_argument(
        "--no-passphrase",
        action="store_true",
        help="Explicitly skip passphrase (for encrypted: false files)"
    )
    parser.add_argument(
        "--memory-dir",
        default=MEMORY_DIR,
        help=f"Memory directory (default: {MEMORY_DIR})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Decrypt and print payload without writing to memory"
    )
    args = parser.parse_args()

    # Read file
    if args.file == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.exists(args.file):
            sys.exit(f"ERROR: file not found: {args.file}")
        with open(args.file) as f:
            raw = f.read()

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: invalid JSON: {e}")

    # Resolve passphrase
    passphrase = None if args.no_passphrase else args.passphrase

    # Load + decrypt
    try:
        payload = load_payload(envelope, passphrase)
    except Exception as e:
        sys.exit(f"ERROR: decryption failed — {e}")

    # Dry run
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    # Write to memory
    write_to_memory(payload, args.memory_dir)

    # Print agent_instructions for system prompt injection
    instructions = payload.get("agent_instructions", "")
    if instructions:
        print(instructions)

    print(f"\n[.klickd loaded → {args.memory_dir}]", file=sys.stderr)


if __name__ == "__main__":
    main()
