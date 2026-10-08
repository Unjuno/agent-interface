import copy
import tempfile
import unittest
from pathlib import Path

import auditor
import candidate


class OrderedContextCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raw = candidate.main(Path(self.temp.name) / "out")
        self.result = auditor.audit(self.raw)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_mixed_denominator_and_equal_budget(self):
        self.assertEqual(self.result["errors"], [])
        self.assertTrue(self.result["coverage_exact"])
        self.assertEqual(self.result["legal_pair_denominator"], 10)
        self.assertEqual(self.result["mixed_rows"], 40)
        self.assertEqual(self.result["exhaustive_context_pair_rows"], 80)
        self.assertEqual(self.result["separate_equal_budget_rows"], 40)
        self.assertEqual(self.result["mixed_rows"], self.result["separate_equal_budget_rows"])

    def test_joint_fault_is_only_seen_by_mixed_suite(self):
        d = self.result["detects"]
        self.assertTrue(d["joint"]["mixed_occ"])
        self.assertFalse(d["joint"]["separate_equal_budget"])
        self.assertTrue(d["factor"]["separate_equal_budget"])
        self.assertTrue(d["order"]["separate_equal_budget"])
        self.assertTrue(d["order_invariant"]["mixed_occ"])
        self.assertTrue(d["order_invariant"]["separate_equal_budget"])

    def test_context_stratum_collapse_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        for row in raw["rows"]:
            if row["suite"] == "mixed_occ":
                row["context"][0] = 0
        self.assertIn("mixed-denominator-mismatch", auditor.audit(raw)["errors"])

    def test_impossible_release_before_action_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw["rows"] if r["suite"] == "mixed_occ")
        row["history"] = ["RELEASE", "OBSERVE"]
        result = auditor.audit(raw)
        self.assertTrue(any("outside-independent-universe" in e for e in result["errors"]))

    def test_fake_expected_universe_metadata_cannot_change_oracle(self):
        raw = copy.deepcopy(self.raw)
        raw["fixture"]["pair_histories"] = [["OBSERVE", "OBSERVE"]]
        self.assertTrue(auditor.audit(raw)["coverage_exact"])
        raw["rows"] = [r for r in raw["rows"]
                       if not (r["suite"] == "mixed_occ" and r["history"] == ["REVOKE", "ACT"])]
        self.assertIn("mixed-denominator-mismatch", auditor.audit(raw)["errors"])


if __name__ == "__main__":
    unittest.main()
