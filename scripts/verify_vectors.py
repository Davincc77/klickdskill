#!/usr/bin/env python3
"""Cross-impl test runner for .klickd v2.5 test vectors (positive + negative)."""
import json, sys, os, tempfile, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_klickd import (
    KlickdWeakPassphraseError,
    load_klickd, KlickdAuthError, KlickdVersionError, KlickdFormatError, KlickdError
)

# This runner lives in scripts/; the repository root (which holds tests/, schema/,
# schemas/) is its parent directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
VECTORS_DIR = REPO_ROOT / "tests"

# Map expected_behavior string fragments → exception classes
ERROR_MAP = {
    "KlickdAuthError":    KlickdAuthError,
    "KlickdVersionError": KlickdVersionError,
    "KlickdFormatError":  KlickdFormatError,
    "KlickdWeakPassphraseError": KlickdWeakPassphraseError,
}

def run_suite(vectors_file: Path, label: str) -> tuple[int, int]:
    with open(vectors_file) as f:
        data = json.load(f)
    print(f"\n── {label} — spec {data['spec_version']} ──────────────────────────")
    passed = failed = 0

    for v in data["vectors"]:
        vid      = v["id"]
        expected = v.get("expected_behavior", "")
        pp       = v["passphrase"]

        # Determine expected exception class (None = expect success)
        expected_exc = None
        for key, cls in ERROR_MAP.items():
            if key in expected:
                expected_exc = cls
                break

        with tempfile.NamedTemporaryFile(mode="w", suffix=".klickd", delete=False) as tmp:
            json.dump(v["envelope"], tmp)
            tmppath = tmp.name

        try:
            captured_warnings = []
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = load_klickd(tmppath, pp)
                captured_warnings = list(w)

            if expected_exc is not None:
                print(f"  FAIL {vid}: expected {expected_exc.__name__}, got success"); failed += 1
            else:
                dn    = result.get("display_name", "?")
                wflag = " [warned:short-pass]" if captured_warnings else ""
                # For N10 rollback vector: still a PASS (documents the gap)
                note  = " [rollback-gap documented]" if "rollback" in vid else ""
                print(f"  PASS {vid}: display_name={dn!r}{wflag}{note}"); passed += 1

        except tuple(ERROR_MAP.values()) as e:
            exc_class = type(e).__name__
            if expected_exc is not None and isinstance(e, expected_exc):
                print(f"  PASS {vid}: {exc_class} as expected"); passed += 1
            elif expected_exc is not None:
                print(f"  FAIL {vid}: expected {expected_exc.__name__}, got {exc_class}: {e}"); failed += 1
            else:
                print(f"  FAIL {vid}: unexpected {exc_class}: {e}"); failed += 1

        except Exception as e:
            print(f"  FAIL {vid}: {type(e).__name__}: {e}"); failed += 1

        finally:
            os.unlink(tmppath)

    return passed, failed


total_passed = total_failed = 0

# Positive vectors (original)
p, f = run_suite(VECTORS_DIR / "vectors_v25.json", "POSITIVE vectors")
total_passed += p; total_failed += f

# Negative vectors (Bankr P2 addition)
neg_file = VECTORS_DIR / "negative_vectors_v25.json"
if neg_file.exists():
    p, f = run_suite(neg_file, "NEGATIVE vectors")
    total_passed += p; total_failed += f
else:
    print("\n[WARN] negative_vectors_v25.json not found — skipping negative suite")

# v3.0 positive vectors
v30_pos_file = VECTORS_DIR / "vectors_v30.json"
if v30_pos_file.exists():
    p, f = run_suite(v30_pos_file, "POSITIVE v3.0 vectors")
    total_passed += p; total_failed += f
else:
    print("\n[WARN] vectors_v30.json not found — skipping v3.0 positive suite")

# v3.0 negative vectors
v30_neg_file = VECTORS_DIR / "negative_vectors_v30.json"
if v30_neg_file.exists():
    p, f = run_suite(v30_neg_file, "NEGATIVE v3.0 vectors")
    total_passed += p; total_failed += f
else:
    print("\n[WARN] negative_vectors_v30.json not found — skipping v3.0 negative suite")

# ── Adversarial suite — unit tests for each defensive layer ──────────────────
def run_adversarial_suite() -> tuple[int, int]:
    from load_klickd import (
        _whitehat_scan, _enforce_ethics, _validate_growth,
        KlickdFormatError
    )
    import warnings as _warnings

    adv_file = VECTORS_DIR / "adversarial" / "adversarial_v30.json"
    if not adv_file.exists():
        print("\n[SKIP] adversarial suite — file not found")
        return 0, 0

    with open(adv_file) as f:
        data = json.load(f)

    print(f"\n── ADVERSARIAL vectors — Grok Audit 5 ──────────────────────────")
    passed = failed = 0

    for v in data["vectors"]:
        vid = v["id"]
        expected = v.get("expected_behavior", "")
        intent   = v.get("payload_intent", {})
        envelope = v.get("envelope")

        # Determine expected outcome
        expect_format_error = "KLICKD_E_FORMAT" in expected
        expect_warning      = "UserWarning" in expected or "KLICKD_SECURITY" in expected
        expect_success      = "success" in expected.lower() and not expect_format_error

        try:
            # Unit tests (whitehat / ethics / growth)
            if "adv-01" in vid or "adv-02" in vid or "adv-03" in vid:
                _whitehat_scan(intent)
                # Prototype pollution should have raised
                print(f"  FAIL {vid}: expected KlickdFormatError, got success"); failed += 1; continue

            elif "adv-04" in vid or "adv-05" in vid:
                with _warnings.catch_warnings(record=True) as w:
                    _warnings.simplefilter("always")
                    _whitehat_scan(intent)
                if any("suspicious" in str(x.message).lower() or "KLICKD_SECURITY" in str(x.message) for x in w):
                    print(f"  PASS {vid}: warning emitted as expected"); passed += 1
                else:
                    print(f"  FAIL {vid}: expected warning, none emitted"); failed += 1
                continue

            elif "adv-06" in vid or "adv-07" in vid or "adv-08" in vid:
                _enforce_ethics(intent)
                print(f"  FAIL {vid}: expected KlickdFormatError, got success"); failed += 1; continue

            elif "adv-09" in vid or "adv-10" in vid or "adv-11" in vid:
                _validate_growth(intent)
                print(f"  FAIL {vid}: expected KlickdFormatError, got success"); failed += 1; continue

            elif "adv-12" in vid:
                # Size bomb — test via _validate_payload in save
                from save_klickd import _validate_payload
                _validate_payload(intent)
                print(f"  FAIL {vid}: expected KlickdFormatError, got success"); failed += 1; continue

            elif "adv-13" in vid or "adv-14" in vid:
                # Envelope-level attack — use patched envelope via load_klickd
                if envelope:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.klickd', delete=False) as tmp:
                        json.dump(envelope, tmp)
                        tmppath = tmp.name
                    try:
                        load_klickd(tmppath, v["passphrase"])
                        print(f"  FAIL {vid}: expected KlickdFormatError, got success"); failed += 1
                    except KlickdFormatError:
                        print(f"  PASS {vid}: KlickdFormatError as expected"); passed += 1
                    except Exception as e:
                        print(f"  FAIL {vid}: unexpected {type(e).__name__}: {e}"); failed += 1
                    finally:
                        os.unlink(tmppath)
                else:
                    print(f"  SKIP {vid}: no envelope to test"); failed += 1
                continue

            elif "adv-15" in vid:
                # Multi-layer: whitehat fires first
                _whitehat_scan(intent)
                print(f"  FAIL {vid}: expected KlickdFormatError on __proto__, got success"); failed += 1; continue

            elif "adv-16" in vid:
                # Merge-logic injection: </UserContext> must be escaped
                from load_klickd import build_system_prompt
                base = "You are a helpful assistant."
                result_prompt = build_system_prompt(intent, base)
                if "</UserContext>" in result_prompt and "<\\/UserContext>" not in result_prompt:
                    # Raw tag leaked — escape failed
                    print(f"  FAIL {vid}: </UserContext> tag not escaped — injection possible"); failed += 1
                elif base in result_prompt:
                    # Base prompt is present and tag is either escaped or absent
                    print(f"  PASS {vid}: </UserContext> escaped, base prompt intact"); passed += 1
                else:
                    print(f"  FAIL {vid}: base prompt missing from output"); failed += 1
                continue

            elif "adv-17" in vid:
                # ethics.immutable=false — valid locked_actions list should still pass
                _enforce_ethics(intent)
                # Should NOT raise — immutable flag is informational, locked_actions valid
                print(f"  PASS {vid}: ethics with immutable=false accepted, locked_actions enforced"); passed += 1
                continue

            else:
                print(f"  SKIP {vid}: no test handler"); failed += 1; continue

        except KlickdFormatError as e:
            if expect_format_error:
                print(f"  PASS {vid}: KlickdFormatError as expected"); passed += 1
            else:
                print(f"  FAIL {vid}: unexpected KlickdFormatError: {e}"); failed += 1
        except Exception as e:
            print(f"  FAIL {vid}: {type(e).__name__}: {e}"); failed += 1

    return passed, failed

adv_p, adv_f = run_adversarial_suite()
total_passed += adv_p
total_failed += adv_f


# ── v4 preview suite — additive payload preservation (NOT GA) ────────────────
def run_v40_preview_suite() -> tuple[int, int]:
    """
    Verify v4.0.0-preview.1 vectors.

    Preview track is additive/permissive:
      • Wire envelope crypto stays at v3.0 (decoded by load_klickd unchanged).
      • Inner payload carries payload_schema_version='4.0.0-preview.1'.
      • Verifier asserts decrypt success, payload_schema_version match,
        and that must_preserve_fields are present after decode.
      • Unknown preview fields MUST be preserved on decode (additive policy).
    """
    v4_file = VECTORS_DIR / "vectors_v40_preview.json"
    if not v4_file.exists():
        print("\n[SKIP] v4.0.0-preview.1 suite — file not found")
        return 0, 0

    with open(v4_file) as f:
        data = json.load(f)

    print(f"\n── v4.0.0-preview.1 vectors — spec {data['spec_version']} "
          f"(envelope {data.get('envelope_version', '3.0')}) ──────────────────────────")
    passed = failed = 0

    for v in data["vectors"]:
        vid = v["id"]
        pp = v["passphrase"]
        expected_psv = v.get("expected_payload_schema_version", "4.0.0-preview.1")
        must_preserve = v.get("must_preserve_fields", [])
        expected_payload = v.get("expected_payload", {})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".klickd", delete=False) as tmp:
            json.dump(v["envelope"], tmp)
            tmppath = tmp.name

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = load_klickd(tmppath, pp)

            # 1) payload_schema_version must match
            actual_psv = result.get("payload_schema_version")
            if actual_psv != expected_psv:
                print(f"  FAIL {vid}: payload_schema_version mismatch "
                      f"(expected {expected_psv!r}, got {actual_psv!r})")
                failed += 1
                continue

            # 2) must_preserve fields must be present after decode
            missing = [k for k in must_preserve if k not in result]
            if missing:
                print(f"  FAIL {vid}: missing preserved fields {missing!r}")
                failed += 1
                continue

            # 3) Field values must match expected payload (deep-equal on the keys
            #    listed in must_preserve — covers nested structures like
            #    media_profile, claim_sources, verification_artifacts, etc.).
            mismatched = [
                k for k in must_preserve
                if k in expected_payload and result.get(k) != expected_payload[k]
            ]
            if mismatched:
                print(f"  FAIL {vid}: preserved fields mutated on decode: {mismatched!r}")
                failed += 1
                continue

            print(f"  PASS {vid}: payload_schema_version={actual_psv} "
                  f"preserved={must_preserve}")
            passed += 1

        except tuple(ERROR_MAP.values()) as e:
            print(f"  FAIL {vid}: unexpected {type(e).__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL {vid}: {type(e).__name__}: {e}")
            failed += 1
        finally:
            os.unlink(tmppath)

    return passed, failed


v4_p, v4_f = run_v40_preview_suite()
total_passed += v4_p
total_failed += v4_f


# ── v4 GA strict suite — schema-validation cross-impl (P0-6) ─────────────────
def _get_path(doc, dotted_path):
    """Tiny JSON pointer-ish helper: 'a.b.0.c' navigates dicts and lists."""
    cur = doc
    for seg in dotted_path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(seg)]
            except (ValueError, IndexError):
                return _MISSING
        elif isinstance(cur, dict):
            if seg not in cur:
                return _MISSING
            cur = cur[seg]
        else:
            return _MISSING
    return cur


_MISSING = object()


def run_v40_ga_strict_suite() -> tuple[int, int]:
    """
    Verify v4.0 GA strict vectors (P0-6).

    Each vector is a JSON document validated against either the strict payload
    schema (schemas/klickd-payload-v4.schema.json) or the strict unified schema
    (schema/klickd-v4.schema.json), plus a structural assertions block both
    Python and JS implementations check identically.

    Positive vectors MUST validate successfully and match all assertions.
    Negative vectors MUST FAIL strict validation (jsonschema errors > 0).
    """
    pos_file = VECTORS_DIR / "vectors_v40_ga.json"
    neg_file = VECTORS_DIR / "negative_vectors_v40_ga.json"
    if not pos_file.exists() and not neg_file.exists():
        print("\n[SKIP] v4.0 GA strict suite — vector files not found")
        return 0, 0

    try:
        from jsonschema import Draft202012Validator, RefResolver
    except ImportError:
        print("\n[SKIP] v4.0 GA strict suite — jsonschema not installed (pip install jsonschema)")
        return 0, 0

    repo = REPO_ROOT
    payload_schema = json.loads((repo / "schemas" / "klickd-payload-v4.schema.json").read_text())
    unified_schema = json.loads((repo / "schema" / "klickd-v4.schema.json").read_text())
    store = {payload_schema["$id"]: payload_schema, unified_schema["$id"]: unified_schema}
    resolver = RefResolver.from_schema(unified_schema, store=store)
    payload_validator = Draft202012Validator(payload_schema)
    unified_validator = Draft202012Validator(unified_schema, resolver=resolver)

    passed = failed = 0

    # Positive vectors
    if pos_file.exists():
        pos = json.loads(pos_file.read_text())
        print(f"\n── v4.0 GA strict POSITIVE vectors — spec {pos['spec_version']} (P0-6) ──────────────────────────")
        for v in pos["vectors"]:
            vid = v["id"]
            doc = v["document"]
            behavior = v.get("expected_behavior", "schema_valid")
            against = "unified" if "unified" in behavior else "payload"
            validator = unified_validator if against == "unified" else payload_validator
            errs = list(validator.iter_errors(doc))
            if errs:
                print(f"  FAIL {vid}: expected schema_valid, got {len(errs)} error(s); first: {errs[0].message[:160]}")
                failed += 1
                continue
            # Structural assertions
            mismatched = []
            for path, expected in (v.get("assertions") or {}).items():
                actual = _get_path(doc, path)
                if path.endswith(".length"):
                    base = _get_path(doc, path[: -len(".length")])
                    actual = len(base) if isinstance(base, (list, str, dict)) else None
                if actual != expected:
                    mismatched.append((path, expected, actual))
            if mismatched:
                print(f"  FAIL {vid}: assertion mismatch {mismatched[:3]}")
                failed += 1
            else:
                print(f"  PASS {vid}: strict {against} OK + {len(v.get('assertions') or {})} assertion(s)")
                passed += 1

    # Negative vectors
    if neg_file.exists():
        neg = json.loads(neg_file.read_text())
        print(f"\n── v4.0 GA strict NEGATIVE vectors — spec {neg['spec_version']} (P0-6) ──────────────────────────")
        for v in neg["vectors"]:
            vid = v["id"]
            doc = v["document"]
            against = v.get("against", "payload")
            validator = unified_validator if against == "unified" else payload_validator
            errs = list(validator.iter_errors(doc))
            reason = v.get("failure_reason", "?")
            if errs:
                print(f"  PASS {vid}: strict {against} rejected as expected ({reason}; {len(errs)} err)")
                passed += 1
            else:
                print(f"  FAIL {vid}: expected rejection ({reason}), document validated OK")
                failed += 1

    return passed, failed


v4ga_p, v4ga_f = run_v40_ga_strict_suite()
total_passed += v4ga_p
total_failed += v4ga_f


total = total_passed + total_failed
print(f"\n{'='*50}")
print(f"TOTAL: {total_passed}/{total} passed  ({total_failed} failed)")
sys.exit(0 if total_failed == 0 else 1)
