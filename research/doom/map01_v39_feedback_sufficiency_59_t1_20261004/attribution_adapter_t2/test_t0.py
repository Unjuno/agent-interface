"""Construction tests for independent scorer-to-actuation time attribution."""
from __future__ import annotations

import unittest

try:
    from scorer_feedback_attribution_v1 import attribute_positive_events
except ImportError:
    attribute_positive_events = None


def samples(times):
    return [{"schema": "independent-progress-sample-v2", "sample_ns": time_ns} for time_ns in times]


def event(time_ns, kind="KILL_COUNT_INCREASE"):
    return {
        "schema": "independent-progress-event-v2",
        "event_sequence": 1,
        "observed_ns": time_ns,
        "kind": kind,
        "polarity": "positive",
        "useful": True,
        "controller_visible": False,
    }


def interval(token, key, start, end, verified=True):
    return {
        "intent_token": token,
        "key": key,
        "admitted_ns": start,
        "release_sync_ns": end,
        "release_verified": verified,
    }


class AttributionTests(unittest.TestCase):
    def require_implementation(self):
        self.assertIsNotNone(
            attribute_positive_events,
            "scorer_feedback_attribution_v1 must implement the tested contract",
        )

    def test_unique_intent_must_cover_entire_scorer_detection_interval(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]), [event(200)], [interval("intent-a", "ATTACK", 90, 210)]
        )
        self.assertEqual(rows[0]["status"], "TEMPORALLY_UNIQUE")
        self.assertEqual(rows[0]["intent_token"], "intent-a")
        self.assertEqual(rows[0]["detection_interval_ns"], [100, 200])
        self.assertEqual(rows[0]["causal_attribution"], "NOT_ESTABLISHED")

    def test_partial_overlap_is_unresolved(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]), [event(200)], [interval("intent-a", "ATTACK", 150, 250)]
        )
        self.assertEqual(rows[0]["status"], "UNRESOLVED")

    def test_two_intents_intersecting_detection_interval_are_ambiguous(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]),
            [event(200)],
            [interval("intent-a", "ATTACK", 90, 180), interval("intent-b", "FORWARD", 170, 210)],
        )
        self.assertEqual(rows[0]["status"], "AMBIGUOUS")
        self.assertIsNone(rows[0]["intent_token"])

    def test_same_intent_key_intervals_may_jointly_cover_without_a_gap(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]),
            [event(200)],
            [interval("intent-a", "ATTACK", 90, 150), interval("intent-a", "FORWARD", 150, 210)],
        )
        self.assertEqual(rows[0]["status"], "TEMPORALLY_UNIQUE")

    def test_unverified_release_cannot_establish_unique_coverage(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]), [event(200)], [interval("intent-a", "ATTACK", 90, 210, False)]
        )
        self.assertEqual(rows[0]["status"], "UNRESOLVED")

    def test_unverified_older_release_remains_possible_overlap(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]),
            [event(200)],
            [
                interval("intent-a", "ATTACK", 90, 210),
                interval("intent-b", "FORWARD", 50, 80, False),
            ],
        )
        self.assertEqual(rows[0]["status"], "AMBIGUOUS")

    def test_same_intent_key_intervals_with_gap_are_unresolved(self):
        self.require_implementation()
        rows = attribute_positive_events(
            samples([100, 200]),
            [event(200)],
            [interval("intent-a", "ATTACK", 90, 140), interval("intent-a", "FORWARD", 150, 210)],
        )
        self.assertEqual(rows[0]["status"], "UNRESOLVED")

    def test_duplicate_per_key_interval_is_rejected(self):
        self.require_implementation()
        row = interval("intent-a", "ATTACK", 90, 210)
        with self.assertRaisesRegex(ValueError, "duplicate per-key"):
            attribute_positive_events(samples([100, 200]), [event(200)], [row, dict(row)])

    def test_rejects_event_not_bound_to_scorer_sample(self):
        self.require_implementation()
        with self.assertRaisesRegex(ValueError, "event sample"):
            attribute_positive_events(samples([100, 200]), [event(201)], [interval("a", "ATTACK", 90, 210)])


if __name__ == "__main__":
    unittest.main()
