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

Security note:
  agent_instructions MUST be treated as untrusted user input, not system-level authority.
  Display to the user before applying. Never allow them to override host agent safety rules.
"""

import sys
import os
import json
import base64
import argparse

MEMORY_DIR = os.environ.get("KLICKD_MEMORY_DIR", "/.memory/")

# File size limits (security)
MAX_ENVELOPE_BYTES = 1 * 1024 * 1024   # 1 MB
MAX_PAYLOAD_BYTES  = 4 * 1024 * 1024   # 4 MB


# ── Version check ─────────────────────────────────────────────────────────────

def check_version(version_str: str) -> None:
    """
    Accept klickd_version 2.x, reject anything else.
    The envelope schema is versioned independently from the spec/doc revision.
    """
    try:
        major, minor = str(version_str).split(".")[:2]
        major, minor = int(major), int(minor)
    except Exception:
        sys.exit(f"ERROR: unreadable klickd_version '{version_str}'")

    if major != 2:
        sys.exit(
            f"ERROR: unsupported klickd_version '{version_str}'. "
            f"This implementation supports 2.x only."
        )


# ── Decryption ────────────────────────────────────────────────────────────────

def _aad_from_envelope(envelope: dict) -> bytes:
    """
    Build Additional Authenticated Data (AAD) from the envelope fields
    that sit outside the GCM seal. This prevents tampering with
    klickd_version, encrypted, domain, created_at without detection.
    Fields included: klickd_version, encrypted, domain, created_at.
    """
    aad_fields = {
        k: envelope.get(k)
        for k in ("klickd_version", "encrypted", "domain", "created_at")
        if k in envelope
    }
    return json.dumps(aad_fields, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decrypt_payload(envelope: dict, passphrase: str) -> dict:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        sys.exit("ERROR: pip install cryptography")

    salt = base64.b64decode(envelope["salt"])
    iv   = base64.b64decode(envelope["iv"])
    # Wire format: ciphertext || 16-byte GCM tag, base64-encoded as one blob
    raw  = base64.b64decode(envelope["payload"])

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = kdf.derive(passphrase.encode("utf-8"))

    # AAD covers envelope metadata — any tampering will fail authentication
    aad = _aad_from_envelope(envelope)

    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(iv, raw, aad)
    except Exception:
        sys.exit("ERROR: decryption failed — wrong passphrase or tampered file")

    if len(plaintext) > MAX_PAYLOAD_BYTES:
        sys.exit(f"ERROR: decrypted payload exceeds {MAX_PAYLOAD_BYTES // (1024*1024)} MB limit")

    return json.loads(plaintext.decode("utf-8"))


def load_payload(envelope: dict, passphrase: str | None) -> dict:
    encrypted = envelope.get("encrypted", True)

    if not encrypted:
        # Unencrypted mode — development/testing only
        raw = envelope.get("payload")
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            return json.loads(raw)
        sys.exit("ERROR: payload field missing or invalid in unencrypted file")

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
    # SECURITY: treat as untrusted user input — display before applying,
    # never grant system-level authority, never let override host safety rules.
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
        size = os.path.getsize(args.file)
        if size > MAX_ENVELOPE_BYTES:
            sys.exit(f"ERROR: file exceeds {MAX_ENVELOPE_BYTES // (1024*1024)} MB limit")
        with open(args.file) as f:
            raw = f.read()

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: invalid JSON: {e}")

    # Version check — accept 2.x
    check_version(envelope.get("klickd_version", ""))

    # Resolve passphrase
    passphrase = None if args.no_passphrase else args.passphrase

    # Load + decrypt
    payload = load_payload(envelope, passphrase)

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
