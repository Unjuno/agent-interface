import unittest

from candidate import summarize


def event(offer_id, pair_id, arm, success, *, adapted=False, response_ns=5,
          observed_generation=1, occupancy="VERIFIED", release="VERIFIED_EMPTY",
          safety_violation=False, attempted=True):
    return {
        "offer_id": offer_id,
        "pair_id": pair_id,
        "arm": arm,
        "useful_effect": success,
        "effect_status": "VERIFIED",
        "adapted": adapted,
        "response_ns": response_ns,
        "observed_generation": observed_generation,
        "occupancy_status": occupancy,
        "release_status": release,
        "safety_violation": safety_violation,
        "action_attempted": attempted,
    }


def offer(offer_id, pair_id, arm, *, generation=1, deadline_ns=10):
    return {
        "offer_id": offer_id,
        "pair_id": pair_id,
        "arm": arm,
        "challenge_id": "cue-1",
        "source_generation": generation,
        "offered_ns": 0,
        "deadline_ns": deadline_ns,
    }


class CandidateSummaryTests(unittest.TestCase):
    def test_keeps_every_external_offer_in_paired_effect_denominator(self):
        offers = [offer("a1", "p1", "A"), offer("b1", "p1", "B"),
                  offer("a2", "p2", "A"), offer("b2", "p2", "B")]
        events = [event("a1", "p1", "A", True), event("b1", "p1", "B", True, adapted=True),
                  event("a2", "p2", "A", False), event("b2", "p2", "B", False, attempted=False)]

        result = summarize(offers, events)

        self.assertIn("offer_count", result)
        self.assertEqual(result["offer_count"], 4)
        self.assertEqual(result["pair_count"], 2)
        self.assertEqual(result["paired_success_delta"], 0)
        self.assertNotIn("adapted_success_rate", result)

    def test_late_response_cannot_count_as_timely_adaptation(self):
        offers = [offer("a", "p", "A"), offer("b", "p", "B", deadline_ns=10)]
        events = [event("a", "p", "A", False), event("b", "p", "B", True, adapted=True, response_ns=11)]

        result = summarize(offers, events)

        self.assertIn("offers", result)
        self.assertIn("mechanism_attribution_eligible", result)
        row = next(row for row in result["offers"] if row["offer_id"] == "b")
        self.assertFalse(row["timely_adaptation"])
        self.assertEqual(result["paired_success_delta"], 1)
        self.assertFalse(result["mechanism_attribution_eligible"])

    def test_generation_mismatch_and_unknown_occupancy_do_not_qualify_mechanism(self):
        offers = [offer("a", "p", "A"), offer("b", "p", "B")]
        events = [event("a", "p", "A", False), event("b", "p", "B", True, adapted=True,
                                                                 observed_generation=2, occupancy="UNKNOWN")]

        result = summarize(offers, events)

        self.assertIn("mechanism_attribution_eligible", result)
        self.assertFalse(result["mechanism_attribution_eligible"])
        self.assertEqual(result["paired_success_delta"], 1)

    def test_safety_violation_overrides_successful_task_effect(self):
        offers = [offer("a", "p", "A"), offer("b", "p", "B")]
        events = [event("a", "p", "A", False), event("b", "p", "B", True,
                                                            safety_violation=True)]

        result = summarize(offers, events)

        self.assertIn("decision", result)
        self.assertEqual(result["decision"], "FAIL_SAFETY")

    def test_missing_effect_does_not_create_a_complete_case_paired_estimate(self):
        offers = [offer("a1", "p1", "A"), offer("b1", "p1", "B"),
                  offer("a2", "p2", "A"), offer("b2", "p2", "B")]
        events = [event("a1", "p1", "A", False), event("b1", "p1", "B", True),
                  event("a2", "p2", "A", True), event("b2", "p2", "B", None)]
        events[3]["effect_status"] = "UNKNOWN"

        result = summarize(offers, events)

        self.assertEqual(result["offer_count"], 4)
        self.assertEqual(result["pair_count"], 2)
        self.assertIsNone(result["paired_success_delta"])
        self.assertEqual(result["decision"], "HOLD_MISSING_EFFECT")

    def test_wrong_effect_cannot_be_hidden_by_success_label(self):
        offers = [offer("a", "p", "A"), offer("b", "p", "B")]
        events = [event("a", "p", "A", False), event("b", "p", "B", True)]
        events[1]["wrong_effects"] = 1

        result = summarize(offers, events)

        self.assertEqual(result["decision"], "FAIL_SAFETY")


if __name__ == "__main__":
    unittest.main()
