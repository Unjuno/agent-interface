import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V16_SOURCE = REPO / "research/doom/acknowledged_scorer_59_4d74_20261004/source"
sys.path.insert(0, str(V16_SOURCE))
sys.path.insert(0, str(ROOT))

from acknowledged_scorer_v1 import AcknowledgedSampler
from independent_progress_clock_v2 import ProgressClock
from map01_scorer_stdio_adapter_v1 import ScorerFileSink
from state_snapshot_sampler import coherent_snapshot_sample


class Variables:
    DEATHCOUNT = "death"
    KILLCOUNT = "kill"
    HEALTH = "health"


class State:
    def __init__(self, tic, values):
        self.tic = tic
        self.game_variables = values


class Game:
    def __init__(self, state_tic=11, after_update=11, values=(0.0, 0.0, 100.0),
                 configured=("death", "kill", "health")):
        self.tic = 1
        self.after_update = after_update
        self.state = State(state_tic, values)
        self.configured = list(configured)
        self.calls = 0

    def get_episode_time(self):
        return self.after_update if self.calls else self.tic

    def advance_action(self, count, update):
        assert count == 1 and update is True
        self.calls += 1

    def get_state(self):
        return self.state

    def get_available_game_variables(self):
        return self.configured

    def is_episode_finished(self):
        return False

    def is_player_dead(self):
        return False

    def get_ticrate(self):
        return 35


class StateSnapshotCompositionTests(unittest.TestCase):
    def make_sampler(self, game, emit=None):
        ticks = iter((100, 101, 102))
        return AcknowledgedSampler(
            coherent_snapshot_sample, "snapshot-run", emit or (lambda row: None),
            clock_ns=lambda: next(ticks))

    def test_retained_runtime_endpoint_composes_with_actual_v16_sampler_and_sink(self):
        raw_path = (REPO / "research/doom/scorer_async_spectator_59_t0_a01_20261004" /
                    "raw.json")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        update = raw["update"]
        snapshot = raw["after_acknowledged_update"]
        game = Game(snapshot["state_tic"], update["episode_after"],
                    (snapshot["state_variables"][1],
                     snapshot["state_variables"][0], 100.0))
        rows = []
        sampler = self.make_sampler(game, rows.append)
        result = sampler(game, Variables, 175)
        self.assertEqual((result.kill_count, result.death_count), (0, 0))
        self.assertEqual(result.producer["tic_before"], 1)
        self.assertEqual(result.producer["tic_after"], 11)
        self.assertEqual(result.producer["observation_status"], "UPDATE_RETURNED")
        self.assertFalse(rows[0]["controller_visible"])
        self.assertEqual(rows[0]["sample"], result.as_dict())
        with tempfile.TemporaryDirectory() as directory:
            sink = ScorerFileSink(Path(directory))
            sink.direct(result, lambda: 200)
            self.assertEqual(sink.samples[0]["payload"]["producer"]["tic_after"], 11)
            self.assertEqual(sink.samples[0]["controller_visible"], False)

    def test_endpoint_mismatch_never_publishes_sample(self):
        game = Game(state_tic=10, after_update=11)
        rows = []
        sampler = self.make_sampler(game, rows.append)
        with self.assertRaisesRegex(RuntimeError, "no GameState snapshot"):
            sampler(game, Variables, 175)
        self.assertEqual(rows[0]["status"], "UPDATE_UNAVAILABLE")
        self.assertIsNone(sampler.last)

    def test_configured_order_is_used_to_find_kill_and_death(self):
        game = Game(values=(5.0, 2.0, 100.0),
                    configured=("kill", "death", "health"))
        sampler = self.make_sampler(game)
        result = sampler(game, Variables, 175)
        self.assertEqual((result.kill_count, result.death_count), (5, 2))

    def test_duplicate_or_missing_required_counter_fails_closed(self):
        game = Game(configured=("death", "kill", "kill"))
        sampler = self.make_sampler(game)
        with self.assertRaisesRegex(ValueError, "configured once"):
            sampler(game, Variables, 175)
        self.assertIsNone(sampler.last)

    def test_fractional_counter_fails_closed(self):
        game = Game(values=(0.0, 1.5, 100.0))
        sampler = self.make_sampler(game)
        with self.assertRaisesRegex(ValueError, "score counter"):
            sampler(game, Variables, 175)
        self.assertIsNone(sampler.last)

    def test_boolean_snapshot_tic_fails_closed(self):
        game = Game(state_tic=True)
        sampler = self.make_sampler(game)
        with self.assertRaisesRegex(ValueError, "GameState tic"):
            sampler(game, Variables, 175)
        self.assertIsNone(sampler.last)


if __name__ == "__main__":
    unittest.main()
