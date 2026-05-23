"""Smoke tests for the Hermes POC scaffold.

No provider API calls. No network. Just:
- import the plugin skeleton cleanly without a Hermes install.
- run the wrapper script with --check against the local dry-run runner.

Run from the repo root:
    python -m unittest integrations.hermes.tests.test_wrapper
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
HERMES_DIR = HERE.parent.parent           # integrations/hermes/
REPO_ROOT = HERMES_DIR.parent.parent      # repo root
WRAPPER = HERMES_DIR / "scripts" / "run_context_cost_benchmark.py"
PLUGIN_INIT = HERMES_DIR / "plugin" / "__init__.py"


class PluginImportTests(unittest.TestCase):
    def test_plugin_module_imports_without_hermes(self):
        spec = importlib.util.spec_from_file_location(
            "klickd_hermes_plugin", PLUGIN_INIT
        )
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertEqual(module.PLUGIN_NAME, "klickd-context-cost")
        self.assertTrue(module.PLUGIN_VERSION.startswith("0."))

        # register() must be safe to call with no host.
        result = module.register(host=None)
        self.assertEqual(result["plugin"], "klickd-context-cost")
        self.assertTrue(result["experimental"])
        self.assertEqual(result["registered_hooks"], [])

    def test_safety_preflight_refuses_network(self):
        spec = importlib.util.spec_from_file_location(
            "klickd_hermes_plugin", PLUGIN_INIT
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        ok = module.on_skill_invoke({"network_allowed": False})
        self.assertTrue(ok["allow"])
        self.assertEqual(ok["refusals"], [])

        denied = module.on_skill_invoke({"network_allowed": True})
        self.assertFalse(denied["allow"])
        self.assertTrue(any("network" in r for r in denied["refusals"]))

    def test_safety_preflight_refuses_secrets(self):
        spec = importlib.util.spec_from_file_location(
            "klickd_hermes_plugin", PLUGIN_INIT
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        denied = module.on_skill_invoke({
            "klickd_payload": {"api_key": "should-never-be-here"},
        })
        self.assertFalse(denied["allow"])
        self.assertTrue(any("secret" in r.lower() for r in denied["refusals"]))


class WrapperScriptTests(unittest.TestCase):
    def test_wrapper_check_succeeds(self):
        self.assertTrue(WRAPPER.is_file(), f"wrapper missing: {WRAPPER}")
        result = subprocess.run(
            [sys.executable, str(WRAPPER), "--check"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("dry-run only", result.stdout)
        self.assertIn("fixture check", result.stdout)


if __name__ == "__main__":
    unittest.main()
