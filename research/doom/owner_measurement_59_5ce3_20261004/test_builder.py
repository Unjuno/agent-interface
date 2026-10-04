"""Executable-source construction tests; no native input or game execution."""
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import types
import unittest
import sys
import builtins
import hashlib
import tempfile

HERE = Path(__file__).resolve().parent
PIN = '12e4c1ebaf382d70760eafbe3cf2e5fda90a9d2c'


class BuilderTests(unittest.TestCase):
    def builder(self):
        path = HERE / 'build_owner.py'
        self.assertTrue(path.is_file(), 'missing pinned-source measurement builder')
        spec = importlib.util.spec_from_file_location('measurement_builder', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def source(self):
        if os.environ.get('OWNER_MEASUREMENT_SOURCE_FILE'):
            return Path(os.environ['OWNER_MEASUREMENT_SOURCE_FILE']).read_bytes()
        if os.environ.get('OWNER_MEASUREMENT_SOURCE_ROOT'):
            return (Path(os.environ['OWNER_MEASUREMENT_SOURCE_ROOT']) /
                    'research/live_control/input_owner_v10.py').read_bytes()
        return subprocess.check_output(
            ['git', 'show', PIN + ':research/live_control/input_owner_v10.py'], cwd=HERE)

    def test_changed_source_is_rejected_before_generation(self):
        builder = self.builder()
        with self.assertRaises(ValueError):
            builder.instrument(self.source() + b'\n# drift\n')

    def bundle_sources(self):
        names = ('input_owner_v10.py', 'doom_typed_release_backend_v1.py',
                 'session_map01_v12.py', 'map01_overlap_controller_v39.py')
        if os.environ.get('OWNER_MEASUREMENT_SOURCE_ROOT'):
            root = Path(os.environ['OWNER_MEASUREMENT_SOURCE_ROOT']) / 'research'
            return {name: (root / ('live_control' if name == 'input_owner_v10.py' else 'doom') /
                          name).read_bytes() for name in names}
        return {name: subprocess.check_output(['git', 'show', PIN + ':research/' +
            ('live_control/' if name == 'input_owner_v10.py' else 'doom/') + name],
            cwd=HERE) for name in names}

    def test_composed_controller_selects_only_the_measured_session(self):
        compose = getattr(self.builder(), 'compose', None)
        self.assertTrue(callable(compose), 'missing selected-path composition builder')
        root = HERE.parents[2]
        destination = HERE / 'generated'
        bundle = compose(self.bundle_sources(), root, destination)
        self.assertEqual(set(bundle), {'input_owner_measured_5ce3.py',
            'doom_release_measured_5ce3.py', 'session_measured_5ce3.py', 'controller_measured_5ce3.py'})
        for text in bundle.values():
            compile(text, '<derived-source>', 'exec')
        tree = ast.parse(bundle['controller_measured_5ce3.py'])
        command = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                       and n.name == 'session_command')
        env = dict(sys=sys, HERE=root / 'research/doom', MEASUREMENT_HERE=destination)
        exec(compile(ast.Module(body=[command], type_ignores=[]), '<session-command>', 'exec'), env)
        output_dir = Path('/out')
        manifest = Path('/fixtures/frozen.json')
        args = types.SimpleNamespace(seed=59, load_fixture_manifest=manifest)
        self.assertEqual(env['session_command'](args, output_dir), [sys.executable,
            str(destination / 'session_measured_5ce3.py'), '--out', str(output_dir), '--seed', '59',
            '--timeout-seconds', '600', '--skill', '1', '--load-fixture-manifest', str(manifest)])

    def test_composition_refuses_changed_session(self):
        compose = getattr(self.builder(), 'compose', None)
        self.assertTrue(callable(compose), 'missing selected-path composition builder')
        sources = self.bundle_sources()
        sources['session_map01_v12.py'] += b'\n# changed\n'
        with self.assertRaises(ValueError):
            compose(sources, HERE.parents[2], HERE / 'generated')

    def test_controller_sets_dependency_path_before_first_doom_import(self):
        root = HERE.parents[2]
        destination = HERE / 'generated'
        tree = ast.parse(self.builder().compose(self.bundle_sources(), root,
                        destination)['controller_measured_5ce3.py'])
        prefix = []
        for node in tree.body:
            # Exercise actual generated setup and first local import; unrelated
            # external imports are excluded, so this is not a full import test.
            if isinstance(node, (ast.Assign, ast.Expr)):
                prefix.append(node)
            if isinstance(node, ast.ImportFrom) and node.module == 'map01_stagnation_v1':
                prefix.append(node)
                break
        fake_sys = types.SimpleNamespace(path=[])
        selected = []
        def local_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name != 'map01_stagnation_v1':
                raise AssertionError('unexpected import boundary')
            if str(root / 'research/doom') not in fake_sys.path:
                raise ModuleNotFoundError('DOOM dependency root unavailable before first import')
            selected.append(name)
            return types.SimpleNamespace(descriptor=object(), normalized_mae=object())
        env = dict(Path=Path, sys=fake_sys, __file__=str(destination / 'controller_measured_5ce3.py'),
                   __builtins__={**vars(builtins), '__import__': local_import})
        failure = None
        try:
            exec(compile(ast.Module(body=prefix, type_ignores=[]), '<controller-import-prefix>', 'exec'), env)
        except ModuleNotFoundError as error:
            failure = str(error)
        self.assertIsNone(failure, 'generated controller imports before dependency setup')
        self.assertEqual(selected, ['map01_stagnation_v1'])

    def test_session_exposes_repository_package_root_before_backend_import(self):
        root = HERE.parents[2]
        destination = HERE / 'generated'
        tree = ast.parse(self.builder().compose(self.bundle_sources(), root,
                        destination)['session_measured_5ce3.py'])
        prefix = []
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.Expr)):
                prefix.append(node)
            if isinstance(node, ast.ImportFrom) and node.module == 'doom_release_measured_5ce3':
                prefix.append(node)
                break
        fake_sys = types.SimpleNamespace(path=[])
        def local_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name != 'doom_release_measured_5ce3':
                raise AssertionError('unexpected import boundary')
            if str(root) not in fake_sys.path:
                raise ModuleNotFoundError('repository package root unavailable to inherited imports')
            return types.SimpleNamespace(Backend=object(), suite=object())
        env = dict(Path=Path, sys=fake_sys, __file__=str(destination / 'session_measured_5ce3.py'),
                   __builtins__={**vars(builtins), '__import__': local_import})
        failure = None
        try:
            exec(compile(ast.Module(body=prefix, type_ignores=[]), '<session-import-prefix>', 'exec'), env)
        except ModuleNotFoundError as error:
            failure = str(error)
        self.assertIsNone(failure, 'missing root for inherited package-qualified imports')

    def custody_function(self):
        text = self.builder().compose(self.bundle_sources(), HERE.parents[2],
                    HERE / 'generated')['session_measured_5ce3.py']
        functions = [node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)
                     and node.name == '_measurement_selected_source']
        self.assertEqual(len(functions), 1, 'missing selected-import custody gate')
        modules = {}
        env = dict(Path=Path, hashlib=hashlib, sys=types.SimpleNamespace(modules=modules))
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<selected-custody>', 'exec'), env)
        return env['_measurement_selected_source'], modules

    def test_custody_rejects_selected_file_at_wrong_path_even_with_equal_bytes(self):
        gate, modules = self.custody_function()
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / 'expected.py'
            other = Path(temporary) / 'substitute.py'
            first.write_bytes(b'fixture')
            other.write_bytes(b'fixture')
            modules['selected'] = types.SimpleNamespace(__file__=str(other))
            with self.assertRaises(ValueError):
                gate('selected', first, hashlib.sha256(b'fixture').hexdigest())

    def test_custody_reports_actual_selected_file_and_rejects_changed_bytes(self):
        gate, modules = self.custody_function()
        with tempfile.TemporaryDirectory() as temporary:
            selected = Path(temporary) / 'expected.py'
            selected.write_bytes(b'fixture')
            modules['selected'] = types.SimpleNamespace(__file__=str(selected))
            digest = hashlib.sha256(b'fixture').hexdigest()
            row = gate('selected', selected, digest)
            self.assertEqual(row, dict(module='selected', path=str(selected.resolve()), sha256=digest))
            selected.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                gate('selected', selected, digest)

    def test_connected_import_gate_rejects_backend_owner_class_substitution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / 'research/doom/candidate'
            destination.mkdir(parents=True)
            bundle = self.builder().compose(self.bundle_sources(), root, destination)
            for name, text in bundle.items():
                (destination / name).write_bytes(text.encode())
            tree = ast.parse(bundle['session_measured_5ce3.py'])
            gate_nodes = [node for node in tree.body
                if (isinstance(node, ast.FunctionDef) and node.name == '_measurement_selected_source')
                or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                    and target.id == 'MEASUREMENT_IMPORTED_SOURCES' for target in node.targets))
                or (isinstance(node, ast.If) and 'Backend.__module__' in ast.unparse(node.test))]
            self.assertEqual(len(gate_nodes), 3, 'missing connected custody/identity statements')
            code = compile(ast.Module(body=gate_nodes, type_ignores=[]), '<connected-import-gate>', 'exec')
            owner_class = type('InputOwner', (), {})
            backend_class = type('Backend', (), {'__module__': 'doom_release_measured_5ce3'})
            modules = {
                'input_owner_measured_5ce3': types.SimpleNamespace(
                    __file__=str(destination / 'input_owner_measured_5ce3.py'), InputOwner=owner_class),
                'doom_release_measured_5ce3': types.SimpleNamespace(
                    __file__=str(destination / 'doom_release_measured_5ce3.py'), InputOwner=owner_class)}
            env = dict(sys=types.SimpleNamespace(modules=modules), Path=Path, hashlib=hashlib,
                       MEASUREMENT_HERE=destination, Backend=backend_class)
            exec(code, env)
            self.assertEqual([row['module'] for row in env['MEASUREMENT_IMPORTED_SOURCES']],
                             ['doom_release_measured_5ce3', 'input_owner_measured_5ce3'])
            modules['doom_release_measured_5ce3'].InputOwner = type('OtherOwner', (), {})
            with self.assertRaises(ValueError):
                exec(code, env)

    def test_repository_lease_intent_token_is_emitted_for_key_and_cleanup(self):
        import copy
        import threading
        import time
        import uuid

        if os.environ.get('OWNER_MEASUREMENT_SOURCE_ROOT'):
            source_root = Path(os.environ['OWNER_MEASUREMENT_SOURCE_ROOT'])
            base_source = (source_root / 'research/live_control/lease.py').read_bytes()
            cause_source = (source_root / 'research/live_control/lease_cause_v1.py').read_bytes()
        else:
            base_source = subprocess.check_output(
                ['git', 'show', PIN + ':research/live_control/lease.py'], cwd=HERE)
            cause_source = subprocess.check_output(
                ['git', 'show', PIN + ':research/live_control/lease_cause_v1.py'], cwd=HERE)
        base_tree = ast.parse(base_source)
        base_node = next(n for n in base_tree.body
                         if isinstance(n, ast.ClassDef) and n.name == 'Lease')
        base_env = dict(threading=threading, time=time)
        exec(compile(ast.Module(body=[base_node], type_ignores=[]),
                     '<repository-lease-base>', 'exec'), base_env)
        cause_tree = ast.parse(cause_source)
        cause_node = next(n for n in cause_tree.body
                          if isinstance(n, ast.ClassDef) and n.name == 'Lease')
        cause_env = dict(copy=copy, threading=threading, uuid=uuid,
                         Previous=base_env['Lease'])
        exec(compile(ast.Module(body=[cause_node], type_ignores=[]),
                     '<repository-cause-lease>', 'exec'), cause_env)
        lease = cause_env['Lease'](time.perf_counter_ns() + 2_000_000_000)
        self.assertTrue(lease.intent_token)
        self.assertFalse(hasattr(lease, 'token'))

        tree = ast.parse(self.builder().instrument(self.source()))
        helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name.startswith('_measurement_')]
        env = dict(time=time)
        exec(compile(ast.Module(body=helpers, type_ignores=[]),
                     '<measurement-helpers>', 'exec'), env)
        owner = types.SimpleNamespace(owner_id='owner-real-lease', records=[])
        rows = []
        env['_measurement_emit'](owner, lease, 'owner_key_press', 38, 1, time)
        env['_measurement_mark'](rows, owner, lease, 38, time)
        self.assertEqual(owner.records[0]['intent'], lease.intent_token)
        self.assertEqual(rows[0]['intent'], lease.intent_token)

    def key_case(self, identity_failure=False):
        tree = ast.parse(self.builder().instrument(self.source()))
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and ast.unparse(n.test) == "op in ('down', 'up')")
        code = compile(ast.fix_missing_locations(ast.Module(body=branch.body,
                        type_ignores=[])), '<generated-key-branch>', 'exec')
        events = []
        class Display:
            def keysym_to_keycode(self, value): return 38
            def sync(self): events.append('sync')
        class Lease:
            deadline = 100000
            @property
            def intent_token(self):
                if identity_failure:
                    raise ValueError('injected key telemetry identity failure')
                return 'intent-one'
            cancel = types.SimpleNamespace(is_set=lambda: False)
            def check(self): pass
        ticks = iter(range(100, 1000))
        owner = types.SimpleNamespace(owner_id='owner-one', records=[])
        env = dict(d=Display(), XK=types.SimpleNamespace(string_to_keysym=lambda x: x),
                   X=types.SimpleNamespace(KeyPress=2, KeyRelease=3),
                   xtest=types.SimpleNamespace(fake_input=lambda d, kind, key: events.append((kind, key))),
                   time=types.SimpleNamespace(perf_counter_ns=lambda: next(ticks)),
                   self=owner, lease=Lease(), held={}, touched=set(), active=None,
                   fault=None, invalid_focus=lambda lease: False, key='a', op='down')
        helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name.startswith('_measurement_')]
        exec(compile(ast.Module(body=helpers, type_ignores=[]), '<measurement-helpers>', 'exec'), env)
        return code, env, events, owner

    def test_generated_key_branch_retains_identity_and_explicit_up_return(self):
        code, env, events, owner = self.key_case()
        exec(code, env)
        self.assertEqual(events, [(2, 38), 'sync'])
        press = owner.records[0]
        self.assertEqual((press['event'], press['owner_id'], press['intent'], press['keycode']),
                         ('owner_key_press', 'owner-one', 'intent-one', 38))
        self.assertLessEqual(press['request_started_ns'], press['sync_completed_ns'])
        self.assertFalse(press['grants_input_authority'])
        env['op'] = 'up'
        exec(code, env)
        self.assertIsNone(env['result'])
        self.assertEqual(events, [(2, 38), 'sync', (3, 38), 'sync'])
        self.assertEqual(env['held'], {})
        up = owner.records[1]
        self.assertEqual((up['event'], up['owner_id'], up['intent'], up['keycode']),
                         ('owner_explicit_key_up', 'owner-one', 'intent-one', 38))

    def test_key_identity_failure_preserves_press_result_and_explicit_up(self):
        code, env, events, owner = self.key_case(identity_failure=True)
        errors = []
        for op in ('down', 'up'):
            env['op'] = op
            try:
                exec(code, env)
            except Exception as error:
                errors.append((op, type(error).__name__))
            else:
                if op == 'down':
                    self.assertEqual(env['result']['event'], 'input_admission')
                else:
                    self.assertIsNone(env['result'])
        self.assertEqual(errors, [], 'telemetry must not replace successful input return')
        self.assertEqual(events, [(2, 38), 'sync', (3, 38), 'sync'])
        self.assertEqual(env['held'], {})
        self.assertEqual(owner.records, [])

    def cleanup_case(self, clock_failure=False, identity_failure=False):
        tree = ast.parse(self.builder().instrument(self.source()))
        release = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                       and n.name == 'release')
        wrapper = ast.parse('''
def factory(held, active, self, d, xtest, X, time):
    revision = 0
    buttons = {}
    touched_buttons = set()
    touched = set(held)
''').body[0]
        wrapper.body += [release, ast.Return(value=ast.Name(id='release', ctx=ast.Load()))]
        helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name.startswith('_measurement_')]
        env = {}
        exec(compile(ast.fix_missing_locations(ast.Module(body=helpers + [wrapper],
                     type_ignores=[])), '<generated-release>', 'exec'), env)
        events = []
        class Display:
            def sync(self): events.append('sync')
            def screen(self): return types.SimpleNamespace(root=types.SimpleNamespace(
                query_pointer=lambda: types.SimpleNamespace(mask=0)))
            def query_keymap(self): return bytes(32)
        class Lease:
            deadline = 10000
            @property
            def intent_token(self):
                if identity_failure:
                    raise ValueError('injected telemetry identity failure')
                return 'intent-one'
        lease = Lease()
        owner = types.SimpleNamespace(owner_id='owner-one', records=[])
        ticks = iter(range(100, 1000))
        def timestamp():
            tick = next(ticks)
            if clock_failure and tick < 103:
                raise ValueError('injected telemetry clock failure')
            return tick
        held = {38: lease, 39: lease}
        call = env['factory'](held, lease, owner, Display(),
            types.SimpleNamespace(fake_input=lambda d, kind, key: events.append((kind, key))),
            types.SimpleNamespace(KeyRelease=3, ButtonRelease=5, Button1Mask=256),
            types.SimpleNamespace(perf_counter_ns=timestamp))
        record = call('cancelled')
        return record, events, held

    def test_bulk_cleanup_retains_per_key_identity_and_one_batch_sync(self):
        record, events, held = self.cleanup_case()
        self.assertEqual(events, [(3, 38), (3, 39), 'sync'])
        self.assertEqual(held, {})
        self.assertTrue(record['verified'])
        self.assertIn('key_release_brackets', record, 'bulk release has no per-key measurement')
        rows = record['key_release_brackets']
        self.assertEqual([(r['owner_id'], r['intent'], r['keycode']) for r in rows],
                         [('owner-one', 'intent-one', 38), ('owner-one', 'intent-one', 39)])
        self.assertEqual(rows[0]['sync_completed_ns'], rows[1]['sync_completed_ns'])
        self.assertLessEqual(rows[0]['request_started_ns'], rows[1]['request_started_ns'])

    def test_telemetry_clock_failure_does_not_block_bulk_release(self):
        record, events, held = self.cleanup_case(clock_failure=True)
        self.assertEqual(events, [(3, 38), (3, 39), 'sync'])
        self.assertEqual(held, {})
        self.assertTrue(record['verified'])
        self.assertEqual([(r['request_started_ns'], r['sync_completed_ns'])
                          for r in record['key_release_brackets']], [(None, None), (None, None)])

    def test_telemetry_identity_failure_does_not_block_bulk_release(self):
        record, events, held = self.cleanup_case(identity_failure=True)
        self.assertEqual(events, [(3, 38), (3, 39), 'sync'])
        self.assertEqual(held, {})
        self.assertTrue(record['verified'])
        self.assertEqual(record['key_release_brackets'], [])


if __name__ == '__main__':
    unittest.main()
