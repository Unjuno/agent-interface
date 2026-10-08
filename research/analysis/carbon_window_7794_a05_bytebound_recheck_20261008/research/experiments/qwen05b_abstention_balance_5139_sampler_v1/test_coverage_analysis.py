"""Prove pre-outcome template/field matching is feasible on the fixed fixture."""
from __future__ import annotations

import unittest

from coverage_analysis import analyze


class CoverageAnalysisTests(unittest.TestCase):
    def test_hash_rank_realized_coverage_is_reported_without_seed_search(self):
        result = analyze()
        self.assertFalse(result["seed_search"])
        self.assertEqual(result["current_hash_rank"]["balanced_set"]["n"], 4)
        self.assertEqual(result["current_hash_rank"]["imbalanced_set"]["n"], 16)
        self.assertEqual(result["current_hash_rank"]["heldout_prefix"]["n"], 8)
        for key in ("template", "field"):
            self.assertEqual(sum(result["current_hash_rank"]["balanced_set"][key].values()), 4)
            self.assertEqual(sum(result["current_hash_rank"]["imbalanced_set"][key].values()), 16)
            self.assertEqual(sum(result["current_hash_rank"]["heldout_prefix"][key].values()), 8)

    def test_stratified_support_prefixes_match_both_marginals_and_are_nested(self):
        candidate = analyze()["stratified_candidate"]
        balanced, imbalanced = candidate["balanced_set"], candidate["imbalanced_set"]
        self.assertEqual(balanced["template"], {"0": 1, "1": 1, "2": 1, "3": 1})
        self.assertEqual(balanced["field"], {
            "digest_frequency": 1, "display_name": 1,
            "sharing_visibility": 1, "timezone": 1,
        })
        self.assertEqual(imbalanced["template"], {"0": 4, "1": 4, "2": 4, "3": 4})
        self.assertEqual(imbalanced["field"], {
            "digest_frequency": 4, "display_name": 4,
            "sharing_visibility": 4, "timezone": 4,
        })
        self.assertTrue(candidate["support_nested"])

    def test_stratified_common_heldout_covers_each_template_and_field_twice(self):
        candidate = analyze()["stratified_candidate"]
        self.assertEqual(candidate["heldout_set"]["n"], 8)
        self.assertEqual(candidate["heldout_set"]["template"], {"0": 2, "1": 2, "2": 2, "3": 2})
        self.assertEqual(candidate["heldout_set"]["field"], {
            "digest_frequency": 2, "display_name": 2,
            "sharing_visibility": 2, "timezone": 2,
        })
        self.assertTrue(candidate["heldout_rows_shared"])


if __name__ == "__main__":
    unittest.main()
