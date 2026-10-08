import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate
import auditor


class TimingReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text())
        cls.by_id = {x["id"]: x for x in cls.fixture["cases"]}

    def test_valid_row_is_only_eligible_for_timing_gate(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["valid_inside"]), "ELIGIBLE_FOR_TIMING_GATE_ONLY")

    def test_pre_window_execution_is_stop(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["candidate_before_start"]), "STOP_OUTSIDE_ALLOCATION")

    def test_post_window_audit_is_stop(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["auditor_after_end"]), "STOP_OUTSIDE_ALLOCATION")

    def test_pre_execution_report_is_hold(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["report_precedes_candidate"]), "HOLD_REPORT_PRECEDES_EXECUTION")

    def test_ambiguous_or_invalid_inputs_fail_closed(self):
        for name in ("naive_timestamp_missing_offset", "reversed_interval"):
            self.assertNotEqual(candidate.classify(self.fixture, self.by_id[name]), "ELIGIBLE_FOR_TIMING_GATE_ONLY")

    def test_clock_disagreement_and_hash_failure_hold(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["clock_source_disagreement"]), "HOLD_CLOCK_UNMAPPED")
        self.assertEqual(candidate.classify(self.fixture, self.by_id["receipt_hash_mismatch"]), "HOLD_RECEIPT_INTEGRITY")

    def test_half_open_boundary(self):
        self.assertEqual(candidate.classify(self.fixture, self.by_id["touches_exclusive_end"]), "STOP_OUTSIDE_ALLOCATION")
        self.assertEqual(candidate.classify(self.fixture, self.by_id["touches_inclusive_start"]), "ELIGIBLE_FOR_TIMING_GATE_ONLY")

    def test_independent_oracle_agrees_without_importing_candidate(self):
        for row in self.fixture["cases"]:
            self.assertEqual(candidate.classify(self.fixture, row), auditor.oracle(self.fixture, row))

    def test_auditor_rejects_all_planted_corruptions(self):
        expected = [{"id": row["id"], "status": auditor.oracle(self.fixture, row),
                     "candidate": row["candidate"], "auditor": row["auditor"],
                     "reported_at": row["reported_at"], "receipt_sha256": row["receipt_sha256"]}
                    for row in self.fixture["cases"]]
        raw = {"schema": "6532-timing-candidate-v1", "cases": expected}
        self.assertEqual(auditor.independent_mutations(raw, self.fixture), [True] * 4)


if __name__ == "__main__":
    unittest.main()
