"""Behavioral tests for the finite Issue #5265 state-machine probe."""
import copy
import unittest

from experiment import execute_proposals


def proposal(proposal_id, producer, **overrides):
    row = {
        "proposal_id": proposal_id,
        "producer_id": producer,
        "intent_revision": "intent-7",
        "state_generation": 12,
        "target_id": "button-save",
        "target_incarnation": "window-3/widget-8",
        "operation": "CLICK",
        "effect_class": "SAVE_DOCUMENT",
        "effect_opportunity": "dirty-revision-19",
        "expected_postcondition": "saved-revision-19",
        "parameters": {"button": 1},
        "deadline_ms": 1000,
        "now_ms": 100,
        "already_satisfied": False,
    }
    row.update(overrides)
    return row


class EffectCoalescingTests(unittest.TestCase):
    def test_equivalent_cross_producer_proposals_create_one_effect(self):
        proposals = [proposal("p-a", "consumer-a"), proposal("p-b", "consumer-b")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 1)
        self.assertEqual(observed["decisions"], ["EXECUTE", "COALESCED"])

    def test_same_coordinates_with_new_target_incarnation_do_not_coalesce(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", target_incarnation="window-4/widget-8")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 2)

    def test_new_intent_revision_does_not_coalesce(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", intent_revision="intent-8")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 2)

    def test_verified_state_generation_change_preserves_legitimate_repeat(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", state_generation=13,
                              effect_opportunity="dirty-revision-20",
                              expected_postcondition="saved-revision-20")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 2)
        self.assertEqual(observed["decisions"], ["EXECUTE", "EXECUTE"])

    def test_late_proposal_after_effect_satisfied_is_no_action(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", already_satisfied=True)]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 1)
        self.assertEqual(observed["decisions"], ["EXECUTE", "NO_ACTION"])

    def test_same_producer_retry_is_delegated_to_existing_idempotency_contract(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-retry", "consumer-a", retry_of="p-a")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["decisions"], ["EXECUTE", "DEFER_TO_ISSUE_24"])
        self.assertEqual(observed["effects"], 1)

    def test_changed_effect_parameters_remain_distinct(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", parameters={"button": 2})]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 2)

    def test_unknown_target_incarnation_yields_without_guessing(self):
        proposals = [proposal("p-a", "consumer-a", target_incarnation=None),
                     proposal("p-b", "consumer-b", target_incarnation=None)]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 0)
        self.assertEqual(observed["decisions"], ["YIELD", "YIELD"])

    def test_expired_proposal_yields_without_effect(self):
        proposals = [proposal("p-a", "consumer-a", now_ms=1000)]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 0)
        self.assertEqual(observed["decisions"], ["YIELD_EXPIRED"])

    def test_coalescing_never_creates_or_extends_authority(self):
        proposals = [proposal("p-a", "consumer-a"), proposal("p-b", "consumer-b")]
        snapshot = copy.deepcopy(proposals)
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(proposals, snapshot)
        self.assertNotIn("authority", observed)
        self.assertNotIn("permit", observed)

    def test_coalesced_group_retains_both_proposal_and_producer_identities(self):
        proposals = [proposal("p-a", "consumer-a"), proposal("p-b", "consumer-b")]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["coalesced_groups"], [{
            "members": [{"proposal_id": "p-a", "producer_id": "consumer-a"},
                        {"proposal_id": "p-b", "producer_id": "consumer-b"}],
            "deadline_ms": 1000,
        }])

    def test_different_deadlines_do_not_share_a_coalescing_group(self):
        proposals = [proposal("p-a", "consumer-a"),
                     proposal("p-b", "consumer-b", deadline_ms=2000)]
        observed = execute_proposals(proposals, "SEMANTIC_EFFECT_COALESCING")
        self.assertEqual(observed["effects"], 2)
        self.assertEqual(len(observed["coalesced_groups"]), 2)

    def test_no_coalescing_control_executes_both_equivalent_proposals(self):
        proposals = [proposal("p-a", "consumer-a"), proposal("p-b", "consumer-b")]
        observed = execute_proposals(proposals, "NO_CROSS_PRODUCER_COALESCING")
        self.assertEqual(observed["effects"], 2)
        self.assertEqual(observed["decisions"], ["EXECUTE", "EXECUTE"])


if __name__ == "__main__":
    unittest.main()
