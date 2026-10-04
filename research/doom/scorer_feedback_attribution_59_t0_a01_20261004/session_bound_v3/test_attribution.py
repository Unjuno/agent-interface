"""Regression tests for session binding over the A03 envelope semantics."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

DOOM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DOOM / "scorer_feedback_attribution_59_t0_a03_20261004"))

try:
    from attribution_v3 import attribute_positive_events
except ImportError:
    attribute_positive_events = None


def sample(time_ns, session_id="run-b"):
    return {
        "schema": "independent-progress-sample-v2",
        "sample_ns": time_ns,
        "session_id": session_id,
    }


def event(time_ns=200, session_id="run-b"):
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


def interval(start=90, end=210, session_id="run-b"):
    return {
        "intent_token": "intent-a",
        "key": "ATTACK",
        "admitted_ns": start,
        "release_sync_ns": end,
        "release_verified": True,
        "session_id": session_id,
    }


class SessionBoundA03Tests(unittest.TestCase):
    def require_implementation(self):
        self.assertIsNotNone(attribute_positive_events, "session-bound A03 wrapper is missing")

    def test_cross_session_envelope_is_rejected(self):
        self.require_implementation()
        with self.assertRaisesRegex(ValueError, "session_id mismatch"):
            attribute_positive_events(
                [sample(100), sample(200)], [event()], [interval(session_id="run-a")]
            )

    def test_same_session_preserves_a03_possible_envelope_not_unique_intent(self):
        self.require_implementation()
        row = attribute_positive_events(
            [sample(100), sample(200)], [event()], [interval()]
        )[0]
        self.assertEqual(row["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertEqual(row["possible_intent_tokens"], ["intent-a"])
        self.assertIsNone(row["intent_token"])
        self.assertEqual(row["causal_attribution"], "NOT_ESTABLISHED")

    def test_same_session_endpoint_tie_remains_unresolved(self):
        self.require_implementation()
        row = attribute_positive_events(
            [sample(100), sample(200)], [event()], [interval(90, 200)]
        )[0]
        self.assertEqual(row["status"], "UNRESOLVED")
        self.assertIsNone(row["intent_token"])

    def test_every_record_kind_requires_session_identity(self):
        self.require_implementation()
        rows = [sample(100), sample(200)]
        no_sample_id = [dict(rows[0], session_id=None), rows[1]]
        no_event_id = [dict(event(), session_id="")]
        no_interval_id = [dict(interval(), session_id=None)]
        cases = [
            (no_sample_id, [event()], [interval()]),
            (rows, no_event_id, [interval()]),
            (rows, [event()], no_interval_id),
        ]
        for samples, events, intervals in cases:
            with self.subTest(samples=samples, events=events, intervals=intervals):
                with self.assertRaisesRegex(ValueError, "session_id"):
                    attribute_positive_events(samples, events, intervals)


if __name__ == "__main__":
    unittest.main()
