"""Construction checks only; the one-shot subprocesses live in run_formal.py."""

from __future__ import annotations

import unittest

import candidate
from audit import audit_document
from build_fixture import build


class ExactIPCWConstructionTests(unittest.TestCase):
    def test_full_enumeration_reconstructs_exact_target(self) -> None:
        public, truth = build()
        output = candidate.calculate(public)
        audit = audit_document(public, truth, output)
        self.assertEqual(len(public["ipcw_cases"]), 64)
        self.assertEqual(audit["exact_probability_mass"], "1/1")
        self.assertEqual(audit["exact_ipcw_expectation"], "1/2")
        self.assertEqual(audit["true_design_risk"], "1/2")
        self.assertEqual(audit["disposition"], "PASS_METHOD_SCOPED")

    def test_candidate_marks_only_superpopulation_estimand(self) -> None:
        public, _ = build()
        output = candidate.calculate(public)
        self.assertEqual(len(output["cases"]), 64)
        self.assertTrue(
            all(
                row["estimand"] == "SUPERPOPULATION_EXPECTED_ERROR_RISK"
                and row["finite_cohort_point_claim"] is None
                and row["estimate"] is not None
                for row in output["cases"]
            )
        )
        self.assertEqual(output["zero_support"]["status"], "UNKNOWN_NONPOSITIVITY")
        self.assertIsNone(output["zero_support"]["estimate"])

    def test_all_six_frozen_mutations_are_rejected(self) -> None:
        public, truth = build()
        output = candidate.calculate(public)
        audit = audit_document(public, truth, output)
        self.assertEqual(len(audit["mutation_controls"]), 6)
        self.assertTrue(all(row["rejected"] for row in audit["mutation_controls"].values()))


if __name__ == "__main__":
    unittest.main()
