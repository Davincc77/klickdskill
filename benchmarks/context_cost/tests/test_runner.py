# Tests for the RFC-003 dry-run runner. No provider calls, no network.
#
# Run from repo root:
#   python -m unittest benchmarks.context_cost.tests.test_runner

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import sys

THIS_DIR = Path(__file__).resolve().parent
BENCH_DIR = THIS_DIR.parent
sys.path.insert(0, str(BENCH_DIR))

import runner  # noqa: E402


class FixtureValidationTests(unittest.TestCase):
    def test_validate_fixtures_passes(self):
        result = runner.validate_fixtures()
        self.assertEqual(result["flow_message_count"], runner.EXPECTED_FLOW_MESSAGES)
        self.assertGreater(len(result["continuity_facts"]), 0)
        for fact in result["continuity_facts"]:
            self.assertTrue(fact["present_in_baseline"], msg=fact["id"])
            self.assertTrue(fact["present_in_klickd"], msg=fact["id"])

    def test_whitespace_proxy_is_deterministic(self):
        a = runner._whitespace_tokens("hello world foo")
        b = runner._whitespace_tokens("hello world foo")
        self.assertEqual(a, b)
        self.assertEqual(a, 3)
        self.assertEqual(runner._whitespace_tokens(""), 0)
        self.assertEqual(runner._whitespace_tokens("   "), 0)


class RunOutputTests(unittest.TestCase):
    def test_run_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            res = runner.run(out_root=tmp_root, date_override="2026-05-22")
            out_dir = tmp_root / "2026-05-22"
            self.assertTrue((out_dir / "summary.csv").is_file())
            self.assertTrue((out_dir / "raw_runs.jsonl").is_file())
            self.assertTrue((out_dir / "report.md").is_file())
            self.assertTrue((out_dir / "artifacts" / "sample_test.log").is_file())

            with (out_dir / "summary.csv").open() as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(rows[0][0], "message_id")
            # 10 message rows + 1 header + 1 total row.
            self.assertEqual(len(rows), 12)
            self.assertEqual(rows[-1][0], "TOTAL")

            with (out_dir / "raw_runs.jsonl").open() as fh:
                lines = [json.loads(line) for line in fh if line.strip()]
            # 10 messages * 3 conditions.
            self.assertEqual(len(lines), 30)
            for entry in lines:
                self.assertIn(entry["condition"], runner.CONDITIONS)
                self.assertIn("NOT a provider token count", entry["note"])

            # paste condition repeats the full system prompt as a leading user
            # message, so paste total must exceed cold total.
            totals = res["proxy"]["per_condition_total"]
            self.assertGreater(totals["paste"], totals["cold"])

    def test_check_mode_exit_code(self):
        rc = runner.main(["--check"])
        self.assertEqual(rc, 0)


class ExtendedMetricsTests(unittest.TestCase):
    def _load_inputs(self):
        system_prompt = runner._load_text(runner.REQUIRED_FIXTURES["baseline_system_prompt"])
        klickd_ctx = runner._load_json(runner.REQUIRED_FIXTURES["klickd_sample_context"])
        flow = runner._load_json(runner.REQUIRED_FIXTURES["flow"])
        return runner._build_condition_inputs(system_prompt, klickd_ctx, flow), klickd_ctx

    def test_heuristic_token_estimate_is_deterministic_and_positive(self):
        self.assertEqual(runner._heuristic_input_token_estimate(""), 0)
        self.assertEqual(runner._heuristic_input_token_estimate("   "), 0)
        self.assertGreater(runner._heuristic_input_token_estimate("hello world"), 0)
        self.assertEqual(
            runner._heuristic_input_token_estimate("a" * 40),
            runner._heuristic_input_token_estimate("a" * 40),
        )

    def test_prompt_size_bytes_handles_utf8(self):
        self.assertEqual(runner._prompt_size_bytes(""), 0)
        self.assertEqual(runner._prompt_size_bytes("Léa"), len("Léa".encode("utf-8")))

    def test_extended_metrics_shape_and_invariants(self):
        inputs, klickd_ctx = self._load_inputs()
        ext = runner.compute_extended_metrics(inputs, klickd_ctx)

        for c in runner.CONDITIONS:
            t = ext["per_condition_total"][c]
            for k in (
                "input_token_estimate_heuristic",
                "prompt_size_bytes",
                "whitespace_tokens",
            ):
                self.assertGreaterEqual(t[k], 0, msg=f"{c}.{k}")

        cold = ext["per_condition_total"]["cold"]
        paste = ext["per_condition_total"]["paste"]
        klickd_t = ext["per_condition_total"]["klickd"]
        self.assertGreater(paste["prompt_size_bytes"], cold["prompt_size_bytes"])
        self.assertGreater(klickd_t["prompt_size_bytes"], cold["prompt_size_bytes"])

        cont = ext["continuity_fields_present"]
        self.assertEqual(cont["present_count"], cont["total_count"])

        gate = ext["gate_decision_presence"]
        self.assertGreater(gate["decisions_locked_count"], 0)
        self.assertTrue(gate["has_ethics_lock"])

        warns = ext["missing_evidence_warnings"]
        self.assertIsInstance(warns, list)
        # The fixture has an empty verification_artifacts.records, so we
        # expect exactly one warning describing that.
        joined = " | ".join(warns)
        self.assertIn("verification_artifacts.records is empty", joined)

    def test_missing_evidence_warnings_on_absent_block(self):
        warns = runner._missing_evidence_warnings({})
        self.assertIn("verification_artifacts block absent", warns)


class ChimeraExtrapolationTests(unittest.TestCase):
    def test_extrapolation_default_packs_and_savings(self):
        result = runner.chimera_v41_extrapolation(klickd_baseline_tokens=1000)
        self.assertEqual(len(result["assumptions"]["default_packs"]), 7)
        self.assertGreater(
            result["base_plus_seven"]["total_tokens"],
            result["router_selected"]["total_tokens"],
        )
        self.assertGreater(result["expected_savings"]["tokens"], 0)
        self.assertGreater(result["expected_savings"]["pct_vs_base_plus_seven"], 0)
        self.assertLess(result["expected_savings"]["pct_vs_base_plus_seven"], 1)

    def test_extrapolation_custom_costs_and_router(self):
        custom = {p: 500 for p in runner.DEFAULT_CHIMERA_PACKS}
        result = runner.chimera_v41_extrapolation(
            klickd_baseline_tokens=2000,
            pack_token_costs=custom,
            router_selection=("core.Code",),
        )
        # base + 7 * 500 + 2000 = 5500; router: 2000 + 500 = 2500.
        self.assertEqual(result["base_plus_seven"]["total_tokens"], 2000 + 7 * 500)
        self.assertEqual(result["router_selected"]["total_tokens"], 2000 + 500)
        self.assertEqual(result["expected_savings"]["tokens"], 6 * 500)

    def test_extrapolation_zero_baseline_does_not_divide_by_zero(self):
        result = runner.chimera_v41_extrapolation(
            klickd_baseline_tokens=0,
            pack_token_costs={p: 0 for p in runner.DEFAULT_CHIMERA_PACKS},
        )
        self.assertEqual(result["expected_savings"]["pct_vs_base_plus_seven"], 0.0)


class FullRunEmitsExtendedOutputsTests(unittest.TestCase):
    def test_run_writes_extended_and_extrapolation_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            res = runner.run(out_root=tmp_root, date_override="2026-05-25")
            out_dir = tmp_root / "2026-05-25"
            self.assertTrue((out_dir / "extended_metrics.json").is_file())
            self.assertTrue((out_dir / "chimera_v41_extrapolation.json").is_file())

            ext = json.loads((out_dir / "extended_metrics.json").read_text())
            self.assertIn("per_condition_total", ext)
            self.assertIn("context_duplication_avoided", ext)

            ext_paths = res["paths"]
            self.assertIn("extended_metrics_json", ext_paths)
            self.assertIn("chimera_v41_extrapolation_json", ext_paths)

            report = (out_dir / "report.md").read_text()
            self.assertIn("Extended metrics", report)
            self.assertIn("Chimera.klickd v4.1", report)


if __name__ == "__main__":
    unittest.main()
