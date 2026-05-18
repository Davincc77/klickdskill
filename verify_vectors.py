#!/usr/bin/env python3
"""Cross-impl test runner for .klickd v2.5 test vectors (positive + negative)."""
import json, sys, os, tempfile, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_klickd import (
    KlickdWeakPassphraseError,
    load_klickd, KlickdAuthError, KlickdVersionError, KlickdFormatError, KlickdError
)

VECTORS_DIR = Path(__file__).parent / "tests"

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

total = total_passed + total_failed
print(f"\n{'='*50}")
print(f"TOTAL: {total_passed}/{total} passed  ({total_failed} failed)")
sys.exit(0 if total_failed == 0 else 1)
