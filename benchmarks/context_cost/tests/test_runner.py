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


if __name__ == "__main__":
    unittest.main()
