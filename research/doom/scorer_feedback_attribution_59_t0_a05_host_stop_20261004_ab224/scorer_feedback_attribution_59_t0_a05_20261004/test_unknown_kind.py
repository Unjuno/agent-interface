"""T0 A05 probe: unknown kind must not be promoted to a useful envelope."""
import unittest

from scorer_feedback_attribution_v4 import attribute_positive_events


class UnknownKindTests(unittest.TestCase):
    def setUp(self):
        self.samples = [
            {"schema": "independent-progress-sample-v2", "sample_ns": 100},
            {"schema": "independent-progress-sample-v2", "sample_ns": 200},
        ]
        self.event = {
            "schema": "independent-progress-event-v2",
            "event_sequence": 1,
            "observed_ns": 200,
            "kind": "BANANA_UNREGISTERED",
            "polarity": "positive",
            "useful": True,
            "controller_visible": False,
        }
        self.interval = {
            "intent_token": "intent-a",
            "key": "ATTACK",
            "admitted_ns": 90,
            "release_sync_ns": 210,
            "release_verified": True,
        }

    def test_unknown_positive_kind_is_not_promoted(self):
        with self.assertRaisesRegex(ValueError, "unsupported positive useful scorer event kind"):
            attribute_positive_events(self.samples, [self.event], [self.interval])

    def test_known_positive_kinds_keep_possible_only_semantics(self):
        for known in ("KILL_COUNT_INCREASE", "MAP_EXIT"):
            with self.subTest(kind=known):
                event = dict(self.event, kind=known)
                rows = attribute_positive_events(self.samples, [event], [self.interval])
                self.assertEqual(rows[0]["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
                self.assertIsNone(rows[0]["intent_token"])


if __name__ == "__main__":
    unittest.main()
