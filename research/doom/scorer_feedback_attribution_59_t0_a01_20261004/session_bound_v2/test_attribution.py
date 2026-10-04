"""Regression tests for cross-session temporal-attribution refusal."""
from __future__ import annotations

import unittest

try:
    from attribution_v2 import attribute_positive_events
except ImportError:
    attribute_positive_events = None

try:
    from scorer_feedback_attribution_v1 import attribute_positive_events as attribute_v1
except ImportError:
    attribute_v1 = None


def sample(time_ns, session_id="run-b"):
    return {
        "schema": "independent-progress-sample-v2",
        "sample_ns": time_ns,
        "session_id": session_id,
    }


def event(time_ns, session_id="run-b"):
    return {
        "schema": "independent-progress-event-v2",
        "event_sequence": 1,
        "observed_ns": time_ns,
        "kind": "KILL_COUNT_INCREASE",
        "polarity": "positive",
        "useful": True,
        "controller_visible": False,
        "session_id": session_id,
    }


def interval(session_id="run-a"):
    return {
        "intent_token": "intent-a",
        "key": "ATTACK",
        "admitted_ns": 90,
        "release_sync_ns": 210,
        "release_verified": True,
        "session_id": session_id,
    }


class SessionBoundAttributionTests(unittest.TestCase):
    def require_implementation(self):
        self.assertIsNotNone(
            attribute_positive_events,
            "session-bound scorer attribution must be implemented",
        )

    def test_equal_numeric_clocks_from_different_sessions_must_not_join(self):
        self.require_implementation()
        with self.assertRaisesRegex(ValueError, "session_id mismatch"):
            attribute_positive_events(
                [sample(100), sample(200)],
                [event(200)],
                [interval("run-a")],
            )

    def test_frozen_v1_control_reproduces_cross_session_false_join(self):
        self.assertIsNotNone(attribute_v1)
        rows = attribute_v1(
            [sample(100), sample(200)],
            [event(200)],
            [interval("run-a")],
        )
        self.assertEqual(rows[0]["status"], "TEMPORALLY_UNIQUE")
        self.assertEqual(rows[0]["intent_token"], "intent-a")

    def test_same_session_preserves_a_fully_bracketed_temporal_association(self):
        self.require_implementation()
        rows = attribute_positive_events(
            [sample(100), sample(200)],
            [event(200)],
            [interval("run-b")],
        )
        self.assertEqual(rows[0]["status"], "TEMPORALLY_UNIQUE")
        self.assertEqual(rows[0]["intent_token"], "intent-a")
        self.assertEqual(rows[0]["causal_attribution"], "NOT_ESTABLISHED")

    def test_missing_session_identity_is_not_silently_accepted(self):
        self.require_implementation()
        cases = [
            ([dict(sample(100), session_id=None), sample(200)], [event(200)], [interval("run-b")]),
            ([sample(100), sample(200)], [dict(event(200), session_id="")], [interval("run-b")]),
            ([sample(100), sample(200)], [event(200)], [dict(interval("run-b"), session_id=None)]),
        ]
        for samples, events, intervals in cases:
            with self.subTest(samples=samples, events=events, intervals=intervals):
                with self.assertRaisesRegex(ValueError, "session_id"):
                    attribute_positive_events(samples, events, intervals)


if __name__ == "__main__":
    unittest.main()
