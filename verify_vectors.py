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

total = total_passed + total_failed
print(f"\n{'='*50}")
print(f"TOTAL: {total_passed}/{total} passed  ({total_failed} failed)")
sys.exit(0 if total_failed == 0 else 1)
