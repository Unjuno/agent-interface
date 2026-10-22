from __future__ import annotations

import unittest

import auditor
import candidate


def public_one(a_resolved: int, a_errors: int, b_resolved: int, b_errors: int) -> dict:
    return {"schema": "unjuno.issue8049.public.v1", "cohorts": [{"cohort": 0, "strata": {
        "A": {"resolved_mask": f"{a_resolved:050x}", "resolved_error_mask": f"{a_errors:050x}"},
        "B": {"resolved_mask": f"{b_resolved:050x}", "resolved_error_mask": f"{b_errors:050x}"},
    }}]}


class ProtocolTests(unittest.TestCase):
    def test_exact_design_variance_reduces_by_fixed_stratum_allocation(self):
        expected = ((0.40 / 0.25 - 0.40**2) + (0.10 / 0.75 - 0.10**2)) / 800
        self.assertAlmostEqual(expected, 0.0019541666666666668)

    def test_candidate_reads_only_public_and_calculates_stratified_estimate(self):
        pub = public_one((1 << 200) - 1, (1 << 80) - 1, (1 << 200) - 1, (1 << 20) - 1)
        got = candidate.estimate(pub)["records"][0]
        expected = (80 / 0.25 + 20 / 0.75) / 400
        self.assertAlmostEqual(got["ht"], expected)
        self.assertTrue(0 <= got["ht_lo"] <= got["ht_hi"] <= 1)
        self.assertAlmostEqual(got["cc"], 0.25)

    def test_auditor_reconstructs_observed_label_identity(self):
        pub = public_one(1, 1, 1, 0)
        truth = {"schema": "unjuno.issue8049.oracle.v1", "cohorts": [{"cohort": 0, "strata": {
            "A": {"outcome_mask": f"{1:050x}"}, "B": {"outcome_mask": f"{0:050x}"},
        }}]}
        row = auditor.reconstruct_one(pub["cohorts"][0], truth["cohorts"][0])
        self.assertEqual(row["ht"], (1 / 0.25) / 400)
        truth["cohorts"][0]["strata"]["A"]["outcome_mask"] = f"{0:050x}"
        with self.assertRaises(ValueError):
            auditor.reconstruct_one(pub["cohorts"][0], truth["cohorts"][0])


if __name__ == "__main__":
    unittest.main()
