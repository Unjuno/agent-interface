import copy
import unittest

import auditor
import candidate


class HandoffCardAuditTests(unittest.TestCase):
    def setUp(self):
        self.cards = candidate.build_cards()

    def test_base_cards_and_keys_match_independent_oracle(self):
        self.assertEqual(len(self.cards), 24)
        self.assertEqual(auditor.audit(self.cards), [])

    def test_shared_facts_and_authority_are_invariant_across_option_counts(self):
        by_family = {}
        for card in self.cards:
            by_family.setdefault(card["family_id"], []).append(card)
        for trio in by_family.values():
            invariant = (trio[0]["operation"], trio[0]["target"], trio[0]["operation_status"], trio[0]["evidence_statement"], trio[0]["authority_boundary"])
            self.assertTrue(all((c["operation"], c["target"], c["operation_status"], c["evidence_statement"], c["authority_boundary"]) == invariant for c in trio))
            self.assertEqual([len(c["options"]) for c in trio], [2, 3, 4])

    def test_rejects_target_or_effect_fact_drift(self):
        for field in ("target", "evidence_statement", "operation_status"):
            altered = copy.deepcopy(self.cards)
            altered[0][field] = "changed"
            self.assertIn("card[0]:" + field, auditor.audit(altered))

    def test_rejects_authority_inflation_and_missing_stop(self):
        altered = copy.deepcopy(self.cards)
        altered[0]["authority_boundary"] = "Selection authorizes dispatch."
        self.assertIn("card[0]:authority_boundary", auditor.audit(altered))
        altered = copy.deepcopy(self.cards)
        altered[0]["options"] = altered[0]["options"][1:]
        self.assertIn("card[0]:option_set", auditor.audit(altered))

    def test_rejects_duplicate_or_unexpected_options(self):
        altered = copy.deepcopy(self.cards)
        altered[0]["options"][1]["id"] = "stop"
        self.assertTrue(any(x.startswith("card[0]:option_set") for x in auditor.audit(altered)))

    def test_rejects_incorrect_or_preference_based_comprehension_key(self):
        altered = copy.deepcopy(self.cards)
        altered[0]["comprehension_key"][3]["answer"] = "Yes"
        self.assertIn("card[0]:comprehension_key", auditor.audit(altered))
        altered = copy.deepcopy(self.cards)
        altered[0]["comprehension_key"][0]["kind"] = "preferred_choice"
        errors = auditor.audit(altered)
        self.assertIn("card[0]:preference_or_unknown_key", errors)

    def test_rejects_missing_card_denominator(self):
        self.assertEqual(auditor.audit(self.cards[:-1]), ["card_denominator"])


if __name__ == "__main__":
    unittest.main()
