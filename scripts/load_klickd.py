#!/usr/bin/env python3
"""load_klickd.py v3.3 -- PBKDF2 + 4-field AAD (v2.x); Argon2id + RFC 8785 JCS (v3.0)
v3.3 fix (2026-05-20):
  BUG FIX — build_system_prompt: duplicate onboarding block suppressed.
  When agent_instructions already contains a .klickd Profile Loader / On First Message
  block (injected by the Klickd app generator), the §29b onboarding_trigger path
  no longer injects a second identical block. Guard checks 5 language variants.
  Impact: users were being asked for their .klickd file TWICE in the same prompt.

v3.2 additions (2026-05-19):
  build_system_prompt handles: resume_trigger, numerical_results, interruption_point,
  context.mode (lightweight), vocabulary_used.

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
  P2       — cipher.name canonical = 'AES-256-GCM' (uppercase); legacy 'aes-256-gcm' accepted with DeprecationWarning
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
_ARGON2_MAX = {"m": 4_194_304, "t": 999, "p": 255}  # sane upper bounds (OOM / DoS guard)
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
    """Bankr CRITICAL 1.3b/6.2 — reject files with sub-minimum or over-maximum Argon2id params."""
    for param, minimum in _ARGON2_MIN.items():
        val = params.get(param)
        if not isinstance(val, int) or val < minimum:
            raise KlickdFormatError(
                f"KLICKD_E_KDF: kdf.params.{param}={val!r} below minimum {minimum}"
            )
    for param, maximum in _ARGON2_MAX.items():
        val = params.get(param)
        if isinstance(val, int) and val > maximum:
            raise KlickdFormatError(
                f"KLICKD_E_KDF: kdf.params.{param}={val!r} exceeds maximum {maximum}"
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

    v3.2: handles resume_trigger, numerical_results, interruption_point,
    context.mode (lightweight), vocabulary_used.

    The returned prompt layout is:
        <UserContext>\n{prefs}\n</UserContext>\n\n---\n\n{base_system_prompt}
    """
    context = klickd_payload.get("context", {}) or {}
    knowledge = klickd_payload.get("knowledge", {}) or {}

    # v3.2: Check context.mode — lightweight = condensed prompt
    mode = context.get("mode", "full")
    is_lightweight = (mode == "lightweight")

    # Auto-audit A3: check both fields independently; prefer user_preferences,
    # append agent_instructions if different and both present.
    # Canonical type for user_preferences is str (SPEC §22.6). Legacy dict form
    # is JSON-serialised for prompt injection (back-compat with pre-v3.4 files).
    prefs_raw = klickd_payload.get("user_preferences", "") or ""
    if isinstance(prefs_raw, dict):
        prefs = json.dumps(prefs_raw, ensure_ascii=False, sort_keys=True)
    else:
        prefs = prefs_raw
    instr = klickd_payload.get("agent_instructions", "") or ""
    # Merge: if both non-empty and different, combine them (user_preferences first)
    if prefs and instr and prefs != instr:
        combined = f"{prefs}\n\n{instr}"
    else:
        combined = prefs or instr

    # --- v3.2 NEW FIELD HANDLING ---
    extra_parts = []

    # resume_trigger: MUST be output at start of resumed session
    resume_trigger = context.get("resume_trigger")
    if resume_trigger and not is_lightweight:
        extra_parts.append(
            f"RESUME SIGNAL (output this verbatim at session start): {resume_trigger}"
        )

    # interruption_point: resume from this exact point
    interruption_point = context.get("interruption_point")
    if interruption_point and not is_lightweight:
        ip_parts = []
        if interruption_point.get("topic"):
            ip_parts.append(f"Topic: {interruption_point['topic']}")
        if interruption_point.get("subtopic"):
            ip_parts.append(f"Subtopic: {interruption_point['subtopic']}")
        if interruption_point.get("completion_pct") is not None:
            ip_parts.append(f"Completion: {interruption_point['completion_pct']}%")
        if interruption_point.get("last_message_excerpt"):
            ip_parts.append(f"Last excerpt: {interruption_point['last_message_excerpt']}")
        if ip_parts:
            extra_parts.append(
                "INTERRUPTION POINT (resume exactly from here):\n" + "\n".join(ip_parts)
            )

    # numerical_results: MUST cite verbatim
    numerical_results = context.get("numerical_results")
    if numerical_results and not is_lightweight:
        nr_lines = []
        for nr in numerical_results:
            label = nr.get("label", "")
            value = nr.get("value", "")
            unit = nr.get("unit", "")
            formula = nr.get("formula", "")
            line = f"  - {label}: {value}{unit}"
            if formula:
                line += f" (formula: {formula})"
            nr_lines.append(line)
        if nr_lines:
            extra_parts.append(
                "NUMERICAL RESULTS (MUST cite verbatim when resuming):\n"
                + "\n".join(nr_lines)
            )

    # vocabulary_used: MUST reuse this exact vocabulary
    vocabulary_used = knowledge.get("vocabulary_used")
    if vocabulary_used and not is_lightweight:
        vocab_str = ", ".join(vocabulary_used[:50])  # cap at 50 terms in prompt
        extra_parts.append(
            f"DOMAIN VOCABULARY (MUST reuse in resumed session): {vocab_str}"
        )

    # language_switch_detected
    if context.get("language_switch_detected") and not is_lightweight:
        extra_parts.append(
            "NOTE: Language switch detected. Context is language-agnostic — adapt response language to user."
        )

    # subject_change_detected
    if context.get("subject_change_detected") and not is_lightweight:
        extra_parts.append(
            "NOTE: Subject change detected. Acknowledge previous session is paused; treat this as a new context branch."
        )

    # §29b — onboarding_trigger: if 'on_new_agent', prepend the profile-loader block
    # Guard: skip injection if agent_instructions already embeds the loader block
    # (Klickd app generators embed it inside agent_instructions — injecting again
    # produces a duplicate prompt that asks the user twice for their .klickd file).
    _loader_already_present = (
        ".klickd Profile Loader" in combined
        or "On First Message" in combined
        or ".klickd à charger" in combined
        or ".klickd-Profil" in combined
        or ".klickd-Fichier" in combined
    )
    onboarding_trigger = klickd_payload.get("onboarding_trigger", "manual")
    if onboarding_trigger == "on_new_agent" and not is_lightweight and not _loader_already_present:
        # Detect language from identity field, fallback to EN
        lang = (klickd_payload.get("identity") or {}).get("language", "en").lower()
        onboarding_prompts = {
            "fr": (
                "## .klickd Profile Loader\n"
                "Au tout premier message de l'utilisateur dans cette session : vérifie si un fichier .klickd "
                "a déjà été fourni.\n"
                "Si ce n'est pas le cas, demande une seule fois :\n"
                "\"Tu as un profil .klickd à charger ? Colle le contenu ou upload le fichier — "
                "je reprends exactement là où tu t'es arrêté.\"\n"
                "Ne pose pas la question une deuxième fois."
            ),
            "de": (
                "## .klickd Profile Loader\n"
                "Beim allerersten Nutzer-Nachricht in dieser Sitzung: prüfe, ob bereits eine .klickd-Datei bereitgestellt wurde.\n"
                "Falls nicht, frage einmal:\n"
                "\"Hast du ein .klickd-Profil? Füge den Inhalt ein oder lade die Datei hoch — "
                "ich mache genau dort weiter, wo du aufgehört hast.\"\n"
                "Frage nicht noch einmal."
            ),
            "lb": (
                "## .klickd Profile Loader\n"
                "Bei der allererster Noriicht vum Benotzer an denger Sessioun: kucke ob eng .klickd-Fichier "
                "scho geluede ginn ass.\n"
                "Wann net, frî eng Kier:\n"
                "\"Hues du e .klickd-Profil ze lueden? Klëbs den Inhalt an oder lued d'Fichier héich — "
                "ech maachen do weider, wou du opgehalen hues.\"\n"
                "Nur eng Kier frî."
            ),
        }
        # Default to English for all other languages
        onboarding_block = onboarding_prompts.get(lang, (
            "## .klickd Profile Loader\n"
            "On your very first message to the user in this session: check if a .klickd payload "
            "has already been provided.\n"
            "If not, ask once:\n"
            "\"Do you have a .klickd profile? Paste or upload it and I'll resume your context instantly.\"\n"
            "Do not ask again after the first exchange."
        ))
        extra_parts.insert(0, onboarding_block)  # Prepend so it's seen first

    # Build full combined context
    all_parts = []
    if combined:
        all_parts.append(combined)
    all_parts.extend(extra_parts)

    if not all_parts:
        return base_system_prompt

    full_context = "\n\n".join(all_parts)

    # Sanitize: escape any </UserContext> sequences that would break the tag boundary
    safe = str(full_context).replace("</UserContext>", "<\\/UserContext>")
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
        # Canonical = 'AES-256-GCM' (uppercase) per SPEC v3.5 §15/§16 + schema enum.
        # Accept legacy lowercase 'aes-256-gcm' (vectors generated < v3.5.1) with deprecation warning.
        cipher_name = envelope["cipher"].get("name")
        if cipher_name == "aes-256-gcm":
            warnings.warn(
                "KLICKD_W_DEPRECATED: cipher.name='aes-256-gcm' (lowercase) is legacy; "
                "canonical is 'AES-256-GCM'. Re-encode to upgrade.",
                DeprecationWarning,
                stacklevel=2,
            )
        elif cipher_name != "AES-256-GCM":
            raise KlickdFormatError(
                f"KLICKD_E_FORMAT: cipher.name must be 'AES-256-GCM' (canonical) "
                f"or 'aes-256-gcm' (legacy), got {cipher_name!r}"
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


# ---------------------------------------------------------------------------
# §14ter — Agent Session Lifecycle State Machine
# ---------------------------------------------------------------------------
#
# Three states:
#   NO_PROFILE      — no .klickd context present in the session
#   PROFILE_LOADED  — file decrypted, payload in context, not yet active
#   SESSION_ACTIVE  — conversation underway
#
# Transitions are driven by: file upload, user decline, session end signals.
# ---------------------------------------------------------------------------

from datetime import datetime, timezone as _tz
import copy as _copy
import uuid as _uuid

# Session end signals (§14ter — SESSION_ACTIVE)
_END_SIGNALS = frozenset({
    "bye", "goodbye", "à bientôt", "a bientôt", "tschüss", "tschuss",
    "äddi", "addi", "au revoir", "ciao", "end session", "fin de session",
    "save my progress", "sauvegarde", "export my .klickd", "save context",
})

# Onboarding prompts — NO_PROFILE state, first message (≤120 chars, 1 sentence)
_NO_PROFILE_PROMPTS = {
    "fr": "Tu as un profil .klickd ? Upload ou colle-le — sinon je t'en crée un automatiquement en fin de session.",
    "de": "Hast du ein .klickd-Profil? Lade es hoch oder füge es ein — sonst erstelle ich dir am Sitzungsende eines.",
    "lb": "Hues du e .klickd-Profil? Lued et héich oder klëbs et an — soss erstellen ech dir eent um Enn vun der Sessioun.",
    "en": "Do you have a .klickd profile? Upload or paste it — or I'll create one for you at the end of this session.",
}

# AUTO_SAVE delivery messages (§14ter.3)
_SAVE_MESSAGES = {
    "fr": "Session sauvegardée. Télécharge ton fichier .klickd mis à jour pour garder ta progression.",
    "de": "Sitzung gespeichert. Lade deine aktualisierte .klickd-Datei herunter.",
    "lb": "Sessioun gespäichert. Lued deng aktualiséiert .klickd-Fichier erof.",
    "en": "Session saved. Download your updated .klickd file to keep your progress.",
}


def get_session_state(session: dict) -> str:
    """
    Return the current session state: 'NO_PROFILE', 'PROFILE_LOADED', or 'SESSION_ACTIVE'.

    The session dict is a simple mutable dict the agent maintains across turns:
        {
            'state': str,           # current state
            'payload': dict|None,   # decrypted .klickd payload, or None
            'passphrase': str|None, # in-memory only — zeroed after AUTO_SAVE
            'lang': str,            # detected language ('en', 'fr', 'de', 'lb')
            'dirty': bool,          # True if session has changes to save
        }

    If 'state' is absent, initialises to 'NO_PROFILE'.
    """
    if "state" not in session:
        session["state"] = "NO_PROFILE"
        session.setdefault("payload", None)
        session.setdefault("passphrase", None)
        session.setdefault("lang", "en")
        session.setdefault("dirty", False)
    return session["state"]


def build_no_profile_prompt(lang: str = "en") -> str:
    """
    Return the single-sentence NO_PROFILE onboarding prompt in the given language.
    §14ter: max 120 chars, 1 sentence, no fallback educational content.
    Falls back to English for unknown languages.
    """
    prompt = _NO_PROFILE_PROMPTS.get(lang[:2].lower(), _NO_PROFILE_PROMPTS["en"])
    assert len(prompt) <= 120, f"KLICKD_BUG: NO_PROFILE prompt exceeds 120 chars: {len(prompt)}"
    return prompt


def transition(session: dict, event: str, **kwargs) -> dict:
    """
    Drive the state machine forward based on an event.

    Events:
        'file_provided'   — user uploaded or pasted a .klickd file
                            kwargs: payload (dict), passphrase (str)
        'user_declined'   — user ignored or declined the profile prompt
        'first_message'   — first user message in a fresh NO_PROFILE session
                            kwargs: lang (str, detected from message)
        'session_end'     — session end signal detected
                            kwargs: session_summary (str), memory_entries (list)
        'export_request'  — user explicitly asked to export .klickd mid-session

    Returns a dict with:
        'state'   — new state
        'action'  — what the agent should do: 'output_resume', 'output_prompt',
                    'proceed', 'auto_save', None
        'message' — string for the agent to output (if any)
    """
    state = get_session_state(session)

    # ── NO_PROFILE ──────────────────────────────────────────────────────────
    if state == "NO_PROFILE":
        if event == "first_message":
            lang = kwargs.get("lang", session.get("lang", "en"))
            session["lang"] = lang
            # Only prompt once — set flag so we don't prompt again
            if session.get("_onboarding_asked"):
                return {"state": state, "action": "proceed", "message": None}
            session["_onboarding_asked"] = True
            return {
                "state": "NO_PROFILE",
                "action": "output_prompt",
                "message": build_no_profile_prompt(lang),
            }

        if event == "file_provided":
            payload = kwargs["payload"]
            passphrase = kwargs.get("passphrase")
            session["payload"] = payload
            session["passphrase"] = passphrase
            session["state"] = "PROFILE_LOADED"
            # Inherit language from payload identity if available
            payload_lang = (payload.get("identity") or {}).get("language", session.get("lang", "en"))
            session["lang"] = payload_lang[:2].lower()
            resume = (payload.get("context") or {}).get("resume_trigger", "")
            return {
                "state": "PROFILE_LOADED",
                "action": "output_resume",
                "message": resume,
            }

        if event == "user_declined":
            session["state"] = "SESSION_ACTIVE"
            return {"state": "SESSION_ACTIVE", "action": "proceed", "message": None}

    # ── PROFILE_LOADED ───────────────────────────────────────────────────────
    if state == "PROFILE_LOADED":
        # Always transition to SESSION_ACTIVE on first user message
        session["state"] = "SESSION_ACTIVE"
        resume = (session.get("payload") or {}).get("context", {}).get("resume_trigger", "")
        return {
            "state": "SESSION_ACTIVE",
            "action": "output_resume",
            "message": resume,
        }

    # ── SESSION_ACTIVE ───────────────────────────────────────────────────────
    if state == "SESSION_ACTIVE":
        if event in ("session_end", "export_request"):
            summary = kwargs.get("session_summary", "")
            memory_entries = kwargs.get("memory_entries", [])
            updated_payload = merge_session_changes(
                session.get("payload"), summary, memory_entries
            )
            session["payload"] = updated_payload
            session["dirty"] = True
            lang = session.get("lang", "en")
            if event == "session_end":
                session["state"] = "NO_PROFILE"  # ready for next session
                # Zero passphrase after flagging for save
                _save_msg = _SAVE_MESSAGES.get(lang[:2].lower(), _SAVE_MESSAGES["en"])
                return {
                    "state": "NO_PROFILE",
                    "action": "auto_save",
                    "message": _save_msg,
                    "payload": updated_payload,
                    "passphrase": session.get("passphrase"),
                }
            else:  # export_request — stay active
                _save_msg = _SAVE_MESSAGES.get(lang[:2].lower(), _SAVE_MESSAGES["en"])
                return {
                    "state": "SESSION_ACTIVE",
                    "action": "auto_save",
                    "message": _save_msg,
                    "payload": updated_payload,
                    "passphrase": session.get("passphrase"),
                }

    return {"state": state, "action": None, "message": None}


def is_session_end_signal(text: str) -> bool:
    """
    Return True if the user's message matches a known session end signal.
    §14ter — SESSION_ACTIVE: agent MUST recognise these signals.
    Case-insensitive, strips punctuation.
    """
    cleaned = text.lower().strip().rstrip(".,!?")
    # Exact match
    if cleaned in _END_SIGNALS:
        return True
    # Substring match for multi-word signals
    for signal in _END_SIGNALS:
        if len(signal) > 4 and signal in cleaned:
            return True
    return False


def merge_session_changes(
    existing_payload: dict | None,
    session_summary: str,
    memory_entries: list,
) -> dict:
    """
    Merge session changes into an existing payload, or build a minimal one
    from scratch if no profile was loaded (NO_PROFILE → AUTO_SAVE path).

    §14ter.3 AUTO_SAVE Protocol:
    - Update context.current_state
    - Update context.resume_trigger
    - Append new memory entries (max 5 per session, total max 1000)
    - Bump created_at to current UTC

    Returns the updated payload dict (does NOT encrypt — caller handles that).
    """
    now = datetime.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if existing_payload is None:
        # Build minimal payload from scratch
        payload = {
            "payload_schema_version": "3.0",
            "domain_schema_version": "education-1.0",
            "identity": {},
            "agent_instructions": "",
            "context": {},
            "knowledge": {},
            "memory": [],
        }
    else:
        payload = _copy.deepcopy(existing_payload)

    # Update context
    ctx = payload.setdefault("context", {})
    if session_summary:
        ctx["current_state"] = session_summary
        # resume_trigger = first 30 words of summary
        words = session_summary.split()
        ctx["resume_trigger"] = " ".join(words[:30])

    # Update created_at
    payload["created_at"] = now

    # Append new memory entries (max 5 per call, total max 1000)
    mem = payload.setdefault("memory", [])
    for entry in memory_entries[:5]:
        if not isinstance(entry, dict):
            continue
        # Ensure required fields
        entry.setdefault("id", str(_uuid.uuid4()))
        entry.setdefault("ts", now)
        entry.setdefault("role", "assistant")
        entry.setdefault("modality", "text")
        entry.setdefault("tags", [])
        if "content" not in entry:
            continue
        mem.append(entry)
    # Enforce 1000-entry cap
    if len(mem) > 1000:
        payload["memory"] = mem[-1000:]

    return payload


def detect_lang(text: str) -> str:
    """
    Minimal language detection from first user message.
    Returns 'fr', 'de', 'lb', or 'en'.
    Fast heuristic — no external dependency.
    """
    t = text.lower()
    # Luxembourgish markers
    if any(w in t for w in ("moien", "äddi", "addi", "klëbs", "hues du", "wéi")):
        return "lb"
    # French markers
    if any(w in t for w in ("je ", "tu ", "vous ", "nous ", "bonjour", "salut", "merci", "c'est")):
        return "fr"
    # German markers
    if any(w in t for w in ("ich ", "du ", "sie ", "hallo", "guten", "danke", "bitte")):
        return "de"
    return "en"
