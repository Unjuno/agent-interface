import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import auditor
import candidate


class Allocation02Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text())

    def test_candidate_and_independent_oracle_agree_on_all_cases(self):
        for row in self.fixture["cases"]:
            self.assertEqual(candidate.classify(self.fixture, row), auditor.oracle(self.fixture, row), row["id"])

    def test_only_fully_contained_and_boundary_start_rows_are_eligible(self):
        eligible = [row["id"] for row in self.fixture["cases"]
                    if candidate.classify(self.fixture, row) == "ELIGIBLE_FOR_TIMING_GATE_ONLY"]
        self.assertEqual(eligible, ["valid_inside", "touches_inclusive_start"])

    def test_wrong_hash_missing_offset_clock_conflict_and_bad_interval_fail_closed(self):
        got = {row["id"]: candidate.classify(self.fixture, row) for row in self.fixture["cases"]}
        self.assertEqual(got["receipt_hash_mismatch"], "HOLD_RECEIPT_INTEGRITY")
        self.assertEqual(got["naive_timestamp_missing_offset"], "HOLD_INVALID_OR_AMBIGUOUS_TIME")
        self.assertEqual(got["clock_source_disagreement"], "HOLD_CLOCK_UNMAPPED")
        self.assertEqual(got["reversed_interval"], "STOP_INVALID_INTERVAL")

    def test_raw_only_mutation_controls_reject_four_corruptions(self):
        rows = []
        for row in self.fixture["cases"]:
            raw = dict(row)
            raw.setdefault("receipt_sha256", auditor.digest(row))
            rows.append({**raw, "status": auditor.oracle(self.fixture, raw)})
        self.assertEqual(auditor.mutation_checks({"cases": rows}, self.fixture), [True] * 4)

    def test_cli_help_is_safe_and_has_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate.json"
            proc = subprocess.run([sys.executable, str(HERE / "candidate.py"), "--help"],
                                  check=False, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--fixture", proc.stdout)
            self.assertFalse(output.exists())

    def test_formal_run_directory_is_not_created_by_construction_suite(self):
        self.assertFalse((HERE / "results").exists())


if __name__ == "__main__":
    unittest.main()
