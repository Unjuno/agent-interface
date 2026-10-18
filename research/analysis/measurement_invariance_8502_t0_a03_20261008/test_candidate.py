"""Construction tests fixed before the A03 candidate source was written."""
import unittest
import json
from pathlib import Path

from candidate import max_cutpoint_gap, run, screen_rows
from generate import generate


class ThresholdGapTests(unittest.TestCase):
    def test_uses_same_cutpoint_differences_not_difference_of_group_maxima(self):
        # A CDF: .50, .90, .95, .99; B CDF: .10, .50, .90, .95.
        # The correct maximum paired-cutpoint gap is .40; the old defective
        # difference-of-maxima formula would return .04.
        counts_a = [50, 40, 5, 4, 1]
        counts_b = [10, 40, 40, 5, 5]
        self.assertAlmostEqual(max_cutpoint_gap(counts_a, counts_b), 0.40)

    def test_sparse_rows_are_uncertain_before_any_effect_screen(self):
        rows = [[0, 0, 0, 0, 0, 0] for _ in range(20)]
        result = screen_rows(rows, rows, min_n=100, threshold_margin=0.15, association_margin=0.22)
        self.assertEqual(result["classification"], "UNCERTAIN")
        self.assertEqual(result["threshold_items"], [])

    def test_large_single_item_cutpoint_shift_is_localized(self):
        a = [[0, 0, 0, 0, 0, 0] for _ in range(100)]
        b = [[0, 0, 0, 0, 0, 0] for _ in range(40)] + [[2, 2, 2, 2, 2, 2] for _ in range(60)]
        result = screen_rows(a, b, min_n=100, threshold_margin=0.15, association_margin=0.22)
        self.assertEqual(result["classification"], "THRESHOLD_NONINVARIANCE")
        self.assertEqual(result["threshold_items"], [0, 1, 2, 3, 4, 5])


class FixtureConstructionTests(unittest.TestCase):
    def test_fresh_seed_fixture_family_matches_authored_construction_truth(self):
        root = Path(__file__).resolve().parent
        config = json.loads((root / "config.json").read_text(encoding="utf-8"))
        fixtures = generate(config)
        output = {row["fixture_id"]: row for row in run(fixtures, config)["results"]}
        for fixture_id, expected in config["expected"].items():
            for field in ("classification", "threshold_items", "loading_items"):
                self.assertEqual(output[fixture_id][field], expected[field], f"{fixture_id}:{field}")


if __name__ == "__main__":
    unittest.main()
