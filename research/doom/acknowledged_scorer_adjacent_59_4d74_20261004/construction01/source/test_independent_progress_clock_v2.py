import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "clock_v2", HERE / "independent_progress_clock_v2.py"
)
clock_v2 = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = clock_v2
spec.loader.exec_module(clock_v2)

ProgressClock = clock_v2.ProgressClock
ProgressSample = clock_v2.ProgressSample


def sample(
    ns,
    kills=0,
    deaths=0,
    finished=False,
    dead=False,
    exit=False,
):
    return ProgressSample(
        sample_ns=ns,
        kill_count=kills,
        death_count=deaths,
        episode_finished=finished,
        player_dead=dead,
        map_exit=exit,
    )


class Tests(unittest.TestCase):
    def test_first_sample_is_baseline(self):
        clock = ProgressClock()
        self.assertEqual(clock.ingest(sample(10)), [])
        self.assertFalse(clock.terminal)

    def test_kill_increase_is_positive_useful(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        rows = clock.ingest(sample(20, kills=1))
        self.assertEqual([row["kind"] for row in rows], ["KILL_COUNT_INCREASE"])
        self.assertTrue(rows[0]["useful"])
        self.assertFalse(rows[0]["controller_visible"])

    def test_map_exit_is_positive_terminal_event(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        rows = clock.ingest(sample(20, finished=True, exit=True))
        self.assertEqual([row["kind"] for row in rows], ["MAP_EXIT"])
        self.assertTrue(clock.terminal)

    def test_nonexit_terminal_is_negative(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        rows = clock.ingest(sample(20, finished=True))
        self.assertEqual([row["kind"] for row in rows], ["EPISODE_FINISHED_NO_EXIT"])
        self.assertEqual(rows[0]["polarity"], "negative")

    def test_later_identical_terminal_state_is_noop_and_advances_clock(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        terminal = sample(20, kills=2, deaths=1, finished=True, dead=True)
        clock.ingest(terminal)
        self.assertEqual(
            clock.ingest(sample(30, kills=2, deaths=1, finished=True, dead=True)),
            [],
        )
        self.assertEqual(clock.last_sample.sample_ns, 30)

    def test_terminal_nonexit_cannot_later_become_map_exit(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        clock.ingest(sample(20, finished=True))
        with self.assertRaisesRegex(ValueError, "new scorer epoch"):
            clock.ingest(sample(30, finished=True, exit=True))

    def test_terminal_cannot_later_increase_kill_count(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        clock.ingest(sample(20, kills=1, finished=True))
        with self.assertRaisesRegex(ValueError, "new scorer epoch"):
            clock.ingest(sample(30, kills=2, finished=True))

    def test_terminal_cannot_later_increase_death_count(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        clock.ingest(sample(20, deaths=1, finished=True, dead=True))
        with self.assertRaisesRegex(ValueError, "new scorer epoch"):
            clock.ingest(sample(30, deaths=2, finished=True, dead=True))

    def test_terminal_player_state_cannot_mutate(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        clock.ingest(sample(20, finished=True))
        with self.assertRaisesRegex(ValueError, "new scorer epoch"):
            clock.ingest(sample(30, finished=True, dead=True))

    def test_same_timestamp_exact_duplicate_is_idempotent(self):
        clock = ProgressClock()
        row = sample(10)
        clock.ingest(row)
        self.assertEqual(clock.ingest(row), [])

    def test_same_timestamp_mutation_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        with self.assertRaisesRegex(ValueError, "later scorer timestamp"):
            clock.ingest(sample(10, kills=1))

    def test_timestamp_regression_fails_closed(self):
        clock = ProgressClock()
        clock.ingest(sample(20))
        with self.assertRaisesRegex(ValueError, "timestamp regression"):
            clock.ingest(sample(19))

    def test_counter_regression_before_terminal_requires_new_epoch(self):
        clock = ProgressClock()
        clock.ingest(sample(10, kills=2, deaths=1))
        with self.assertRaisesRegex(ValueError, "kill_count regression"):
            clock.ingest(sample(20, kills=1, deaths=1))

    def test_invalid_exit_state_is_rejected(self):
        clock = ProgressClock()
        with self.assertRaisesRegex(ValueError, "map_exit requires"):
            clock.ingest(sample(10, finished=False, exit=True))

    def test_append_jsonl_enforces_scorer_only_schema(self):
        clock = ProgressClock()
        clock.ingest(sample(10))
        rows = clock.ingest(sample(20, kills=1))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scorer.jsonl"
            self.assertEqual(clock_v2.append_jsonl(path, rows), 1)
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema"], clock_v2.EVENT_SCHEMA)
            self.assertFalse(written["controller_visible"])
            bad = dict(rows[0])
            bad["controller_visible"] = True
            with self.assertRaisesRegex(ValueError, "controller-invisible"):
                clock_v2.append_jsonl(path, [bad])


if __name__ == "__main__":
    unittest.main()
