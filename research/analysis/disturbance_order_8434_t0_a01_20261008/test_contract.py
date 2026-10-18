"""Behavioral contract for the finite disturbance-order method experiment."""

import copy
import json
import unittest
from pathlib import Path

from audit import audit_document
from candidate import build_raw, evaluate_schedule


PACKAGE = Path(__file__).parent
SOURCE_BYTES = (PACKAGE / "SOURCE.json").read_bytes()
SOURCE = json.loads(SOURCE_BYTES)


def raw_fixture():
    return build_raw(SOURCE, SOURCE_BYTES)


class DisturbanceOrderContractTests(unittest.TestCase):
    def test_equal_marginal_orderings_can_reverse_fixed_route_ranking(self):
        clustered = ["A"] * 8 + ["B"] * 8 + ["A"] * 8 + ["B"] * 8
        alternating = [label for _ in range(16) for label in ("A", "B")]

        clustered_result = evaluate_schedule(clustered)
        alternating_result = evaluate_schedule(alternating)

        self.assertEqual(clustered_result["label_counts"], {"A": 16, "B": 16})
        self.assertEqual(alternating_result["label_counts"], {"A": 16, "B": 16})
        self.assertEqual(clustered_result["opportunity_count"], 32)
        self.assertEqual(alternating_result["opportunity_count"], 32)
        self.assertEqual(clustered_result["routes"]["switch_reconfigure"]["safe_effects"], 28)
        self.assertEqual(clustered_result["routes"]["two_step_cache"]["safe_effects"], 7)
        self.assertEqual(alternating_result["routes"]["switch_reconfigure"]["safe_effects"], 0)
        self.assertEqual(alternating_result["routes"]["two_step_cache"]["safe_effects"], 31)
        self.assertEqual(clustered_result["routes"]["null_a"]["safe_effects"], 32)
        self.assertEqual(clustered_result["routes"]["null_b"]["safe_effects"], 32)

    def test_independent_auditor_accepts_complete_source_bound_fixture(self):
        result = audit_document(SOURCE_BYTES, raw_fixture())
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["case_count"], 96)
        self.assertTrue(result["heldout_crossover"])
        self.assertIn("clustered", result["heldout_positive_structures"])
        self.assertIn("alternating", result["heldout_negative_structures"])

    def test_audit_reports_strata_so_pooled_mean_cannot_hide_sign_reversal(self):
        result = audit_document(SOURCE_BYTES, raw_fixture())
        self.assertGreaterEqual(result["heldout_deltas"]["clustered"]["median_paired_delta"], 4)
        self.assertLessEqual(result["heldout_deltas"]["alternating"]["median_paired_delta"], -4)
        self.assertEqual(result["heldout_deltas"]["heldout_block"]["median_paired_delta"], 27)

    def test_auditor_rejects_omitted_case(self):
        raw = raw_fixture()
        raw["cases"].pop()
        self.assertEqual(audit_document(SOURCE_BYTES, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_duplicate_case(self):
        raw = raw_fixture()
        raw["cases"].append(copy.deepcopy(raw["cases"][0]))
        self.assertEqual(audit_document(SOURCE_BYTES, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_equal_marginal_order_relabel(self):
        raw = raw_fixture()
        case = raw["cases"][0]
        case["schedule"][0], case["schedule"][1] = case["schedule"][1], case["schedule"][0]
        self.assertEqual(audit_document(SOURCE_BYTES, raw)["status"], "FAIL_METHOD")

    def test_auditor_rejects_denominator_and_outcome_mutations(self):
        raw = raw_fixture()
        raw["cases"][0]["opportunity_count"] -= 1
        self.assertEqual(audit_document(SOURCE_BYTES, raw)["status"], "FAIL_METHOD")

        raw = raw_fixture()
        raw["cases"][0]["routes"]["switch_reconfigure"]["safe_effects"] += 1
        self.assertEqual(audit_document(SOURCE_BYTES, raw)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
