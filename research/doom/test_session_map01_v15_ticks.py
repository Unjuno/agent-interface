"""Exact episode-tick contract tests for the scorer selected by V39."""
import ast
import time
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("session_map01_v15.py")


class ProgressSample:
    def __init__(self, sample_ns, kills, deaths, finished, dead, success):
        self.sample_ns = sample_ns
        self.kills = kills
        self.deaths = deaths
        self.finished = finished
        self.dead = dead
        self.success = success


def load_sample_function():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "_coherent_progress_sample")
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {"ProgressSample": ProgressSample, "time": time}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
    return namespace[function.name]


class FakeGame:
    def __init__(self, before, after, kills=0, deaths=0, ticrate=35):
        self.tics = iter((before, after))
        self.last_tic = after
        self.scorer_reads = 0
        self.kills = kills
        self.deaths = deaths
        self.ticrate = ticrate

    def get_episode_time(self):
        try:
            self.last_tic = next(self.tics)
        except StopIteration:
            pass
        return self.last_tic

    def is_episode_finished(self):
        self.scorer_reads += 1
        return False

    def is_player_dead(self):
        self.scorer_reads += 1
        return False

    def get_game_variable(self, variable):
        self.scorer_reads += 1
        return self.kills if variable == 1 else self.deaths

    def get_ticrate(self):
        self.scorer_reads += 1
        return self.ticrate

    def is_episode_timeout_reached(self):
        self.scorer_reads += 1
        return False


class ExactScorerTickTests(unittest.TestCase):
    def setUp(self):
        self.sample = load_sample_function()
        self.variables = type("Variables", (), {"KILLCOUNT": 1, "DEATHCOUNT": 2})

    def test_fractional_and_boolean_initial_ticks_fail_before_scorer_reads(self):
        for invalid in (10.5, True, -1):
            with self.subTest(invalid=invalid):
                game = FakeGame(invalid, 11)
                with self.assertRaises(ValueError):
                    self.sample(game, self.variables, 600, clock_ns=lambda: 1)
                self.assertEqual(game.scorer_reads, 0)

    def test_fractional_post_sample_tick_is_rejected(self):
        for invalid in (10.5, -1):
            with self.subTest(invalid=invalid):
                game = FakeGame(10, invalid)
                with self.assertRaises(ValueError):
                    self.sample(game, self.variables, 600, clock_ns=lambda: 1)

    def test_exact_integer_ticks_still_produce_a_coherent_sample(self):
        game = FakeGame(10, 10)
        sample = self.sample(game, self.variables, 600, clock_ns=lambda: 1)
        self.assertEqual(sample.sample_ns, 1)
        self.assertEqual((sample.kills, sample.deaths), (0, 0))

    def test_malformed_progress_counters_are_rejected(self):
        for field, value in (("kills", 1.5), ("kills", True), ("kills", -1),
                             ("deaths", 2.5), ("deaths", False), ("deaths", -1)):
            with self.subTest(field=field, value=value):
                game = FakeGame(10, 10, **{field: value})
                with self.assertRaises(ValueError):
                    self.sample(game, self.variables, 600, clock_ns=lambda: 1)

    def test_invalid_ticrate_is_rejected(self):
        for value in (35.5, True, 0, -1):
            with self.subTest(value=value):
                game = FakeGame(10, 10, ticrate=value)
                with self.assertRaises(ValueError):
                    self.sample(game, self.variables, 600, clock_ns=lambda: 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
