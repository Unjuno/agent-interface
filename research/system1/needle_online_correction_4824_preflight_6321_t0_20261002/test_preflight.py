import unittest

import audit_data
import make_data


class LabelPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = make_data.build()

    def test_all_role_labels_match_declared_functions(self):
        self.assertEqual(audit_data.inspect(self.data), [])

    def test_seed_and_split_row_counts(self):
        self.assertEqual(len(self.data["seeds"]), 3)
        self.assertTrue(all(sum(len(rows) for rows in s["splits"].values()) == 328 for s in self.data["seeds"]))

    def test_a_target_is_constant_even_when_feature_zero_is_one(self):
        for s in self.data["seeds"]:
            for split in ("a_support", "a_heldout"):
                self.assertTrue(all(r["label"] == 0 for r in s["splits"][split]))

    def test_b_target_tracks_only_feature_zero(self):
        for s in self.data["seeds"]:
            for split in ("b_arrival", "b_heldout"):
                self.assertTrue(all(r["label"] == r["features"][0] for r in s["splits"][split]))

    def test_support_arrival_and_heldout_feature_vectors_are_disjoint_within_role(self):
        for s in self.data["seeds"]:
            for role, pairs in (("A", (("a_support", "a_heldout"),)),
                                ("B", (("b_arrival", "b_heldout"),))):
                for left, right in pairs:
                    a = {tuple(r["features"]) for r in s["splits"][left]}
                    b = {tuple(r["features"]) for r in s["splits"][right]}
                    self.assertFalse(a & b, (role, left, right))

    def test_seven_frozen_corruptions_are_rejected(self):
        cases = audit_data.mutations(self.data)
        self.assertEqual(len(cases), 7)
        self.assertTrue(all(c["rejected"] for c in cases))


if __name__ == "__main__":
    unittest.main(verbosity=2)
