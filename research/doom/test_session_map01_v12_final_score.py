"""Exercise the V12 finish branch with a fake engine and clock."""
import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).with_name("session_map01_v12.py")
MISSING_TIMEOUT_API = object()


def load_finish(out, wall_seconds, close, emit, *, exit_probe=False):
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
        "args": SimpleNamespace(out=out, timeout_seconds=100, skill=1, door_task_exit=exit_probe),
        "control_started_ns": 0, "executor": object(),
        "vd": SimpleNamespace(GameVariable=SimpleNamespace(DEATHCOUNT="deaths", KILLCOUNT="kills")),
        "time": SimpleNamespace(perf_counter_ns=lambda: wall_seconds * 1_000_000_000),
        "json": json, "emit": emit, "close_before_control_effect": close, "probe_delivery": None,
    }
    exec(compile(wrapper, str(SOURCE), "exec"), namespace)
    return namespace["finish"]


class FinishScoringTests(unittest.TestCase):
    def finish(self, *, native_timeout=MISSING_TIMEOUT_API, tic=50, refresh=False,
               finished=True, dead=False, wall_seconds=5):
        game = SimpleNamespace(
            is_episode_finished=Mock(side_effect=[finished and not refresh, finished]),
            is_player_dead=lambda: dead,
            get_episode_time=lambda: tic,
            get_ticrate=lambda: 35,
            get_game_variable={"deaths": int(dead), "kills": 1}.__getitem__,
            get_total_reward=lambda: 0.0,
            advance_action=Mock(),
        )
        if native_timeout is not MISSING_TIMEOUT_API:
            game.is_episode_timeout_reached = Mock(return_value=native_timeout)
        with TemporaryDirectory() as directory:
            out = Path(directory)
            emitted, close = [], Mock()
            load_finish(out, wall_seconds, close, emitted.append)(game)
            self.assertEqual(close.call_args.args[1:], (out, emitted.append, "finish"))
            record = json.loads((out / "score.json").read_bytes())
            self.assertEqual(emitted, [record])
        if refresh or not finished:
            game.advance_action.assert_called_once_with(1, True)
        else:
            game.advance_action.assert_not_called()
        self.assertEqual(record["scorer_refresh_calls_after_control"], game.advance_action.call_count)
        return record

    def test_synthetic_refresh_is_fenced_and_counted_in_finish(self):
        import threading
        game = SimpleNamespace(is_episode_finished=lambda: True, is_player_dead=lambda: False,
            is_episode_timeout_reached=lambda: False,
            get_game_variable={"deaths": 0, "kills": 0}.__getitem__, get_total_reward=lambda: 0.0)
        with TemporaryDirectory() as directory:
            out = Path(directory)
            emitted, close = [], Mock()
            finish = load_finish(out, 5, close, emitted.append)
            scope = finish.__globals__
            scope['args'].synthetic_exit_refresh = True
            scope['args'].synthetic_exit_pwad = Path('/fixed.wad')
            scope.update(door_coordinator=SimpleNamespace(finished=True, gate=SimpleNamespace(neutral=lambda session: True)),
                synthetic_heartbeat_count=4, synthetic_heartbeat_revision=7,
                lock=threading.Lock(), latest_observation={'sequence': 1}, deepcopy=lambda value: dict(value),
                backend=object(), session=object(),
                synthetic_neutral_heartbeat=Mock(return_value={'verified': True}))
            def refresh(engine, directory, neutral, owner, *, deadline_ns):
                close.assert_called_once()
                self.assertTrue(neutral())
                self.assertTrue(owner()['verified'])
                self.assertEqual(deadline_ns, 6_000_000_000)
                return {'disposition': 'refreshed', 'refresh_calls': 1}
            scope['synchronize_terminal'] = refresh
            finish(game)
            self.assertEqual(json.loads((out / 'score.json').read_text())['scorer_refresh_calls_after_control'], 1)
            self.assertEqual(emitted[0]['event'], 'synthetic_terminal_refresh')
            self.assertEqual(scope['synthetic_neutral_heartbeat'].call_args.kwargs['expected_revision'], 7)

    def test_synthetic_refresh_requires_all_four_heartbeats(self):
        with TemporaryDirectory() as directory:
            close = Mock()
            finish = load_finish(Path(directory), 5, close, lambda row: None)
            scope = finish.__globals__
            scope['args'].synthetic_exit_refresh = True
            scope.update(door_coordinator=SimpleNamespace(finished=True), synthetic_heartbeat_count=3,
                         synthetic_heartbeat_revision=7)
            with self.assertRaises(ValueError): finish(object())
            close.assert_called_once()

    def test_native_timeout_is_not_map_exit_before_wall_cutoff(self):
        record = self.finish(native_timeout=True)
        self.assertTrue(record["episode_finished"])
        self.assertFalse(record["map_exit"])
        self.assertFalse(record["one_life_map_exit"])
        self.assertTrue(record["episode_timeout_reached"])
        self.assertEqual(record["episode_timeout_source"], "engine_api")
        self.assertIsNone(record["engine_tic_limit_reached"])

    def test_engine_tick_limit_does_not_prove_terminal_timeout(self):
        for tic in (3500, 3501):
            with self.subTest(tic=tic):
                record = self.finish(tic=tic, refresh=True)
                self.assertFalse(record["map_exit"])
                self.assertIsNone(record["episode_timeout_reached"])
                self.assertEqual(record["episode_timeout_source"], "engine_tic_limit")
                self.assertTrue(record["engine_tic_limit_reached"])

    def test_unfinished_at_tic_limit_is_not_a_confirmed_timeout(self):
        record = self.finish(tic=3500, finished=False)
        self.assertFalse(record["map_exit"])
        self.assertFalse(record["episode_finished"])
        self.assertIsNone(record["episode_timeout_reached"])
        self.assertEqual(record["episode_timeout_source"], "engine_tic_limit")
        self.assertTrue(record["engine_tic_limit_reached"])

    def test_non_boolean_engine_timeout_stays_unknown_and_cannot_exit(self):
        for value in (None, 0, 1, "true"):
            with self.subTest(value=value):
                record = self.finish(native_timeout=value)
                self.assertFalse(record["map_exit"])
                self.assertIsNone(record["episode_timeout_reached"])
                self.assertEqual(record["episode_timeout_source"], "engine_api")
                self.assertIsNone(record["engine_tic_limit_reached"])

    def test_missing_engine_tic_keeps_timeout_unknown(self):
        record = self.finish(tic=None)
        self.assertFalse(record["map_exit"])
        self.assertIsNone(record["episode_timeout_reached"])
        self.assertEqual(record["episode_timeout_source"], "engine_tic_limit")
        self.assertIsNone(record["engine_tic_limit_reached"])

    def test_finished_alive_needs_native_non_timeout_evidence(self):
        record=self.finish(native_timeout=False,tic=3499)
        self.assertTrue(record['map_exit']);self.assertTrue(record['one_life_map_exit'])
        for tic in (0,3499,3500,3501):
            with self.subTest(tic=tic):
                record=self.finish(tic=tic)
                self.assertFalse(record['map_exit'])
                self.assertIsNone(record['episode_timeout_reached'])

    def test_unknown_terminal_values_cannot_be_scored_as_exit(self):
        for finished, dead in ((True, None), (True, 0)):
            with self.subTest(finished=finished, dead=dead), TemporaryDirectory() as directory:
                game = SimpleNamespace(is_episode_finished=lambda: finished, is_player_dead=lambda: dead,
                    is_episode_timeout_reached=lambda: False, get_episode_time=lambda: 50,
                    get_ticrate=lambda: 35, get_game_variable=lambda key: 0,
                    get_total_reward=lambda: 0.0, advance_action=Mock())
                out=Path(directory); emitted=[]
                load_finish(out, 5, Mock(), emitted.append)(game)
                self.assertFalse(json.loads((out/'score.json').read_text())['map_exit'])

    def test_invalid_death_count_cannot_become_one_life_exit(self):
        for value in (0.5,-0.5,False,float('nan'),float('inf')):
            with self.subTest(value=value), TemporaryDirectory() as directory:
                game=SimpleNamespace(is_episode_finished=lambda:True,is_player_dead=lambda:False,
                    is_episode_timeout_reached=lambda:False,get_game_variable=lambda key: value if key=='deaths' else 0.0,
                    get_total_reward=lambda:0.0,advance_action=Mock())
                out=Path(directory)
                with self.assertRaises(ValueError):load_finish(out,5,Mock(),lambda row:None)(game)
                self.assertFalse((out/'score.json').exists())

    def test_actual_command_loop_propagates_finish_scoring_failure(self):
        tree=ast.parse(SOURCE.read_bytes())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        loop=next(n for n in ast.walk(main) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and n.iter.attr=='stdin')
        wrapper=ast.parse('def run(executor):\n pass\n');wrapper.body[0].body=[loop];ast.fix_missing_locations(wrapper)
        game=SimpleNamespace(is_episode_finished=lambda:None,advance_action=Mock())
        with TemporaryDirectory() as directory:
            out=Path(directory);events=[]
            scope={'sys':SimpleNamespace(stdin=['{"op":"finish"}']), 'json':json,
              'args':SimpleNamespace(out=out,timeout_seconds=100,skill=1,fresh_neutral_fixture_setup=False,verified_fixture_setup=False),
              'time':SimpleNamespace(perf_counter_ns=lambda:5_000_000_000),'control_started_ns':0,
              'door_coordinator':None,'probe_delivery':None,'game':game,'executor':object(),
              'close_before_control_effect':lambda *args:None,'emit':events.append,
              'Expired':type('Expired',(Exception,),{})}
            exec(compile(wrapper,str(SOURCE),'exec'),scope)
            with self.assertRaises(ValueError):scope['run'](object())
            self.assertFalse((out/'score.json').exists());game.advance_action.assert_not_called()

    def test_unknown_initial_terminal_state_does_not_advance(self):
        game=SimpleNamespace(is_episode_finished=Mock(side_effect=[None,True]),
                             advance_action=Mock(),is_player_dead=lambda:False,
                             is_episode_timeout_reached=lambda:False,
                             get_game_variable=lambda key:0,get_total_reward=lambda:0)
        with TemporaryDirectory() as directory:
            out=Path(directory)
            with self.assertRaises(ValueError):load_finish(out,5,Mock(),lambda row:None)(game)
            game.advance_action.assert_not_called()
            self.assertFalse((out/'score.json').exists())

    def test_actual_exit_probe_finish_loop_remains_passive(self):
        import threading
        tree=ast.parse(SOURCE.read_bytes())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        loop=next(n for n in ast.walk(main) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and n.iter.attr=='stdin')
        wrapper=ast.parse('def run(executor):\n pass\n');wrapper.body[0].body=[loop];ast.fix_missing_locations(wrapper)
        game=SimpleNamespace(is_episode_finished=lambda:False,is_player_dead=lambda:False,
            is_episode_timeout_reached=lambda:False,get_game_variable=lambda key:0,
            get_total_reward=lambda:0.0,advance_action=Mock())
        with TemporaryDirectory() as directory:
            out=Path(directory);events=[]
            scope={'sys':SimpleNamespace(stdin=['{"op":"finish"}']), 'json':json,
              'args':SimpleNamespace(out=out,timeout_seconds=100,skill=1,door_task_exit=True,
                       fresh_neutral_fixture_setup=False,verified_fixture_setup=False),
              'time':SimpleNamespace(perf_counter_ns=lambda:5_000_000_000),'control_started_ns':0,
              'door_coordinator':SimpleNamespace(finished=True,pending=None),
              'door_scorer':SimpleNamespace(failed=False,index=1,STAGES=('exit-probe',)),
              'latest_observation':None,'lock':threading.RLock(),'deepcopy':lambda value:value,
              'probe_delivery':None,'game':game,'close_before_control_effect':lambda *args:None,
              'vd':SimpleNamespace(GameVariable=SimpleNamespace(DEATHCOUNT='deaths',KILLCOUNT='kills')),
              'emit':events.append,'Expired':type('Expired',(Exception,),{})}
            exec(compile(wrapper,str(SOURCE),'exec'),scope);scope['run'](object())
            game.advance_action.assert_not_called()
            self.assertFalse(json.loads((out/'score.json').read_text())['map_exit'])

    def test_exit_probe_finish_never_advances_unfinished_game(self):
        game=SimpleNamespace(is_episode_finished=lambda:False,is_player_dead=lambda:False,
            is_episode_timeout_reached=lambda:False,get_game_variable=lambda key:0,
            get_total_reward=lambda:0.0,advance_action=Mock())
        with TemporaryDirectory() as directory:
            out=Path(directory);load_finish(out,5,Mock(),lambda row:None,exit_probe=True)(game)
            game.advance_action.assert_not_called()
            score=json.loads((out/'score.json').read_text())
            self.assertFalse(score['map_exit']);self.assertEqual(score['scorer_refresh_calls_after_control'],0)

    def test_scorer_refresh_failure_preserves_error_without_publishing_score(self):
        failure = RuntimeError("synthetic engine refresh failed")
        game = SimpleNamespace(is_episode_finished=lambda: False,
                               advance_action=Mock(side_effect=failure),
                               is_player_dead=Mock())
        with TemporaryDirectory() as directory:
            out = Path(directory)
            emitted, close = [], Mock()
            with self.assertRaises(RuntimeError) as raised:
                load_finish(out, 5, close, emitted.append)(game)
            self.assertIs(raised.exception, failure)
            self.assertFalse((out / "score.json").exists())
            self.assertEqual(emitted, [])
        close.assert_called_once()
        game.advance_action.assert_called_once_with(1, True)
        game.is_player_dead.assert_not_called()

    def test_death_and_existing_wall_cutoff_still_prevent_exit(self):
        self.assertFalse(self.finish(native_timeout=False, dead=True)["map_exit"])
        self.assertFalse(self.finish(native_timeout=False, wall_seconds=95)["map_exit"])
