#!/usr/bin/env python3
"""Root compatibility wrapper for the cross-impl vector runner.

The canonical implementation now lives at ``scripts/verify_vectors.py``. This
thin wrapper preserves the documented public entry point ``python
verify_vectors.py`` (used by CI, CONTRIBUTING.md, and the v4.1 evidence-pack
tooling) by delegating to the relocated module.
"""
import runpy
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "scripts" / "verify_vectors.py"
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
