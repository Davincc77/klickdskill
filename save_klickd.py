"""
save_klickd.py — .klickd v3.0 encryption module
================================================
Encrypts a Python dict payload with AES-256-GCM and writes a .klickd v3.0
JSON envelope to disk.

Envelope layout (all bytes fields are standard base64, RFC 4648 §4)
--------------------------------------------------------------------
klickd_version : "3.0"
encrypted      : true
domain         : str   caller-supplied, e.g. "general"
created_at     : str   UTC, RFC 3339, YYYY-MM-DDTHH:MM:SSZ (no fractional sec)
kdf            : {name, salt, params: {m, t, p}}   — Argon2id block
cipher         : {name, iv}                         — AES-256-GCM block
ciphertext     : base64(ciphertext_bytes || 16-byte GCM tag)

AAD (Additional Authenticated Data)
-------------------------------------
RFC 8785 JCS canonical JSON of exactly 6 fields:
    {cipher, created_at, domain, encrypted, kdf, klickd_version}
sorted keys, ensure_ascii=False.
This matches the AAD that load_klickd.py v3.0 expects.

Payload limits
--------------
- Plaintext payload: <= 4 MB  (KLICKD_E_FORMAT if exceeded)
- agent_instructions / user_preferences: <= 32 KB (KLICKD_E_FORMAT)
- ethics.locked_actions: validated as list[str] if present
- growth.level: validated <= 5 if present
- growth.memory_refs: validated >= 3 if level == 5

KDF defaults
------------
Argon2id: m=65536 (64 MiB), t=3 iterations, p=1 thread
These meet the §14.1 minimum floors enforced by the decoder.

Error classes (imported from load_klickd)
------------------------------------------
KlickdWeakPassphraseError  passphrase < 8 chars (hard reject)
(KlickdAuthError, KlickdVersionError, KlickdFormatError also re-exported)
"""

import base64
import json
import os
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from argon2.low_level import hash_secret_raw, Type as Argon2Type
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

# Shared error classes from load_klickd
from load_klickd import KlickdAuthError, KlickdVersionError, KlickdFormatError  # noqa: F401


# ---------------------------------------------------------------------------
# Additional error class
# ---------------------------------------------------------------------------

class KlickdWeakPassphraseError(Exception):
    """Raised when the passphrase is too short to meet the minimum security bar."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KLICKD_VERSION   = "3.0"
_KEY_BYTES        = 32
_SALT_BYTES       = 16
_IV_BYTES         = 12
_GCM_TAG_BYTES    = 16

# Argon2id defaults — meet §14.1 minimum floors
_ARGON2_M         = 65536   # 64 MiB
_ARGON2_T         = 3
_ARGON2_P         = 1
_ARGON2_MIN_M     = 65536   # floor (matches decoder)
_ARGON2_MIN_T     = 3
_ARGON2_MIN_P     = 1
_ARGON2_MAX_M     = 4_194_304  # 4 GiB — OOM/DoS guard
_ARGON2_MAX_T     = 999
_ARGON2_MAX_P     = 255

_MIN_PASSPHRASE_REJECT = 8    # hard reject below this
_MIN_PASSPHRASE_WARN   = 12   # warn below this

# Payload limits (mirrors decoder)
_MAX_PAYLOAD_BYTES     = 4 * 1024 * 1024   # 4 MB
_MAX_AGENT_INSTR_BYTES = 32 * 1024         # 32 KB

# Ethics/growth validation limits
_MAX_GROWTH_LEVEL = 5
_MIN_MEMORY_REFS_AT_MAX_LEVEL = 3


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jcs_canonicalize(obj: dict) -> bytes:
    """
    RFC 8785 JCS canonical JSON.
    Covers all .klickd AAD field types: strings, bools, ints, nested objects.
    NFC normalisation applies to strings (Python str is already NFC in practice;
    explicit normalisation added for correctness per RFC 8785 §3.2.2.2).
    Float values with non-zero fractional part must not appear in AAD fields.
    """
    import unicodedata
    def _normalize(o):
        if isinstance(o, str):
            return unicodedata.normalize("NFC", o)
        if isinstance(o, dict):
            return {_normalize(k): _normalize(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_normalize(i) for i in o]
        return o
    normalized = _normalize(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _derive_key(passphrase: str, salt: bytes,
                m: int = _ARGON2_M, t: int = _ARGON2_T, p: int = _ARGON2_P) -> bytes:
    """Derive a 32-byte AES key via Argon2id."""
    if not ARGON2_AVAILABLE:
        raise ImportError(
            "argon2-cffi is required for v3.0 encoding: pip install argon2-cffi"
        )
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=t,
        memory_cost=m,
        parallelism=p,
        hash_len=_KEY_BYTES,
        type=Argon2Type.ID,
    )


def _build_aad_v3(klickd_version: str, encrypted: bool,
                  domain: str, created_at: str,
                  kdf_block: dict, cipher_block: dict) -> bytes:
    """
    Build v3.0 AAD: 6 fields via RFC 8785 JCS.
    Fields: cipher, created_at, domain, encrypted, kdf, klickd_version
    """
    aad_dict = {
        "cipher":         cipher_block,
        "created_at":     created_at,
        "domain":         domain,
        "encrypted":      encrypted,
        "kdf":            kdf_block,
        "klickd_version": klickd_version,
    }
    return _jcs_canonicalize(aad_dict)


def _utc_now_rfc3339() -> str:
    """Return current UTC time as YYYY-MM-DDTHH:MM:SSZ (no fractional seconds)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_payload(payload: dict) -> None:
    """
    Validate payload fields before encryption.

    Checks:
    - agent_instructions / user_preferences <= 32 KB
    - ethics.locked_actions is list[str] if present  (§18ter)
    - growth.level <= 5 if present
    - growth.memory_refs >= 3 if level == 5  (§18 growth validation)
    """
    # agent_instructions / user_preferences size cap
    for field in ("agent_instructions", "user_preferences"):
        val = payload.get(field)
        if isinstance(val, str):
            size = len(val.encode("utf-8"))
            if size > _MAX_AGENT_INSTR_BYTES:
                raise KlickdFormatError(
                    f"KLICKD_E_FORMAT: {field!r} exceeds 32 KB limit ({size} bytes)"
                )

    # §18ter — ethics.locked_actions must be a list of strings if present
    ethics = payload.get("ethics")
    if ethics is not None:
        if not isinstance(ethics, dict):
            raise KlickdFormatError(
                "KLICKD_E_FORMAT: 'ethics' must be a dict"
            )
        locked = ethics.get("locked_actions")
        if locked is not None:
            if not isinstance(locked, list) or not all(isinstance(a, str) for a in locked):
                raise KlickdFormatError(
                    "KLICKD_E_FORMAT: ethics.locked_actions must be a list of strings"
                )

    # §18 — growth level and memory_refs validation
    growth = payload.get("growth")
    if growth is not None:
        if not isinstance(growth, dict):
            raise KlickdFormatError(
                "KLICKD_E_FORMAT: 'growth' must be a dict"
            )
        level = growth.get("level")
        if level is not None:
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_klickd(
    payload: dict,
    passphrase: str,
    domain: str = "general",
    filepath: str = None,
    argon2_m: int = _ARGON2_M,
    argon2_t: int = _ARGON2_T,
    argon2_p: int = _ARGON2_P,
) -> str:
    """
    Encrypt *payload* and write a .klickd v3.0 envelope to *filepath*.

    Parameters
    ----------
    payload : dict
        Arbitrary JSON-serialisable dict to encrypt.
    passphrase : str
        Encryption passphrase.  Must be >= 8 characters; >= 12 recommended.
    domain : str, optional
        Logical domain tag stored in the envelope (default: "general").
    filepath : str, optional
        Destination path.  If None, a UUID-named file is created under
        ``~/.klickd/memory/``.
    argon2_m : int, optional
        Argon2id memory cost in KiB (default: 65536 = 64 MiB).
    argon2_t : int, optional
        Argon2id time cost / iterations (default: 3).
    argon2_p : int, optional
        Argon2id parallelism (default: 1).

    Returns
    -------
    str
        Absolute path to the written file.

    Raises
    ------
    KlickdWeakPassphraseError
        If *passphrase* is shorter than 8 characters.
    KlickdFormatError
        If *payload* is not JSON-serialisable, exceeds size limits,
        or contains invalid ethics/growth fields.
    ImportError
        If argon2-cffi is not installed.

    Warns
    -----
    UserWarning
        If *passphrase* is shorter than 12 characters.
    """
    # --- passphrase enforcement ---------------------------------------------
    if len(passphrase) < _MIN_PASSPHRASE_REJECT:
        raise KlickdWeakPassphraseError(
            f"Passphrase must be at least {_MIN_PASSPHRASE_REJECT} characters "
            f"(got {len(passphrase)})."
        )

    if len(passphrase) < _MIN_PASSPHRASE_WARN:
        warnings.warn(
            f"Passphrase is only {len(passphrase)} characters; "
            "a minimum of 12 is recommended.",
            UserWarning,
            stacklevel=2,
        )

    # --- validate payload fields (ethics, growth, size) -------------------
    _validate_payload(payload)

    # --- serialise payload --------------------------------------------------
    try:
        plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise KlickdFormatError(f"Payload is not JSON-serialisable: {exc}") from exc

    # --- payload size check (before encryption) ----------------------------
    if len(plaintext) > _MAX_PAYLOAD_BYTES:
        raise KlickdFormatError(
            f"KLICKD_E_FORMAT: payload exceeds 4MB limit ({len(plaintext)} bytes)"
        )

    # --- CSPRNG material ----------------------------------------------------
    salt = os.urandom(_SALT_BYTES)
    iv   = os.urandom(_IV_BYTES)

    # --- timestamp ----------------------------------------------------------
    created_at = _utc_now_rfc3339()

    # --- build kdf + cipher blocks ------------------------------------------
    kdf_block = {
        "name":   "argon2id",
        "salt":   base64.b64encode(salt).decode("ascii"),
        "params": {"m": argon2_m, "t": argon2_t, "p": argon2_p},
    }
    cipher_block = {
        "name": "aes-256-gcm",
        "iv":   base64.b64encode(iv).decode("ascii"),
    }

    # --- build AAD (6 fields, RFC 8785 JCS) ---------------------------------
    aad = _build_aad_v3(_KLICKD_VERSION, True, domain, created_at, kdf_block, cipher_block)

    # --- derive key (Argon2id) ----------------------------------------------
    key = _derive_key(passphrase, salt, m=argon2_m, t=argon2_t, p=argon2_p)

    # --- encrypt AES-256-GCM ------------------------------------------------
    aesgcm = AESGCM(key)
    # cryptography lib appends the 16-byte GCM tag at the end automatically
    cipher_bytes = aesgcm.encrypt(iv, plaintext, aad)
    # cipher_bytes = ciphertext_bytes || 16-byte tag  ✓

    # --- base64-encode (RFC 4648 §4, standard padded) -----------------------
    ciphertext_b64 = base64.b64encode(cipher_bytes).decode("ascii")

    # --- build envelope -----------------------------------------------------
    envelope = {
        "klickd_version": _KLICKD_VERSION,
        "encrypted":      True,
        "domain":         domain,
        "created_at":     created_at,
        "kdf":            kdf_block,
        "cipher":         cipher_block,
        "ciphertext":     ciphertext_b64,
    }

    # --- resolve output path ------------------------------------------------
    if filepath is None:
        default_dir = Path.home() / ".klickd" / "memory"
        default_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(default_dir / f"{uuid.uuid4()}.klickd")

    out_path = Path(filepath).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # --- write file ---------------------------------------------------------
    # Auto-audit A4: use ensure_ascii=False for consistency with payload encoding
    # (ASCII-safe base64 fields are unaffected; domain/created_at remain printable ASCII)
    out_path.write_text(
        json.dumps(envelope, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(out_path.resolve())
