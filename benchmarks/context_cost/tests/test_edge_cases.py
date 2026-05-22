# Lightweight tests for the optional edge-case fixtures under
# benchmarks/context_cost/fixtures/edge_cases/. These fixtures are NOT consumed
# by the v1 dry-run runner; this test just verifies they are valid JSON and
# match the structural checks declared in
# fixtures/validation/edge_ground_truth.json.
#
# Run from repo root:
#   python -m unittest benchmarks.context_cost.tests.test_edge_cases

from __future__ import annotations

import json
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
BENCH_DIR = THIS_DIR.parent
FIXTURES = BENCH_DIR / "fixtures"
EDGE = FIXTURES / "edge_cases"
EDGE_GT = FIXTURES / "validation" / "edge_ground_truth.json"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class EdgeGroundTruthTests(unittest.TestCase):
    def test_edge_ground_truth_parses(self):
        data = _load_json(EDGE_GT)
        self.assertEqual(data.get("fixture_version"), "1")
        self.assertIn("scenarios", data)
        self.assertEqual(
            set(data["scenarios"].keys()),
            {"migration_version_break", "tool_call_failure_recovery", "multi_session_handoff"},
        )


class MigrationVersionBreakTests(unittest.TestCase):
    def setUp(self):
        self.ctx = _load_json(EDGE / "migration_version_break" / "context.json")
        self.report = _load_json(
            EDGE / "migration_version_break" / "expected_migration_report.json"
        )

    def test_source_version_is_pre_v4(self):
        self.assertTrue(str(self.ctx["klickd_version"]).startswith("3."))

    def test_no_v4_only_fields_in_source(self):
        self.assertNotIn("handoff", self.ctx.get("context", {}))
        self.assertNotIn("verification_artifacts", self.ctx)

    def test_report_has_no_data_loss(self):
        self.assertFalse(self.report["data_loss"])

    def test_report_warns_for_v4_only_fields(self):
        codes = {w["code"] for w in self.report.get("warnings", [])}
        self.assertIn("missing_field.handoff", codes)
        self.assertIn("missing_field.verification_artifacts", codes)

    def test_decisions_preserved(self):
        self.assertIn("context.decisions_locked", self.report["preserved_fields"])


class ToolCallFailureRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.scenario = _load_json(
            EDGE / "tool_call_failure_recovery" / "scenario.json"
        )

    def test_first_tool_call_failed(self):
        turn = self.scenario["turns"][1]
        self.assertEqual(turn["role"], "agent_action")
        self.assertEqual(turn["result"]["status"], "error")
        self.assertEqual(turn["result"]["error_code"], "transient_error_500")

    def test_artifact_pointer_resolves(self):
        rel = self.scenario["turns"][1]["result"]["artifact_path"]
        artifact = BENCH_DIR.parent.parent / rel
        self.assertTrue(artifact.is_file(), f"missing artifact: {artifact}")
        self.assertIn("tool_call.result", artifact.read_text(encoding="utf-8"))

    def test_forbidden_behaviors_include_blind_retry_and_fabrication(self):
        forbidden = set(self.scenario["turns"][2]["forbidden_behaviors"])
        self.assertIn("silent_blind_retry", forbidden)
        self.assertIn("fabricate_task_list_without_tool_result", forbidden)


class MultiSessionHandoffTests(unittest.TestCase):
    def setUp(self):
        self.data = _load_json(EDGE / "multi_session_handoff" / "sessions.json")

    def test_three_sessions(self):
        self.assertEqual(len(self.data["sessions"]), 3)

    def test_resume_session_has_no_new_decisions(self):
        self.assertEqual(self.data["sessions"][-1]["decisions_made"], [])

    def test_minimum_resume_context_is_substantive(self):
        self.assertGreaterEqual(len(self.data["expected_resume_minimum_context"]), 4)

    def test_forbids_asking_lea_to_reexplain(self):
        self.assertIn(
            "ask_lea_to_re_explain_project",
            self.data["forbidden_resume_behaviors"],
        )


if __name__ == "__main__":
    unittest.main()
