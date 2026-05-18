#!/usr/bin/env python3
"""Cross-impl test runner for .klickd v2.5 test vectors."""
import json, sys, os, tempfile, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_klickd import load_klickd, KlickdAuthError

VECTORS_FILE = Path(__file__).parent / "tests" / "vectors.json"

with open(VECTORS_FILE) as f:
    data = json.load(f)

print(f".klickd test vectors — spec {data['spec_version']}")
passed = failed = 0

for v in data["vectors"]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.klickd', delete=False) as tmp:
        json.dump(v["envelope"], tmp)
        tmppath = tmp.name
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = load_klickd(tmppath, v["passphrase"])
        if "KlickdAuthError" in v.get("expected_behavior", ""):
            print(f"  FAIL {v['id']}: expected auth error, got success"); failed += 1
        else:
            dn = result.get("display_name", "?")
            warn = " [warned:short-passphrase]" if w else ""
            print(f"  PASS {v['id']}: display_name={dn!r}{warn}"); passed += 1
    except KlickdAuthError:
        if "KlickdAuthError" in v.get("expected_behavior", ""):
            print(f"  PASS {v['id']}: KlickdAuthError as expected"); passed += 1
        else:
            print(f"  FAIL {v['id']}: unexpected KlickdAuthError"); failed += 1
    except Exception as e:
        print(f"  FAIL {v['id']}: {type(e).__name__}: {e}"); failed += 1
    finally:
        os.unlink(tmppath)

print(f"\n{passed}/{passed+failed} passed")
sys.exit(0 if failed == 0 else 1)
