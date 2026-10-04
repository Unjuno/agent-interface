from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dependencies"))
sys.path.insert(0, str(ROOT))

from acknowledged_scorer_v1 import AcknowledgedSampler
from independent_progress_clock_v2 import ProgressClock, ProgressSample
from producer_scorer_session_envelope_join import attribute_acknowledged_events


class FakeGame:
    def __init__(self) -> None:
        self.tic = 10
        self.finished = False

    def is_episode_finished(self) -> bool:
        return self.finished

    def get_episode_time(self) -> int:
        return self.tic

    def advance_action(self, count: int, render: bool) -> None:
        assert count == 1 and render is True
        self.tic += 1


def source_records(run_id: str = "session-A"):
    clock_values = iter([90, 110, 120, 190, 210, 220])
    emitted = []
    kill_count = 0

    def sample(_game, _variables, _timeout_seconds, **_kwargs):
        nonlocal kill_count
        kill_count += 1
        return ProgressSample(next(clock_values), kill_count - 1, 0,
                              False, False, False)

    sampler = AcknowledgedSampler(sample, run_id, emitted.append,
                                  clock_ns=lambda: next(clock_values))
    game = FakeGame()
    samples = [sampler(game, {}, 1).as_dict(), sampler(game, {}, 1).as_dict()]
    clock = ProgressClock()
    events = []
    for row in samples:
        events.extend(clock.ingest(ProgressSample(**{
            key: value for key, value in row.items()
            if key not in ("schema", "producer")
        })))
    admission = {
        "event": "input_admission", "id": "program-1", "step": 0,
        "key": "W", "keycode": 38, "input_occurrence_id": "owner-a:1",
        "owner_id": "owner-a", "intent_token": "intent-a",
        "admitted_ns": 90, "input_ack_ns": 95, "session_id": run_id,
    }
    release = {
        "event": "input_release_transition", "id": "program-1", "step": 0,
        "session_id": run_id,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "keycode": 38,
            "input_occurrence_id": "owner-a:1", "owner_id": "owner-a",
            "intent_token": "intent-a", "owner_keyrelease_started_ns": 250,
            "owner_sync_returned_ns": 260, "server_sync_completed": True,
            "cancel_requested_after_sync": False,
        },
    }
    binding = {"program_id": "program-1", "step": 0,
               "semantic_action_sha256": "a" * 64, "session_id": run_id}
    return samples, events, [admission], [release], [binding], emitted


class SessionEnvelopeJoinTests(unittest.TestCase):
    def test_event_links_to_acknowledged_sample_and_possible_occurrence_envelope(self):
        samples, events, admissions, releases, bindings, updates = source_records()
        results = attribute_acknowledged_events(
            samples, events, admissions, releases, bindings)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertEqual(results[0]["possible_occurrence_ids"], ["owner-a:1"])
        self.assertEqual(results[0]["session_id"], "session-A")
        self.assertEqual(results[0]["producer_run_id"], "session-A")
        self.assertEqual(results[0]["producer_sample_sequence"], 2)
        self.assertEqual(results[0]["producer_update_sequence"], 2)
        self.assertIsNone(results[0]["intent_token"])
        self.assertEqual(results[0]["causal_attribution"], "NOT_ESTABLISHED")
        self.assertEqual([row["sample"] for row in updates], samples)
        self.assertTrue(all(row["sample"]["producer"]["run_id"] == "session-A"
                            for row in updates))

    def test_cross_session_release_is_rejected_despite_clock_overlap(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        releases[0]["session_id"] = "session-B"
        with self.assertRaisesRegex(ValueError, "session_id mismatch"):
            attribute_acknowledged_events(samples, events, admissions, releases, bindings)

    def test_missing_owner_session_identity_fails_closed(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        del admissions[0]["session_id"]
        with self.assertRaisesRegex(ValueError, "session_id"):
            attribute_acknowledged_events(samples, events, admissions, releases, bindings)

    def test_event_must_link_to_an_exact_acknowledged_sample_clock(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        events[0]["observed_ns"] += 1
        with self.assertRaisesRegex(ValueError, "exactly one acknowledged sample"):
            attribute_acknowledged_events(samples, events, admissions, releases, bindings)

    def test_event_at_release_sync_endpoint_is_unresolved(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        boundary_ns = 260
        samples[1]["sample_ns"] = boundary_ns
        events[0]["observed_ns"] = boundary_ns
        results = attribute_acknowledged_events(
            samples, events, admissions, releases, bindings)
        self.assertEqual(results[0]["status"], "UNRESOLVED")
        self.assertEqual(results[0]["reason"], "endpoint_tie_without_authenticated_order")

    def test_cancellation_release_interval_remains_a_possible_envelope(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        releases[0] = {
            "event": "input_released", "id": "program-1", "session_id": "session-A",
            "owner_release": {
                "event": "owner_release", "verified": True,
                "key_release_intervals_ns": [{
                    "step": 0, "keycode": 38,
                    "input_occurrence_id": "owner-a:1", "owner_id": "owner-a",
                    "intent_token": "intent-a", "interval_ns": [250, 260],
                }],
            },
        }
        results = attribute_acknowledged_events(
            samples, events, admissions, releases, bindings)
        self.assertEqual(results[0]["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertEqual(results[0]["possible_occurrence_ids"], ["owner-a:1"])

    def test_duplicate_producer_sample_sequence_is_rejected(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        samples[1]["producer"]["sample_sequence"] = 1
        with self.assertRaisesRegex(ValueError, "increase by one"):
            attribute_acknowledged_events(samples, events, admissions, releases, bindings)

    def test_missing_producer_provenance_is_rejected(self):
        samples, events, admissions, releases, bindings, _updates = source_records()
        del samples[0]["producer"]
        with self.assertRaisesRegex(ValueError, "producer provenance"):
            attribute_acknowledged_events(samples, events, admissions, releases, bindings)

    def test_terminal_repeat_preserves_ack_identity_and_state(self):
        samples, _events, _admissions, _releases, _bindings, _updates = source_records()
        samples[0]["episode_finished"] = True
        repeat = dict(samples[0], sample_ns=130)
        repeat["producer"] = dict(samples[0]["producer"], sample_sequence=2,
                                  observation_status="TERMINAL_REPEAT_NO_UPDATE")
        self.assertEqual(attribute_acknowledged_events([samples[0], repeat], [], [], [], []), [])

    def test_terminal_repeat_cannot_mutate_progress_state(self):
        samples, _events, _admissions, _releases, _bindings, _updates = source_records()
        samples[0]["episode_finished"] = True
        repeat = dict(samples[0], sample_ns=130, kill_count=1)
        repeat["producer"] = dict(samples[0]["producer"], sample_sequence=2,
                                  observation_status="TERMINAL_REPEAT_NO_UPDATE")
        with self.assertRaisesRegex(ValueError, "terminal scorer state"):
            attribute_acknowledged_events([samples[0], repeat], [], [], [], [])

    def test_external_terminal_update_ack_is_retained_by_current_sampler(self):
        game = FakeGame()
        emitted = []
        sampler = AcknowledgedSampler(
            lambda *_args, **_kwargs: ProgressSample(120, 0, 0, True, False, False),
            "session-A", emitted.append)
        sampler.before_external_update(game)
        before = game.get_episode_time()
        game.advance_action(1, True)
        after = game.get_episode_time()
        sampler.observe_external_update(game, before, after, 90, 110)
        game.finished = True
        sample = sampler(game, {}, 1)
        self.assertEqual(sample.producer["observation_status"], "EXTERNAL_UPDATE_RETURNED")
        self.assertEqual(sample.producer["update_sequence"], 1)
        self.assertEqual(sample.producer["sample_sequence"], 1)
        self.assertEqual(emitted[0]["status"], "EXTERNAL_UPDATE_RETURNED")
        self.assertEqual(emitted[0]["sample"]["producer"], sample.producer)


if __name__ == "__main__":
    unittest.main()
