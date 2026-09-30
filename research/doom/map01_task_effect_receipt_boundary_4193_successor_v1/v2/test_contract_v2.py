import unittest

from contract import classify


def complete(**changes):
    row = {
        "mode": "ATTACK", "session_id": "s1", "plan_id": "p1",
        "actuation_id": "a1", "source_event_id": "e-down-1",
        "event_kind": "TASK_EFFECT", "clock_domain": "mono-s1",
        "down_ns": 100, "terminal_ns": 200,
        "scorer_event_id": "score-1", "scorer_effect_kind": "KILL_COUNT_INCREASE", "scorer_session_id": "s1",
        "scorer_plan_id": "p1", "scorer_actuation_id": "a1",
        "scorer_source_event_id": "e-down-1", "scorer_monotonic_ns": 120,
        "scorer_clock_domain": "mono-s1", "scorer_authority": False,
        "physical_down": True, "physical_up": True, "terminal_neutral": True,
        "duplicate_scorer_events": 0,
    }
    row.update(changes)
    return row


class ContractTests(unittest.TestCase):
    def test_unique_source_bound_positive_is_accepted(self):
        self.assertEqual(classify(complete()), "BOUND_TASK_EFFECT")

    def test_missing_source_identity_holds(self):
        self.assertEqual(classify(complete(source_event_id=None)), "HOLD_SOURCE_IDENTITY_INSUFFICIENT")

    def test_wrong_join_identity_holds(self):
        for field in ("scorer_session_id", "scorer_plan_id", "scorer_actuation_id", "scorer_source_event_id"):
            with self.subTest(field=field):
                self.assertEqual(classify(complete(**{field: "wrong"})), "HOLD_SOURCE_IDENTITY_INSUFFICIENT")

    def test_incomparable_clock_holds(self):
        self.assertEqual(classify(complete(scorer_clock_domain="other")), "HOLD_CLOCK_DOMAIN_UNCOMPARABLE")

    def test_nonmonotonic_or_out_of_interval_scorer_holds(self):
        self.assertEqual(classify(complete(scorer_monotonic_ns=99)), "HOLD_CLOCK_DOMAIN_UNCOMPARABLE")
        self.assertEqual(classify(complete(scorer_monotonic_ns=200)), "HOLD_CLOCK_DOMAIN_UNCOMPARABLE")

    def test_unsupported_event_kind_holds(self):
        self.assertEqual(classify(complete(event_kind="HUD_STATE")), "HOLD_UNSUPPORTED_EVENT_KIND")

    def test_unsupported_scorer_kind_holds(self):
        self.assertEqual(classify(complete(scorer_effect_kind="HUD_CHANGE")), "HOLD_UNSUPPORTED_EFFECT_KIND")

    def test_duplicate_scorer_binding_fails(self):
        self.assertEqual(classify(complete(duplicate_scorer_events=2)), "FAIL_AMBIGUOUS_EVENT_BINDING")

    def test_no_input_cannot_bind_positive_effect(self):
        self.assertEqual(classify(complete(mode="NO_INPUT")), "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING")

    def test_missing_physical_edges_holds(self):
        self.assertEqual(classify(complete(physical_up=False)), "HOLD_PHYSICAL_EDGE_INCOMPLETE")

    def test_missing_neutral_terminal_holds(self):
        self.assertEqual(classify(complete(terminal_neutral=False)), "HOLD_TERMINAL_NOT_NEUTRAL")


if __name__ == "__main__":
    unittest.main()
