import copy
import json
from pathlib import Path
import unittest

from audit_truth import audit


HERE = Path(__file__).resolve().parent
T1 = HERE.parent / "same_cohort_negative_control_5841_t1_v1"
FIXTURE = json.loads((HERE / "inputs" / "T1_fixture.json").read_text(encoding="utf-8"))
RAW = json.loads((T1 / "results" / "candidate.stdout.json").read_text(encoding="utf-8"))


class FixtureDerivedTruthAuditTests(unittest.TestCase):
    def test_retained_raw_reconstructs_all_truth_and_observed_rows(self):
        result = audit(FIXTURE, RAW)
        self.assertEqual(result["status"], "PASS_FIXTURE_DERIVED_RAW")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["case_count"], 7)
        self.assertEqual(result["row_count"], 56)
        self.assertEqual(result["reconstructed_truth_labels"], 56)

    def test_detects_single_primary_truth_flip_without_changing_rates(self):
        mutated = copy.deepcopy(RAW)
        target = next(item for item in mutated["cases"] if item["case_id"] == "clean_null")
        target["rows"][0]["ground_truth"]["primary"] = False
        result = audit(FIXTURE, mutated)
        self.assertTrue(any(error.endswith(":ground_truth_mismatch") for error in result["errors"]))

    def test_detects_truth_swap_even_when_aggregate_primary_count_is_preserved(self):
        mutated = copy.deepcopy(RAW)
        target = next(item for item in mutated["cases"] if item["case_id"] == "clean_null")
        target["rows"][0]["ground_truth"]["primary"], target["rows"][2]["ground_truth"]["primary"] = (
            target["rows"][2]["ground_truth"]["primary"], target["rows"][0]["ground_truth"]["primary"]
        )
        result = audit(FIXTURE, mutated)
        self.assertEqual(sum(r["ground_truth"]["primary"] for r in target["rows"][:4]), 2)
        self.assertTrue(any(error.endswith(":ground_truth_mismatch") for error in result["errors"]))

    def test_detects_clean_sentinel_truth_flip(self):
        mutated = copy.deepcopy(RAW)
        target = next(item for item in mutated["cases"] if item["case_id"] == "clean_null")
        target["rows"][0]["ground_truth"]["sentinel"] = True
        result = audit(FIXTURE, mutated)
        self.assertTrue(any(error.endswith(":ground_truth_mismatch") for error in result["errors"]))

    def test_detects_collateral_truth_flip(self):
        mutated = copy.deepcopy(RAW)
        target = next(item for item in mutated["cases"] if item["case_id"] == "true_collateral")
        target["rows"][7]["ground_truth"]["collateral"] = False
        result = audit(FIXTURE, mutated)
        self.assertTrue(any(error.endswith(":ground_truth_mismatch") for error in result["errors"]))

    def test_detects_missing_truth_label(self):
        mutated = copy.deepcopy(RAW)
        target = next(item for item in mutated["cases"] if item["case_id"] == "true_collateral")
        del target["rows"][7]["ground_truth"]["sentinel"]
        result = audit(FIXTURE, mutated)
        self.assertTrue(any(error.endswith(":ground_truth_mismatch") for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
