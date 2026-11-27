"""Pre-freeze sanity checks for the fixed synthetic design and matcher."""

import unittest
import copy

from candidate import evaluate
from audit import independent_predictions
from make_design import build_design


class FrozenDesignConstructionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = build_design()
        cls.by_family = {}
        for row in cls.design["cases"]:
            cls.by_family.setdefault(row["family"], row)

    def test_fixed_split_sizes_and_unique_case_ids(self):
        rows = self.design["cases"]
        self.assertEqual(len(rows), 860)
        self.assertEqual(len({row["case_id"] for row in rows}), 860)
        self.assertEqual(sum(row["split"] == "heldout_positive" for row in rows), 300)
        self.assertEqual(sum(row["split"] == "heldout_negative" for row in rows), 500)

    def test_matcher_output_does_not_depend_on_ground_truth_oracle(self):
        row = self.by_family["sibling_reorder"]
        altered = copy.deepcopy(row)
        altered["oracle"]["target_current_id"] = "withheld-and-changed"
        self.assertEqual(evaluate(row), evaluate(altered))

    def test_independent_reconstruction_agrees_on_each_case_family(self):
        for family, row in self.by_family.items():
            self.assertEqual(evaluate(row)["predictions"], independent_predictions(row), family)

    def test_relational_soft_match_recovers_reordered_target_and_abstains_on_low_margin(self):
        row = self.by_family["sibling_reorder"]
        predicted = evaluate(row)["predictions"]
        self.assertEqual(predicted["RELATIONAL"], row["oracle"]["target_current_id"])
        self.assertIsNone(predicted["ID_PATH"])
        self.assertIsNone(predicted["ROLE_LABEL"])
        # Extra same-label controls and the wrapper fixture do not meet the
        # frozen concentration certificate; abstention is the expected result.
        for family in ("insert_duplicate_save", "transparent_wrapper"):
            self.assertIsNone(evaluate(self.by_family[family])["predictions"]["RELATIONAL"], family)

    def test_relational_soft_match_abstains_on_ambiguous_or_changed_controls(self):
        for family in ("automorphism", "removed_target", "semantic_role_change"):
            self.assertIsNone(evaluate(self.by_family[family])["predictions"]["RELATIONAL"], family)


if __name__ == "__main__":
    unittest.main()
