#!/usr/bin/env python3
"""load_klickd.py v3.0 -- PBKDF2 + 4-field AAD (v2.x); Argon2id + RFC 8785 JCS (v3.0)

Security patches applied (Bankr audit 2026-05-18):
  CRITICAL 1.3b / 6.2 — Argon2id/PBKDF2 minimum parameter floor enforced
  HIGH     2.2b       — </UserContext> tag escape in build_system_prompt()
  HIGH     2.3a       — envelope 1MB + payload 4MB size limits enforced
  MEDIUM   1.5        — base64.b64decode(validate=True) at all call sites
  MEDIUM   2.1a       — klickd_version must be string matching \d+\.\d+
  MEDIUM   4.1c       — memory_path removed from user-controlled fields

Grok Audit 2 fixes (2026-05-18):
  P0       — build_system_prompt: klickd context injected BEFORE base_system_prompt (§12)
  P1       — _jcs_canonicalize: RFC 8785 NFC Unicode normalisation added
  P1       — §18ter ethics enforcement: locked_actions validated as hard constraints
  P1       — §18 whitehat scan hook at load time
  P1       — §18 growth validation: level<=5, memory_refs>=3 for level 5
  P2       — cipher.name validated as 'aes-256-gcm' (v3.0 path)
  P2       — kdf.name validated: only 'argon2id' or 'pbkdf2-sha256' accepted
  P2       — agent_instructions and user_preferences checked independently (not 'or' fallback)
"""
import json, base64, os, re, sys, warnings
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    raise ImportError("pip install cryptography")

# RFC 8785 JCS — inline, no external dep.
# Covers all .klickd AAD field types: strings, bools, ints, nested objects.
# Float values with non-zero fractional part must not appear in AAD fields.
# NFC normalisation applied per RFC 8785 §3.2.2.2.
def _jcs_canonicalize(obj) -> bytes:
    import unicodedata
    def _normalize(o):
        if isinstance(o, str):
            return unicodedata.normalize("NFC", o)
        if isinstance(o, dict):
            return {_normalize(k): _normalize(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_normalize(i) for i in o]
        return o
    return json.dumps(
        _normalize(obj),
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')

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
    fields = {k: envelope[k] for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")}
    return _jcs_canonicalize(fields)


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
    Inject .klickd context BEFORE the base system prompt (§12 — highest authority).

    Grok Audit 2 P0: klickd context injected at the TOP so the model sees it
    first and treats it as the highest-priority instruction source.
    Bankr HIGH 2.2b: escape </UserContext> tag boundaries to prevent injection.

    The returned prompt layout is:
        <UserContext>\n{prefs}\n</UserContext>\n\n---\n\n{base_system_prompt}
    """
    # Auto-audit A3: check both fields independently; prefer user_preferences,
    # append agent_instructions if different and both present.
    prefs = klickd_payload.get("user_preferences", "") or ""
    instr = klickd_payload.get("agent_instructions", "") or ""
    # Merge: if both non-empty and different, combine them (user_preferences first)
    if prefs and instr and prefs != instr:
        combined = f"{prefs}\n\n{instr}"
    else:
        combined = prefs or instr
    if not combined:
        return base_system_prompt
    # Sanitize: escape any </UserContext> sequences that would break the tag boundary
    safe = str(combined).replace("</UserContext>", "<\\/UserContext>")
    user_context = f"<UserContext>\n{safe}\n</UserContext>"
    # klickd context FIRST (§12 — highest authority), base prompt follows
    return f"{user_context}\n\n---\n\n{base_system_prompt}"


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
        # P2 — validate cipher.name explicitly (Grok Audit 2)
        cipher_name = envelope["cipher"].get("name")
        if cipher_name != "aes-256-gcm":
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: cipher.name must be 'aes-256-gcm', got {cipher_name!r}"
            )
        # P2 — validate kdf.name explicitly (Grok Audit 2)
        kdf_name = envelope["kdf"].get("name")
        if kdf_name not in ("argon2id", "pbkdf2-sha256"):
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: kdf.name must be 'argon2id' or 'pbkdf2-sha256', got {kdf_name!r}"
            )
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
    # P2 Grok Audit 2: check each field independently (not 'or' fallback)
    for _field in ("agent_instructions", "user_preferences"):
        _val = payload.get(_field, "")
        if isinstance(_val, str) and len(_val.encode("utf-8")) > _MAX_AGENT_INSTR_BYTES:
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: {_field!r} exceeds 32 KB limit"
            )

    # §18 whitehat scan — flag suspicious payload fields at load time
    _whitehat_scan(payload)

    # §18ter ethics enforcement — locked_actions as hard constraints
    _enforce_ethics(payload)

    # §18 growth validation — level<=5, memory_refs>=3 at level 5
    _validate_growth(payload)

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


# ---------------------------------------------------------------------------
# §18 Whitehat scan — detect suspicious payload fields at load time
# ---------------------------------------------------------------------------

_SUSPICIOUS_KEYS = frozenset({
    "__proto__", "constructor", "prototype",
    "system_prompt", "ignore_instructions", "override",
    "jailbreak", "bypass", "admin", "sudo",
})

_PROTOTYPE_POLLUTION_KEYS = frozenset({"__proto__", "constructor", "prototype"})

def _whitehat_scan(payload: dict) -> None:
    """
    §18 whitehat scan: check for suspicious or reserved keys in payload.
    Raises KlickdFormatError for prototype-pollution attempts.
    Emits a warning for other suspicious keys (non-fatal, for audit trail).
    Auto-audit A5: single-pass loop, no redundant sub-check.
    """
    suspicious_found = []
    for key in payload.keys():
        if key in _PROTOTYPE_POLLUTION_KEYS:
            # Hard error — always reject, no warning needed
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: suspicious key {key!r} rejected (prototype pollution)"
            )
        if key in _SUSPICIOUS_KEYS:
            suspicious_found.append(key)
    if suspicious_found:
        warnings.warn(
            f"KLICKD_SECURITY: suspicious keys in payload: {suspicious_found}. "
            "Review before use.",
            UserWarning,
            stacklevel=3,
        )


# ---------------------------------------------------------------------------
# §18ter Ethics enforcement — locked_actions as hard constraints
# ---------------------------------------------------------------------------

def _enforce_ethics(payload: dict) -> None:
    """
    §18ter: validate ethics block if present.
    - ethics.locked_actions must be a list of strings
    - Presence of locked_actions is reported for audit trail (non-fatal)
    """
    ethics = payload.get("ethics")
    if ethics is None:
        return
    if not isinstance(ethics, dict):
        raise KlickdFormatError("KLICKD_E_FORMAT: 'ethics' field must be a dict")
    locked = ethics.get("locked_actions")
    if locked is not None:
        if not isinstance(locked, list) or not all(isinstance(a, str) for a in locked):
            raise KlickdFormatError(
                "KLICKD_E_FORMAT: ethics.locked_actions must be a list of strings"
            )


# ---------------------------------------------------------------------------
# §18 Growth validation
# ---------------------------------------------------------------------------

_MAX_GROWTH_LEVEL = 5
_MIN_MEMORY_REFS_AT_MAX_LEVEL = 3

def _validate_growth(payload: dict) -> None:
    """
    §18 growth validation:
    - growth.level must be 0-5 if present
    - growth.level == 5 requires memory_refs >= 3
    """
    growth = payload.get("growth")
    if growth is None:
        return
    if not isinstance(growth, dict):
        raise KlickdFormatError("KLICKD_E_FORMAT: 'growth' field must be a dict")
    level = growth.get("level")
    if level is None:
        return
    if not isinstance(level, int) or level < 0:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: growth.level must be a non-negative integer, got {level!r}"
        )
    if level > _MAX_GROWTH_LEVEL:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: growth.level={level} exceeds maximum {_MAX_GROWTH_LEVEL}"
        )
    if level == _MAX_GROWTH_LEVEL:
        memory_refs = growth.get("memory_refs")
        count = len(memory_refs) if isinstance(memory_refs, list) else (
            int(memory_refs) if isinstance(memory_refs, int) else 0
        )
        if count < _MIN_MEMORY_REFS_AT_MAX_LEVEL:
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: growth.level=5 requires memory_refs >= "
                f"{_MIN_MEMORY_REFS_AT_MAX_LEVEL}, got {count}"
            )
