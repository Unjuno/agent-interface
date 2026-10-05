"""Reject malformed terminal timeout values in the selected V15 scorer."""
import ast
import math
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
    namespace = {"ProgressSample": ProgressSample, "time": time, "math": math}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
    return namespace[function.name]


class FakeGame:
    def __init__(self, timeout_result, finished=True):
        self.timeout_result = timeout_result
        self.finished = finished

    def get_episode_time(self):
        return 10

    def is_episode_finished(self):
        return self.finished

    def is_player_dead(self):
        return False

    def get_game_variable(self, _variable):
        return 0.0

    def get_ticrate(self):
        return 35

    def is_episode_timeout_reached(self):
        return self.timeout_result


class TimeoutReadbackTests(unittest.TestCase):
    def setUp(self):
        self.sample = load_sample_function()
        self.variables = type("Variables", (), {"KILLCOUNT": 1, "DEATHCOUNT": 2})

    def test_non_boolean_timeout_readback_is_rejected(self):
        for value in (0, 1, 0.0, 1.0, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid timeout flag"):
                    self.sample(FakeGame(value), self.variables, 600,
                                clock_ns=lambda: 1)

    def test_exact_boolean_timeout_controls_success(self):
        for value, expected_success in ((False, True), (True, False)):
            with self.subTest(value=value):
                result = self.sample(FakeGame(value), self.variables, 600,
                                     clock_ns=lambda: 1)
                self.assertIs(result.success, expected_success)


if __name__ == "__main__":
    unittest.main(verbosity=2)
