import unittest

import audit
import prepare


class RoleContextContractTests(unittest.TestCase):
    def test_role_targets_and_exact_split_sizes(self):
        deck = prepare.build((71, 73, 79))
        self.assertEqual(deck["schema"], "unjuno.needle.role-context-online.v1")
        for seed in deck["seeds"]:
            splits = seed["splits"]
            self.assertEqual([len(splits[k]) for k in ("a_support", "a_heldout", "b_arrival", "b_heldout")],
                             [64, 128, 8, 128])
            for row in splits["a_support"] + splits["a_heldout"]:
                self.assertEqual(row["label"], 0)
            for row in splits["b_arrival"] + splits["b_heldout"]:
                self.assertEqual(row["label"], row["features"][0])

    def test_same_role_splits_are_disjoint_and_balanced(self):
        deck = prepare.build((83,))
        self.assertEqual(audit.check_dataset(deck, (83,)), [])
        sample = deck["seeds"][0]["splits"]
        for left, right in (("a_support", "a_heldout"), ("b_arrival", "b_heldout")):
            l = {tuple(r["features"]) for r in sample[left]}
            r = {tuple(r["features"]) for r in sample[right]}
            self.assertFalse(l & r)

    def test_cross_role_ambiguity_is_explicit_but_no_cross_role_leakage(self):
        deck = prepare.build(prepare.SEEDS)
        self.assertEqual(audit.check_dataset(deck, prepare.SEEDS), [])
        for seed in deck["seeds"]:
            splits = seed["splits"]
            a_train = {tuple(row["features"]) for row in splits["a_support"]}
            b_train = {tuple(row["features"]) for row in splits["b_arrival"]}
            a_test = {tuple(row["features"]) for row in splits["a_heldout"]}
            b_test = {tuple(row["features"]) for row in splits["b_heldout"]}
            self.assertFalse(a_train & a_test)
            self.assertFalse(b_train & b_test)
            self.assertGreater(seed["cross_role_overlap_count"], 0)
            probe = seed["role_conflict_probe"]
            self.assertEqual(probe["a_label"], 0)
            self.assertEqual(probe["b_label"], probe["features"][0])

    def test_role_gate_disables_adapter_on_a_and_enables_on_b(self):
        self.assertEqual(audit.adapter_gate(0), 0)
        self.assertEqual(audit.adapter_gate(1), 1)
        self.assertEqual(audit.scope_decision("known", True), "PROPOSE")
        self.assertEqual(audit.scope_decision("known", False), "YIELD")
        self.assertEqual(audit.scope_decision("unknown", True), "YIELD")
        self.assertEqual(audit.scope_decision("known", True, intent_match=False), "YIELD")

    def test_unknown_role_rejected(self):
        with self.assertRaises(ValueError):
            prepare.make_rows(89, "C", "test", 1, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
