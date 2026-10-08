import copy
import unittest

from auditor import audit
from candidate import summarize


def records():
    fixture = {
        "offers": [
            {"offer_id": "a1", "pair_id": "p1", "case_id": "benefit", "arm": "A",
             "challenge_id": "cue1", "source_generation": 7, "offered_ns": 0, "deadline_ns": 10},
            {"offer_id": "b1", "pair_id": "p1", "case_id": "benefit", "arm": "B",
             "challenge_id": "cue1", "source_generation": 7, "offered_ns": 0, "deadline_ns": 10},
        ],
        "expected_cases": {"benefit": "OBSERVED_ALL_OFFER_B_ADVANTAGE"},
    }
    events = [
        {"offer_id": "a1", "pair_id": "p1", "arm": "A", "observed_generation": 7,
         "useful_effect": False, "effect_status": "VERIFIED", "adapted": False,
         "response_ns": 4, "occupancy_status": "VERIFIED", "release_status": "VERIFIED_EMPTY",
         "safety_violation": False, "action_attempted": True},
        {"offer_id": "b1", "pair_id": "p1", "arm": "B", "observed_generation": 7,
         "useful_effect": True, "effect_status": "VERIFIED", "adapted": True,
         "response_ns": 4, "occupancy_status": "VERIFIED", "release_status": "VERIFIED_EMPTY",
         "safety_violation": False, "action_attempted": True},
    ]
    return fixture, events


class IndependentAuditTests(unittest.TestCase):
    def test_reconstructs_complete_all_offer_pair(self):
        fixture, events = records()
        report = summarize(fixture["offers"], events)

        result = audit(fixture, events, report)

        self.assertIn("status", result)
        self.assertEqual(result["status"], "PASS_AUDIT")
        self.assertEqual(result["offer_count"], 2)
        self.assertEqual(result["case_statuses"], {"benefit": "OBSERVED_ALL_OFFER_B_ADVANTAGE"})

    def test_detects_hidden_external_offer(self):
        fixture, events = records()
        report = summarize(fixture["offers"], events)
        mutated = copy.deepcopy(events)
        mutated.pop()

        result = audit(fixture, mutated, report)

        self.assertIn("findings", result)
        self.assertIn("EVENT_CARDINALITY_MISMATCH", result["findings"])

    def test_detects_observation_from_wrong_source_generation(self):
        fixture, events = records()
        report = summarize(fixture["offers"], events)
        mutated = copy.deepcopy(events)
        mutated[1]["observed_generation"] = 8

        result = audit(fixture, mutated, report)

        self.assertIn("findings", result)
        self.assertIn("SOURCE_GENERATION_MISMATCH", result["findings"])

    def test_detects_release_or_effect_receipt_mutation(self):
        fixture, events = records()
        report = summarize(fixture["offers"], events)
        mutated = copy.deepcopy(events)
        mutated[1]["release_status"] = "UNKNOWN"

        result = audit(fixture, mutated, report)

        self.assertIn("findings", result)
        self.assertIn("RELEASE_OR_EFFECT_MISMATCH", result["findings"])


if __name__ == "__main__":
    unittest.main()
