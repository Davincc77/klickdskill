#!/usr/bin/env python3
"""load_klickd.py v2.5 — PBKDF2 + 4-field AAD (v2.x); Argon2id + RFC 8785 JCS (v3.0)

Security patches applied (Bankr audit 2026-05-18):
  CRITICAL 1.3b / 6.2 — Argon2id/PBKDF2 minimum parameter floor enforced
  HIGH     2.2b       — </UserContext> tag escape in build_system_prompt()
  HIGH     2.3a       — envelope 1MB + payload 4MB size limits enforced
  MEDIUM   1.5        — base64.b64decode(validate=True) at all call sites
  MEDIUM   2.1a       — klickd_version must be string matching \d+\.\d+
  MEDIUM   4.1c       — memory_path removed from user-controlled fields
"""
import json, base64, os, re, sys, warnings
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    raise ImportError("pip install cryptography")

try:
    import jcs
    JCS_AVAILABLE = True
except ImportError:
    JCS_AVAILABLE = False
    warnings.warn("jcs not installed — v2.x compat only. pip install jcs for v3.0 support.")

try:
    from argon2.low_level import hash_secret_raw, Type
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False


class KlickdError(Exception): pass
class KlickdAuthError(KlickdError): pass
class KlickdVersionError(KlickdError): pass
class KlickdFormatError(KlickdError): pass
class KlickdWeakPassphraseError(KlickdError): pass

SUPPORTED_MAJOR     = {"2", "3"}
MIN_PASSPHRASE_LEN  = 8
WARN_PASSPHRASE_LEN = 12
_VERSION_RE         = re.compile(r"^\d+\.\d+$")
_GCM_TAG_BYTES      = 16

# Bankr CRITICAL — minimum KDF parameter floors (both encoder and decoder MUST enforce)
_ARGON2_MIN = {"m": 65536, "t": 3, "p": 1}
_PBKDF2_MIN_ITER = 600_000

# File size limits (Bankr HIGH 2.3a)
_MAX_ENVELOPE_BYTES = 1 * 1024 * 1024   # 1 MB
_MAX_PAYLOAD_BYTES  = 4 * 1024 * 1024   # 4 MB
_MAX_AGENT_INSTR_BYTES = 32 * 1024      # 32 KB


def _b64decode_strict(value: str, field_name: str) -> bytes:
    """base64.b64decode with validate=True — rejects URL-safe and non-padded input (Bankr 1.5)."""
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        raise KlickdFormatError(f"KLICKD_E_FORMAT: malformed base64 in {field_name!r}")


def _canonical_aad_v2(envelope: dict) -> bytes:
    """v2.x AAD: 4 fields, Python json.dumps canonical."""
    fields = {k: envelope[k] for k in ("created_at", "domain", "encrypted", "klickd_version")}
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _canonical_aad_v3(envelope: dict) -> bytes:
    """v3.0 AAD: 6 fields (incl kdf+cipher blocks), RFC 8785 JCS."""
    if not JCS_AVAILABLE:
        raise KlickdFormatError("v3.0 requires RFC 8785 JCS: pip install jcs")
    fields = {k: envelope[k] for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")}
    return jcs.canonicalize(fields)


def _derive_key_v2(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)
    return kdf.derive(passphrase.encode("utf-8"))


def _validate_argon2_params(params: dict) -> None:
    """Bankr CRITICAL 1.3b/6.2 — reject files with sub-minimum Argon2id params."""
    for param, minimum in _ARGON2_MIN.items():
        val = params.get(param)
        if not isinstance(val, int) or val < minimum:
            raise KlickdFormatError(
                f"KLICKD_E_KDF: kdf.params.{param}={val!r} below minimum {minimum}"
            )


def _derive_key_v3(passphrase: str, kdf_block: dict) -> bytes:
    name = kdf_block.get("name", "argon2id")
    salt = _b64decode_strict(kdf_block["salt"], "kdf.salt")
    if name == "argon2id":
        if not ARGON2_AVAILABLE:
            raise KlickdFormatError("Argon2id requires: pip install argon2-cffi")
        params = kdf_block.get("params", {})
        _validate_argon2_params(params)  # CRITICAL: enforce minimum floor
        return hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=params["t"],
            memory_cost=params["m"],
            parallelism=params["p"],
            hash_len=32,
            type=Type.ID,
        )
    elif name == "pbkdf2-sha256":
        iterations = kdf_block.get("params", {}).get("iterations", 0)
        # Bankr CRITICAL: enforce minimum iterations floor
        if not isinstance(iterations, int) or iterations < _PBKDF2_MIN_ITER:
            raise KlickdFormatError(
                f"KLICKD_E_KDF: pbkdf2 iterations={iterations!r} below minimum {_PBKDF2_MIN_ITER}"
            )
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
        return kdf.derive(passphrase.encode("utf-8"))
    else:
        raise KlickdFormatError(f"KLICKD_E_KDF: unsupported kdf.name={name!r}")


def build_system_prompt(klickd_payload: dict, base_system_prompt: str) -> str:
    """
    Inject user_preferences as a <UserContext> block AFTER the base system prompt.

    Bankr HIGH 2.2b: escape </UserContext> tag boundaries to prevent injection.
    Bankr MEDIUM 2.2a: UserContext placed AFTER base prompt (lower weight, reduces jailbreak surface).
    """
    prefs = klickd_payload.get("user_preferences", "") or klickd_payload.get("agent_instructions", "")
    if not prefs:
        return base_system_prompt
    # Sanitize: escape any </UserContext> sequences that would break the tag boundary
    safe_prefs = str(prefs).replace("</UserContext>", "<\\/UserContext>")
    user_context = f"<UserContext>\n{safe_prefs}\n</UserContext>"
    # Base prompt FIRST (higher authority), UserContext appended after
    return f"{base_system_prompt}\n\n---\n\n{user_context}"


def load_klickd(filepath: str, passphrase: str, memory_dir: str = "~/.klickd/memory/") -> dict:
    """
    Decrypt a .klickd file and return the plaintext payload as a dict.

    Supports v2.x (PBKDF2, 4-field AAD) and v3.0 (Argon2id, JCS, 6-field AAD).

    Args:
        filepath:   Path to the .klickd file.
        passphrase: Decryption passphrase.
        memory_dir: Caller-supplied memory directory (Bankr 4.1c — NOT from payload).

    Raises:
        KlickdAuthError:    wrong passphrase or tampered ciphertext
        KlickdVersionError: unsupported major version
        KlickdFormatError:  malformed envelope or payload
    """
    # Passphrase entropy warning (stderr unconditionally — Bankr P1 #3)
    if len(passphrase) < MIN_PASSPHRASE_LEN:
        raise KlickdWeakPassphraseError(
            f"KLICKD_E_WEAK_PASS: passphrase too short ({len(passphrase)} < {MIN_PASSPHRASE_LEN})"
        )
    if len(passphrase) < WARN_PASSPHRASE_LEN:
        print(
            f"WARNING: passphrase entropy below recommended threshold "
            f"({len(passphrase)} chars < {WARN_PASSPHRASE_LEN} recommended). "
            "Use a passphrase of at least 12 characters in production.",
            file=sys.stderr,
        )
        warnings.warn(
            f"Passphrase is only {len(passphrase)} characters; "
            f"a minimum of {WARN_PASSPHRASE_LEN} is recommended.",
            UserWarning,
            stacklevel=2,
        )

    # Envelope size check — Bankr HIGH 2.3a
    try:
        file_size = os.path.getsize(filepath)
    except OSError as e:
        raise KlickdFormatError(f"KLICKD_E_FORMAT: cannot stat file: {e}")
    if file_size > _MAX_ENVELOPE_BYTES:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: envelope exceeds 1MB limit ({file_size} bytes)"
        )

    try:
        with open(filepath) as f:
            envelope = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise KlickdFormatError(f"KLICKD_E_FORMAT: cannot read envelope: {e}")

    # Version validation — Bankr MEDIUM 2.1a: must be string matching \d+\.\d+
    version_str = envelope.get("klickd_version")
    if not isinstance(version_str, str) or not _VERSION_RE.match(version_str):
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: klickd_version must be a string matching N.N, got {version_str!r}"
        )
    major = version_str.split(".")[0]
    if major not in SUPPORTED_MAJOR:
        raise KlickdVersionError(f"KLICKD_E_VERSION: unsupported version {version_str!r}")

    for field in ("encrypted", "domain", "created_at", "ciphertext"):
        if field not in envelope:
            raise KlickdFormatError(f"KLICKD_E_FORMAT: missing field {field!r}")

    # Strict base64 decode — Bankr MEDIUM 1.5
    raw = _b64decode_strict(envelope["ciphertext"], "ciphertext")

    if len(raw) < _GCM_TAG_BYTES:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: ciphertext too short (< {_GCM_TAG_BYTES} bytes)"
        )

    # Version dispatch
    if major == "3":
        for block in ("kdf", "cipher"):
            if block not in envelope:
                raise KlickdFormatError(f"KLICKD_E_FORMAT: v3.0 requires {block!r} block")
        iv  = _b64decode_strict(envelope["cipher"]["iv"], "cipher.iv")
        aad = _canonical_aad_v3(envelope)
        key = _derive_key_v3(passphrase, envelope["kdf"])
    else:
        # v2.x
        for field in ("kdf_salt", "iv"):
            if field not in envelope:
                raise KlickdFormatError(f"KLICKD_E_FORMAT: missing field {field!r}")
        salt = _b64decode_strict(envelope["kdf_salt"], "kdf_salt")
        iv   = _b64decode_strict(envelope["iv"], "iv")
        aad  = _canonical_aad_v2(envelope)
        key  = _derive_key_v2(passphrase, salt)

    try:
        plaintext = AESGCM(key).decrypt(iv, raw, aad)
    except Exception:
        raise KlickdAuthError(
            "KLICKD_E_AUTH: decryption failed — wrong passphrase or tampered file"
        )

    # Payload size check — Bankr HIGH 2.3a
    if len(plaintext) > _MAX_PAYLOAD_BYTES:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: payload exceeds 4MB limit ({len(plaintext)} bytes)"
        )

    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception:
        raise KlickdFormatError("KLICKD_E_FORMAT: decrypted payload is not valid JSON")

    # agent_instructions / user_preferences size cap — 32KB (Bankr P1 #6)
    agent_instr = payload.get("agent_instructions", "") or payload.get("user_preferences", "")
    if isinstance(agent_instr, str) and len(agent_instr.encode("utf-8")) > _MAX_AGENT_INSTR_BYTES:
        raise KlickdFormatError(
            "KLICKD_E_FORMAT: agent_instructions/user_preferences exceeds 32 KB limit"
        )

    # Memory path: caller-supplied, NOT from payload (Bankr MEDIUM 4.1c)
    # Strip any path traversal — must resolve to a subpath of home directory
    resolved = Path(memory_dir).expanduser().resolve()
    home = Path.home().resolve()
    try:
        resolved.relative_to(home)
    except ValueError:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: memory_dir must be under home directory, got {resolved}"
        )
    payload["_resolved_memory_path"] = str(resolved)

    return payload
