#!/usr/bin/env python3
"""load_klickd.py v3.0 — Argon2id + RFC 8785 JCS canonicalization"""
import json, base64, os, warnings
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
    warnings.warn("jcs not installed — falling back to json.dumps canonical (v2.x compat only). pip install jcs for v3.0 support.")

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

SUPPORTED_MAJOR = {"2", "3"}
MIN_PASSPHRASE_LEN = 8
WARN_PASSPHRASE_LEN = 12


def _canonical_aad_v2(envelope: dict) -> bytes:
    """v2.x AAD: 4 fields, Python json.dumps canonical."""
    fields = {k: envelope[k] for k in ("created_at", "domain", "encrypted", "klickd_version")}
    return json.dumps(fields, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode("utf-8")


def _canonical_aad_v3(envelope: dict) -> bytes:
    """v3.0 AAD: 6 fields (incl kdf+cipher blocks), RFC 8785 JCS."""
    if not JCS_AVAILABLE:
        raise KlickdFormatError("v3.0 requires RFC 8785 JCS: pip install jcs")
    fields = {k: envelope[k] for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")}
    return jcs.canonicalize(fields)


def _derive_key_v2(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
    return kdf.derive(passphrase.encode("utf-8"))


def _derive_key_v3(passphrase: str, kdf_block: dict) -> bytes:
    name = kdf_block.get("name", "argon2id")
    salt = base64.b64decode(kdf_block["salt"])
    if name == "argon2id":
        if not ARGON2_AVAILABLE:
            raise KlickdFormatError("Argon2id requires: pip install argon2-cffi")
        params = kdf_block.get("params", {"m": 65536, "t": 3, "p": 1})
        return hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=params["t"],
            memory_cost=params["m"],
            parallelism=params["p"],
            hash_len=32,
            type=Type.ID
        )
    elif name == "pbkdf2-sha256":
        iterations = kdf_block.get("params", {}).get("iterations", 600000)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
        return kdf.derive(passphrase.encode("utf-8"))
    else:
        raise KlickdFormatError(f"KLICKD_E_KDF: unsupported kdf.name={name!r}")


def load_klickd(filepath: str, passphrase: str) -> dict:
    """
    Decrypt a .klickd file and return the plaintext payload as a dict.

    Supports v2.x (PBKDF2, 4-field AAD) and v3.0 (Argon2id, JCS, 6-field AAD).

    Raises:
        KlickdAuthError: wrong passphrase or tampered ciphertext
        KlickdVersionError: unsupported major version
        KlickdFormatError: malformed envelope
    """
    if len(passphrase) < WARN_PASSPHRASE_LEN:
        warnings.warn(f"Passphrase is only {len(passphrase)} characters; a minimum of {WARN_PASSPHRASE_LEN} is recommended.")

    try:
        with open(filepath) as f:
            envelope = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise KlickdFormatError(f"KLICKD_E_FORMAT: cannot read envelope: {e}")

    version_str = envelope.get("klickd_version", "")
    major = version_str.split(".")[0]
    if major not in SUPPORTED_MAJOR:
        raise KlickdVersionError(f"KLICKD_E_VERSION: unsupported version {version_str!r}")

    for field in ("encrypted", "domain", "created_at", "ciphertext"):
        if field not in envelope:
            raise KlickdFormatError(f"KLICKD_E_FORMAT: missing field {field!r}")

    try:
        raw = base64.b64decode(envelope["ciphertext"])
    except Exception:
        raise KlickdFormatError("KLICKD_E_FORMAT: malformed base64 in ciphertext")

    if len(raw) < 16:
        raise KlickdFormatError("KLICKD_E_FORMAT: ciphertext too short (< 16 bytes)")

    # Version dispatch
    if major == "3":
        for block in ("kdf", "cipher"):
            if block not in envelope:
                raise KlickdFormatError(f"KLICKD_E_FORMAT: v3.0 requires {block!r} block")
        try:
            iv = base64.b64decode(envelope["cipher"]["iv"])
        except Exception:
            raise KlickdFormatError("KLICKD_E_FORMAT: malformed cipher.iv")
        aad = _canonical_aad_v3(envelope)
        key = _derive_key_v3(passphrase, envelope["kdf"])
    else:
        # v2.x
        for field in ("kdf_salt", "iv"):
            if field not in envelope:
                raise KlickdFormatError(f"KLICKD_E_FORMAT: missing field {field!r}")
        try:
            salt = base64.b64decode(envelope["kdf_salt"])
            iv   = base64.b64decode(envelope["iv"])
        except Exception:
            raise KlickdFormatError("KLICKD_E_FORMAT: malformed base64 in kdf_salt or iv")
        aad = _canonical_aad_v2(envelope)
        key = _derive_key_v2(passphrase, salt)

    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, raw, aad)
    except Exception:
        raise KlickdAuthError("KLICKD_E_AUTH: decryption failed — wrong passphrase or tampered file")

    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception:
        raise KlickdFormatError("KLICKD_E_FORMAT: decrypted payload is not valid JSON")

    # Resolve memory path
    memory_path = payload.get("memory_path", "~/.klickd/memory/")
    payload["_resolved_memory_path"] = str(Path(memory_path).expanduser())

    return payload
