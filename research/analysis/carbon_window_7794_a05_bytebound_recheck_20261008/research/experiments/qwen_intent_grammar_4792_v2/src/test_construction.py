import unittest

from candidates import NO_ACTION_REASONS, YIELD_REASONS, TokenTrie, candidates_from_state


class CandidateTrieConstructionTests(unittest.TestCase):
    def test_candidates_are_visible_state_derived(self):
        state = {
            "allowed_values": {"timezone": ["UTC", "Asia/Tokyo"]},
            "allowed_effects": ["set_timezone", "save_settings", "toggle_email_reminders"],
            "visible_targets": ["toggle_email_reminders", "hidden_target"],
        }
        values = candidates_from_state(state)
        self.assertEqual(values, sorted(set(values)))
        self.assertIn('{"field":"timezone","op":"set","value":"UTC"}', values)
        self.assertIn('{"op":"save"}', values)
        self.assertIn('{"op":"toggle","target":"toggle_email_reminders"}', values)
        self.assertNotIn('{"op":"toggle","target":"hidden_target"}', values)
        self.assertEqual(sum('"op":"yield"' in value for value in values), len(YIELD_REASONS))
        self.assertEqual(sum('"op":"no_action"' in value for value in values), len(NO_ACTION_REASONS))

    def test_effect_and_visibility_gates(self):
        state = {"allowed_values": {"timezone": ["UTC"]}, "allowed_effects": [],
                 "visible_targets": ["toggle_email_reminders"]}
        values = candidates_from_state(state)
        self.assertFalse(any('"op":"set"' in value or '"op":"save"' in value or '"op":"toggle"' in value for value in values))

    def test_trie_exact_prefix_sets_and_eos(self):
        trie = TokenTrie([[3, 4], [3, 5, 6]], eos_token_id=2)
        self.assertEqual(trie.allowed([]), [3])
        self.assertEqual(trie.allowed([3]), [4, 5])
        self.assertEqual(trie.allowed([3, 4]), [2])
        self.assertEqual(trie.allowed([3, 5]), [6])
        self.assertEqual(trie.allowed([3, 5, 6]), [2])
        self.assertEqual(trie.allowed([9]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
