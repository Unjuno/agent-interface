"""Actual session command loop with selected Fake X Executor; no engine setup."""
import ast
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_map01_process_identity_backend import backend_fixture, Executor, native


def command_loop(stdin):
    source = Path(__file__).with_name('session_map01_v12.py')
    tree = ast.parse(source.read_bytes(), filename=str(source))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    loop = next(n for n in ast.walk(main) if isinstance(n, ast.For) and
                isinstance(n.target, ast.Name) and n.target.id == 'line')
    args = ('executor', 'backend', 'game', 'args', 'session', 'emit',
            'latest_observation', 'control_started_ns')
    function = ast.FunctionDef(name='commands', args=ast.arguments(
        posonlyargs=[], args=[ast.arg(arg=n) for n in args], vararg=None,
        kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=[loop], decorator_list=[])
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != 'main']
    module = ast.fix_missing_locations(ast.Module(body=definitions + [function], type_ignores=[]))
    namespace = dict(json=json, Path=Path, time=time, hashlib=hashlib, shutil=shutil,
                     sys=SimpleNamespace(stdin=io.StringIO(stdin)),
                     Expired=type('Expired', (Exception,), {}),
                     vd=SimpleNamespace(__version__='fake', GameVariable=SimpleNamespace(DEATHCOUNT=1, KILLCOUNT=2)),
                     iwad_sha256='f'*64, loaded_fixture=None,
                     FIXTURE_SCHEMA='map01_os_input_fixture_v1', SETUP_INPUT_CONTRACT='fixture')
    exec(compile(module, str(source), 'exec'), namespace)
    return namespace['commands']


class RetirementBoundaryTests(unittest.TestCase):
    def invoke(self, backend, events, executor, operation, sink=None):
        effects = []
        session = backend.session
        session.tmp = backend.out / 'session'
        session.tmp.mkdir(exist_ok=True)
        def save(path):
            effects.append('save')
            Path(path).write_bytes(b'fake engine save')
        game = SimpleNamespace(
            is_episode_finished=lambda: False,
            advance_action=lambda *a: effects.append('advance'),
            is_player_dead=lambda: False,
            get_game_variable=lambda v: 0,
            get_total_reward=lambda: 0,
            get_episode_time=lambda: 1,
            save=save)
        arguments = SimpleNamespace(out=backend.out, fixture_out=backend.out/'fixture.png',
                                    timeout_seconds=600, skill=1, seed=7)
        observations = [r for r in events if r.get('event') == 'observation']
        run = command_loop(json.dumps({'op': operation}) + '\n')
        try:
            run(executor, backend, game, arguments, session, sink or events.append,
                observations[-1] if observations else {}, time.perf_counter_ns())
        finally:
            print(json.dumps({'operation': operation, 'game_effect_calls': effects,
                'post_control_score_count': sum(r.get('event') == 'post_control_score' for r in events),
                'fixture_saved_count': sum(r.get('event') == 'fixture_saved' for r in events),
                'obligation': executor.release_obligation_snapshot()}), flush=True)
            self.effects = effects

    def test_failed_release_blocks_finish_and_fixture_effects(self):
        for operation in ('finish', 'save_fixture'):
            with self.subTest(operation=operation), backend_fixture() as (backend, events, generation, fake):
                backend.snapshot('source', 0)
                entered, resume, terminal = (threading.Event() for _ in range(3))
                original = native.xtest.fake_input.side_effect
                def send(connection, event, code):
                    if event == native.X.KeyRelease:
                        entered.set()
                        if not resume.wait(6): raise RuntimeError('test gate not resumed')
                    return original(connection, event, code)
                def emit(row):
                    events.append(row)
                    if row.get('event') == 'terminal': terminal.set()
                executor = Executor(backend, emit)
                try:
                    with patch.object(native.xtest, 'fake_input', side_effect=send):
                        executor.submit('original', [{'op':'hold', 'keys':['a'], 'duration_ms':5}],
                                        backend.sequence, time.perf_counter_ns()+10_000_000_000)
                        self.assertTrue(entered.wait(1))
                        self.assertTrue(terminal.wait(3))
                        with self.assertRaisesRegex(RuntimeError, 'input retirement'):
                            self.invoke(backend, events, executor, operation)
                        self.assertEqual(self.effects, [])
                        self.assertEqual(fake.down, {38})
                        self.assertFalse(resume.is_set())
                        receipt = json.loads((backend.out/'control-boundary-failure.json').read_text())
                        self.assertEqual(receipt['release_obligation'],
                                         json.loads(json.dumps(executor.release_obligation_snapshot())))
                        self.assertEqual(receipt['operation'], operation)
                        self.assertIs(receipt['grants_input_authority'], False)
                        self.assertEqual(receipt['task_effect'], 'unknown')
                        self.assertFalse(any(r.get('event') in ('post_control_score','fixture_saved') for r in events))
                finally:
                    resume.set()
                    executor.close()

    def test_unstarted_ambiguous_admission_is_not_retired(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('source', 0)
            def refuse(row):
                events.append(row)
                if row.get('event') == 'accepted': raise OSError('admission delivery unknown')
            executor = Executor(backend, refuse)
            try:
                with self.assertRaises(OSError):
                    executor.submit('unstarted', [{'op':'observe'}], backend.sequence,
                                    time.perf_counter_ns()+1_000_000_000)
                with self.assertRaisesRegex(RuntimeError, 'input retirement'):
                    self.invoke(backend, events, executor, 'finish')
                self.assertEqual(self.effects, [])
                self.assertEqual(fake.down, set())
                receipt = json.loads((backend.out/'control-boundary-failure.json').read_text())
                self.assertEqual(receipt['active_intent'], 'unstarted')
                self.assertIsNone(receipt['release_obligation'])
            finally: executor.close()

    def test_verified_retirement_allows_each_original_effect_path(self):
        for operation in ('finish', 'save_fixture'):
            with self.subTest(operation=operation), backend_fixture() as (backend, events, generation, fake):
                backend.snapshot('source', 0)
                executor = Executor(backend, events.append)
                try:
                    executor.submit('healthy', [{'op':'hold','keys':['a'],'duration_ms':5}],
                                    backend.sequence, time.perf_counter_ns()+1_000_000_000)
                    executor.active[2].join(1) if executor.active else None
                    self.invoke(backend, events, executor, operation)
                    self.assertIn('advance', self.effects)
                    self.assertEqual('save' in self.effects, operation == 'save_fixture')
                    self.assertFalse((backend.out/'control-boundary-failure.json').exists())
                    self.assertEqual(fake.down, set())
                finally: executor.close()

    def test_failure_save_and_delivery_errors_cannot_resume_effects(self):
        for fault in ('collision', 'delivery'):
            with self.subTest(fault=fault), backend_fixture() as (backend, events, generation, fake):
                backend.snapshot('source', 0)
                def refuse(row):
                    if row.get('event') == 'accepted': raise OSError('admission unknown')
                executor = Executor(backend, refuse)
                try:
                    with self.assertRaises(OSError):
                        executor.submit('unstarted', [{'op':'observe'}], backend.sequence,
                                        time.perf_counter_ns()+1_000_000_000)
                    receipt = backend.out/'control-boundary-failure.json'
                    if fault == 'collision': receipt.write_bytes(b'original custody sentinel')
                    def sink(row):
                        if row.get('event') == 'control_boundary_failed':
                            row['active_intent'] = 'external rewrite'
                            raise OSError('failure delivery unknown')
                        events.append(row)
                    with self.assertRaises(OSError):
                        self.invoke(backend, events, executor, 'finish', sink)
                    self.assertEqual(self.effects, [])
                    if fault == 'collision':
                        self.assertEqual(receipt.read_bytes(), b'original custody sentinel')
                    else:
                        self.assertEqual(json.loads(receipt.read_text())['active_intent'], 'unstarted')
                    self.assertFalse(any(r.get('event') == 'post_control_score' for r in events))
                finally: executor.close()

    def test_close_error_prevents_engine_effects(self):
        with backend_fixture() as (backend, events, generation, fake):
            executor = Executor(backend, events.append)
            try:
                error = RuntimeError('close sentinel')
                with patch.object(executor, 'close', side_effect=error):
                    with self.assertRaises(RuntimeError) as caught:
                        self.invoke(backend, events, executor, 'finish')
                self.assertIs(caught.exception, error)
                self.assertEqual(self.effects, [])
            finally: executor.close()


if __name__ == '__main__': unittest.main()
