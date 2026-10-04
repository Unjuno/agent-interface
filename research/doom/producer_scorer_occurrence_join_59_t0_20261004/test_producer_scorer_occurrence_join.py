from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dependencies"))
sys.path.insert(0, str(ROOT))

from acknowledged_scorer_v1 import AcknowledgedSampler
from independent_progress_clock_v2 import ProgressClock, ProgressSample
from occurrence_attribution import normalize_releases
from producer_scorer_occurrence_join import attribute_acknowledged_events


class FakeGame:
    def __init__(self) -> None:
        self.tic = 10
        self.finished = False

    def is_episode_finished(self) -> bool:
        return self.finished

    def get_episode_time(self) -> int:
        return self.tic

    def advance_action(self, count: int, render: bool) -> None:
        assert count == 1
        assert render is True
        self.tic += 1


def source_records(run_id: str = "run-A") -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    clock_values = iter([90, 110, 120, 190, 210, 220])
    emitted: list[dict] = []
    kills = 0

    def sample(game, variables, timeout_seconds, **kwargs):
        nonlocal kills
        kills += 1
        return ProgressSample(next(clock_values), kills - 1, 0, False, False, False)

    sampler = AcknowledgedSampler(sample, run_id, emitted.append,
                                  clock_ns=lambda: next(clock_values))
    game = FakeGame()
    samples = [sampler(game, {}, 1).as_dict(), sampler(game, {}, 1).as_dict()]
    scorer = ProgressClock()
    events = scorer.ingest(ProgressSample(**{k: v for k, v in samples[0].items()
                                              if k != "schema" and k != "producer"}))
    events += scorer.ingest(ProgressSample(**{k: v for k, v in samples[1].items()
                                               if k != "schema" and k != "producer"}))
    admission = {
        "event": "input_admission", "id": "program-1", "step": 0,
        "key": "W", "keycode": 38, "input_occurrence_id": "owner-a:1",
        "owner_id": "owner-a", "intent_token": "intent-a",
        "admitted_ns": 120, "input_ack_ns": 125, "run_id": run_id,
    }
    release = {
        "event": "input_release_transition", "id": "program-1", "step": 0,
        "run_id": run_id,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "keycode": 38,
            "input_occurrence_id": "owner-a:1", "owner_id": "owner-a",
            "intent_token": "intent-a", "owner_keyrelease_started_ns": 250,
            "owner_sync_returned_ns": 260, "server_sync_completed": True,
            "cancel_requested_after_sync": False,
        },
    }
    binding = {"program_id": "program-1", "step": 0,
               "semantic_action_sha256": "a" * 64, "run_id": run_id}
    return samples, events, [admission], [release], [binding], emitted


class ProducerScorerOccurrenceJoinTests(unittest.TestCase):
    def test_acknowledged_event_joins_to_unique_key_occurrence_with_provenance(self):
        samples, events, admissions, raw_releases, bindings, emitted = source_records()
        results = attribute_acknowledged_events(
            samples, events, admissions, raw_releases, bindings)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "unique_temporal_occurrence")
        self.assertEqual(results[0]["input_occurrence_id"], "owner-a:1")
        self.assertEqual(results[0]["producer_run_id"], "run-A")
        self.assertEqual(results[0]["producer_sample_sequence"], 2)
        self.assertEqual(results[0]["producer_update_sequence"], 2)
        self.assertFalse(results[0]["causation_claimed"])
        self.assertEqual([row["sample"] for row in emitted], samples)

    def test_cross_run_interval_is_rejected_instead_of_joined_by_clock_overlap(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        raw_releases[0]["run_id"] = "run-B"
        with self.assertRaisesRegex(ValueError, "run_id mismatch"):
            attribute_acknowledged_events(
                samples, events, admissions, raw_releases, bindings)

    def test_missing_owner_run_binding_fails_closed(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        del admissions[0]["run_id"]
        with self.assertRaisesRegex(ValueError, "run_id"):
            attribute_acknowledged_events(
                samples, events, admissions, raw_releases, bindings)

    def test_event_must_link_to_one_producer_sample_at_its_observation_clock(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        events[0]["observed_ns"] += 1
        with self.assertRaisesRegex(ValueError, "exactly one acknowledged sample"):
            attribute_acknowledged_events(
                samples, events, admissions, raw_releases, bindings)

    def test_release_sync_bracket_stays_unresolved_after_source_join(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        raw_releases[0]["owner_thread_keyup_receipt"]["owner_keyrelease_started_ns"] = 215
        raw_releases[0]["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = 225
        results = attribute_acknowledged_events(
            samples, events, admissions, raw_releases, bindings)
        self.assertEqual(results[0]["status"], "unresolved_release_boundary")
        self.assertEqual(results[0]["producer_update_sequence"], 2)

    def test_cancellation_release_interval_keeps_occurrence_through_join(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        raw_releases[0] = {
            "event": "input_released", "id": "program-1", "run_id": "run-A",
            "owner_release": {
                "event": "owner_release", "verified": True,
                "key_release_intervals_ns": [{
                    "keycode": 38, "input_occurrence_id": "owner-a:1",
                    "owner_id": "owner-a", "intent_token": "intent-a",
                    "interval_ns": [250, 260],
                }],
            },
        }
        results = attribute_acknowledged_events(
            samples, events, admissions, raw_releases, bindings)
        self.assertEqual(results[0]["status"], "unique_temporal_occurrence")
        self.assertEqual(results[0]["input_occurrence_id"], "owner-a:1")

    def test_duplicate_producer_sample_sequence_is_rejected(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        samples[1]["producer"]["sample_sequence"] = 1
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            attribute_acknowledged_events(
                samples, events, admissions, raw_releases, bindings)

    def test_missing_producer_provenance_is_rejected(self):
        samples, events, admissions, raw_releases, bindings, _emitted = source_records()
        del samples[0]["producer"]
        with self.assertRaisesRegex(ValueError, "lacks acknowledged producer provenance"):
            attribute_acknowledged_events(
                samples, events, admissions, raw_releases, bindings)

    def test_terminal_repeat_keeps_same_state_and_original_update_identity(self):
        samples, _events, _admissions, _raw_releases, _bindings, _emitted = source_records()
        samples[0]["episode_finished"] = True
        repeat = dict(samples[0])
        repeat["sample_ns"] = 130
        repeat["producer"] = dict(samples[0]["producer"],
                                  sample_sequence=2,
                                  observation_status="TERMINAL_REPEAT_NO_UPDATE")
        results = attribute_acknowledged_events(
            [samples[0], repeat], [], [], [], [])
        self.assertEqual(results, [])

    def test_terminal_repeat_cannot_change_progress_state(self):
        samples, _events, _admissions, _raw_releases, _bindings, _emitted = source_records()
        samples[0]["episode_finished"] = True
        repeat = dict(samples[0], sample_ns=130, kill_count=1)
        repeat["producer"] = dict(samples[0]["producer"],
                                  sample_sequence=2,
                                  observation_status="TERMINAL_REPEAT_NO_UPDATE")
        with self.assertRaisesRegex(ValueError, "terminal scorer state"):
            attribute_acknowledged_events([samples[0], repeat], [], [], [], [])


if __name__ == "__main__":
    unittest.main()
