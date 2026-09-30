import json
import unittest

from candidates import TokenTrie, candidates_from_state
from protocol import bind_intent, expected_bound, make_rows, simulate_bound


class SyntheticTests(unittest.TestCase):
    def test_deterministic_and_label_blind_candidates(self):
        a = make_rows(4792963, "heldout", 32)
        b = make_rows(4792963, "heldout", 32)
        self.assertEqual(a, b)
        for row in a:
            before = candidates_from_state(row["state"])
            poisoned = dict(row["state"], intent={"op": "save"}, target="poison")
            self.assertEqual(before, candidates_from_state(poisoned))
            self.assertEqual(before, sorted(set(before)))

    def test_trie_and_eos(self):
        trie = TokenTrie([[1, 2], [1, 3]], 9)
        self.assertEqual(trie.allowed([]), [1])
        self.assertEqual(trie.allowed([1]), [2, 3])
        self.assertEqual(trie.allowed([1, 2]), [9])
        self.assertEqual(trie.allowed([8]), [])

    def test_all_gold_bind_and_effect(self):
        rows = make_rows(4792963, "heldout", 32)
        for row in rows:
            candidates = candidates_from_state(row["state"])
            self.assertIn(json.dumps(row["intent"], sort_keys=True, separators=(",", ":")), candidates)
            bound = expected_bound(row)
            self.assertEqual(bound, bind_intent(row["intent"], row["state"], row["requested_generation"]))
            self.assertEqual(simulate_bound(bound, row["state"]), simulate_bound(bound, row["state"]))


if __name__ == "__main__":
    unittest.main()

