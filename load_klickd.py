"""Root compatibility shim for the reference decoder.

The canonical implementation now lives at ``scripts/load_klickd.py``. This shim
keeps ``import load_klickd`` working for code that places the repository root on
``PYTHONPATH`` (e.g. ``demo/demo_soul_handoff.py``) by loading the relocated
module and re-exporting its public names.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

_TARGET = _Path(__file__).resolve().parent / "scripts" / "load_klickd.py"
_spec = _ilu.spec_from_file_location("_klickd_load_impl", _TARGET)
_mod = _ilu.module_from_spec(_spec)
_sys.modules["_klickd_load_impl"] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
