import json
from pathlib import Path
import tempfile
import unittest

from independent_progress_clock_v1 import (
    EVENT_SCHEMA,
    ProgressClock,
    ProgressSample,
    append_jsonl,
    summarize_events,
)


def sample(ns, kills=0, deaths=0, finished=False, dead=False, exit_=False):
    return ProgressSample(ns, kills, deaths, finished, dead, exit_)


class ProgressClockTests(unittest.TestCase):
    def test_first_sample_is_baseline(self):
        clock = ProgressClock()
        self.assertEqual(clock.ingest(sample(100, kills=3)), [])
        self.assertEqual(clock.last_sample.kill_count, 3)

    def test_kill_increase_is_positive_useful(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = clock.ingest(sample(200, kills=1))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "KILL_COUNT_INCREASE")
        self.assertEqual(events[0]["polarity"], "positive")
        self.assertIs(events[0]["useful"], True)
        self.assertIs(events[0]["controller_visible"], False)

    def test_map_exit_is_positive_useful(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = clock.ingest(sample(250, finished=True, exit_=True))
        self.assertEqual([row["kind"] for row in events], ["MAP_EXIT"])
        self.assertTrue(events[0]["useful"])

    def test_death_is_negative_not_useful(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = clock.ingest(sample(200, deaths=1, dead=True))
        self.assertEqual(
            [row["kind"] for row in events],
            ["DEATH_COUNT_INCREASE", "PLAYER_DEAD"],
        )
        self.assertTrue(all(row["polarity"] == "negative" for row in events))
        self.assertTrue(all(row["useful"] is False for row in events))

    def test_nonexit_terminal_is_negative(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = clock.ingest(sample(200, finished=True))
        self.assertEqual(events[0]["kind"], "EPISODE_FINISHED_NO_EXIT")
        self.assertFalse(events[0]["useful"])

    def test_exact_duplicate_same_time_is_idempotent(self):
        clock = ProgressClock()
        first = sample(100, kills=1)
        self.assertEqual(clock.ingest(first), [])
        self.assertEqual(clock.ingest(first), [])

    def test_same_time_mutation_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        with self.assertRaisesRegex(ValueError, "without a later"):
            clock.ingest(sample(100, kills=1))

    def test_timestamp_regression_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        with self.assertRaisesRegex(ValueError, "timestamp regression"):
            clock.ingest(sample(99))

    def test_counter_regression_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(100, kills=2, deaths=1))
        with self.assertRaisesRegex(ValueError, "kill_count regression"):
            clock.ingest(sample(200, kills=1, deaths=1))
        clock = ProgressClock()
        clock.ingest(sample(100, kills=2, deaths=1))
        with self.assertRaisesRegex(ValueError, "death_count regression"):
            clock.ingest(sample(200, kills=2, deaths=0))

    def test_map_exit_state_validation(self):
        with self.assertRaisesRegex(ValueError, "map_exit requires"):
            sample(100, exit_=True).validate()
        with self.assertRaisesRegex(ValueError, "map_exit requires"):
            sample(100, finished=True, dead=True, exit_=True).validate()

    def test_finished_or_exit_regression_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(100, finished=True, exit_=True))
        with self.assertRaisesRegex(ValueError, "episode_finished regression"):
            clock.ingest(sample(200))

    def test_summary_first_useful(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = []
        events += clock.ingest(sample(150, deaths=1, dead=True))
        events += clock.ingest(sample(200, kills=1, deaths=1, dead=False))
        result = summarize_events(events)
        self.assertEqual(result["positive_useful_events"], 1)
        self.assertEqual(result["negative_events"], 2)
        self.assertEqual(result["first_useful_ns"], 200)

    def test_append_jsonl_is_scorer_file_only(self):
        clock = ProgressClock()
        clock.ingest(sample(100))
        events = clock.ingest(sample(200, kills=1))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scorer-events.jsonl"
            self.assertEqual(append_jsonl(path, events), 1)
            row = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["schema"], EVENT_SCHEMA)
            self.assertIs(row["controller_visible"], False)

    def test_health_ammo_and_pixels_are_not_contract_fields(self):
        fields = set(ProgressSample.__dataclass_fields__)
        self.assertTrue({"sample_ns", "kill_count", "death_count", "episode_finished", "player_dead", "map_exit"} <= fields)
        self.assertTrue({"health", "ammo", "pixels_changed", "frame_hash"}.isdisjoint(fields))


if __name__ == "__main__":
    unittest.main()
