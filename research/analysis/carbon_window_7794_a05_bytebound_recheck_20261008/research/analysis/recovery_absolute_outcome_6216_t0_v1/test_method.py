#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent


class RecoveryAbsoluteOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))

    def test_candidate_matches_independent_difference_walk(self):
        result = candidate.run(self.data)
        self.assertTrue(auditor.audit(self.data, result)["candidate_exact_match"])

    def test_ordinal_identity_absolute_separation(self):
        result = auditor.expected_result(self.data)
        hi, lo = result["regimes"]["high_success"], result["regimes"]["low_success"]
        self.assertTrue(all(a["winner_set_counts"] == b["winner_set_counts"] for a, b in zip(hi, lo)))
        self.assertTrue(all(a["pooled_success"] != b["pooled_success"] for a, b in zip(hi, lo)))
        self.assertTrue(all(a["all_zero"] != b["all_zero"] for a, b in zip(hi, lo)))

    def test_checkpoint_permutation_preserves_marginals_not_binding(self):
        r = auditor.expected_result(self.data)["checkpoint_binding"]
        self.assertEqual(r["base"]["marginal_successes"], r["permuted"]["marginal_successes"])
        self.assertEqual((r["base"]["correct"], r["permuted"]["correct"]), (2, 0))

    def test_yield_forbidden_and_missing_label_types(self):
        r = auditor.expected_result(self.data)["controls"]
        self.assertTrue(r["yield_correct"])
        self.assertTrue(r["forbidden_effect_refused"])
        self.assertEqual((r["selective_labels"]["lower"], r["selective_labels"]["upper"]), ({"numerator": 1, "denominator": 4}, {"numerator": 3, "denominator": 4}))
        self.assertFalse(r["selective_labels"]["rejected_outcomes_imputed"])

    def test_frozen_mutation_controls(self):
        candidate_result = candidate.run(self.data)
        audit = auditor.audit(self.data, candidate_result)
        self.assertTrue(audit["pass"])
        self.assertEqual(sum(audit["mutations_rejected"].values()), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
