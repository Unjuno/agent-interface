"""Exercise the V12 finish branch with a fake engine and clock."""
import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).with_name("session_map01_v12.py")


def load_finish(out, wall_seconds, close, emit):
    tree = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    finish = next(node for node in ast.walk(main)
                  if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                  and ast.unparse(node.test) == "command['op'] == 'finish'")
    if not isinstance(finish.body[-1], ast.Break):
        raise RuntimeError("expected V12 finish to leave the control loop")
    function = ast.FunctionDef(
        name="finish", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="game")],
            vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=finish.body[:-1], decorator_list=[])
    wrapper = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {
        "args": SimpleNamespace(out=out, timeout_seconds=100, skill=1),
        "control_started_ns": 0, "executor": object(),
        "vd": SimpleNamespace(GameVariable=SimpleNamespace(DEATHCOUNT="deaths", KILLCOUNT="kills")),
        "time": SimpleNamespace(perf_counter_ns=lambda: wall_seconds * 1_000_000_000),
        "json": json, "emit": emit, "close_before_control_effect": close,
    }
    exec(compile(wrapper, str(SOURCE), "exec"), namespace)
    return namespace["finish"]


class FinishScoringTests(unittest.TestCase):
    def finish(self, *, native_timeout=None, tic=50, refresh=False, dead=False, wall_seconds=5):
        game = SimpleNamespace(
            is_episode_finished=Mock(side_effect=[False, True] if refresh else [True, True]),
            is_player_dead=lambda: dead,
            get_episode_time=lambda: tic,
            get_ticrate=lambda: 35,
            get_game_variable={"deaths": int(dead), "kills": 1}.__getitem__,
            get_total_reward=lambda: 0.0,
            advance_action=Mock(),
        )
        if native_timeout is not None:
            game.is_episode_timeout_reached = Mock(return_value=native_timeout)
        with TemporaryDirectory() as directory:
            out = Path(directory)
            emitted, close = [], Mock()
            load_finish(out, wall_seconds, close, emitted.append)(game)
            self.assertEqual(close.call_args.args[1:], (out, emitted.append, "finish"))
            record = json.loads((out / "score.json").read_bytes())
            self.assertEqual(emitted, [record])
        if refresh:
            game.advance_action.assert_called_once_with(1, True)
        else:
            game.advance_action.assert_not_called()
        return record

    def test_native_timeout_is_not_map_exit_before_wall_cutoff(self):
        record = self.finish(native_timeout=True)
        self.assertTrue(record["episode_finished"])
        self.assertFalse(record["map_exit"])
        self.assertFalse(record["one_life_map_exit"])
        self.assertTrue(record["episode_timeout_reached"])

    def test_engine_tick_fallback_catches_timeout_at_final_refresh(self):
        for tic in (3500, 3501):
            with self.subTest(tic=tic):
                record = self.finish(tic=tic, refresh=True)
                self.assertFalse(record["map_exit"])
                self.assertTrue(record["episode_timeout_reached"])

    def test_finished_alive_before_timeout_can_exit(self):
        for native in (None, False):
            with self.subTest(native=native):
                record = self.finish(native_timeout=native, tic=3499)
                self.assertTrue(record["map_exit"])
                self.assertTrue(record["one_life_map_exit"])
                self.assertFalse(record["episode_timeout_reached"])

    def test_death_and_existing_wall_cutoff_still_prevent_exit(self):
        self.assertFalse(self.finish(native_timeout=False, dead=True)["map_exit"])
        self.assertFalse(self.finish(native_timeout=False, wall_seconds=95)["map_exit"])
