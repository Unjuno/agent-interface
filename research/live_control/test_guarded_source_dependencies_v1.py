"""Source-provenance regressions only; no GUI, model or frozen allocation."""
import ast
import contextlib
import hashlib
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import guarded_source_dependencies_v1 as subject


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GuardedSourceTests(unittest.TestCase):
    def fixture(self, root):
        for name in (*subject.WRAPPERS, *subject.IMPLEMENTATIONS, subject.HELPER):
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('source fixture: '+name)
        return root/'research/live_control'

    def test_shared_change_changes_record_with_unchanged_wrapper(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(subject, 'ROOT', Path(td)):
            root = Path(td); here = self.fixture(root)
            wrapper = 'scoped_target_handle_v1.py'
            original = {wrapper: sha(here/wrapper)}
            before = subject.complete_guarded_hashes(original, base=here)
            for relative in subject.IMPLEMENTATIONS:
                path = root/relative; previous = path.read_bytes()
                path.write_bytes(previous+b' changed')
                after = subject.complete_guarded_hashes(original, base=here)
                changed = [k for k in before if before[k] != after[k]]
                self.assertEqual(changed, ['../../'+relative])
                self.assertEqual(after[wrapper], original[wrapper])
                path.write_bytes(previous)
            self.assertEqual(original, {wrapper: sha(here/wrapper)})
            self.assertEqual(before[Path(subject.HELPER).name], sha(root/subject.HELPER))

    def test_root_relative_keys_and_equivalent_existing_key_are_preserved(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(subject, 'ROOT', Path(td)):
            root = Path(td); self.fixture(root)
            name = subject.WRAPPERS[0]; alias = './'+subject.IMPLEMENTATIONS[0]
            original = {name: sha(root/name), alias: sha(root/subject.IMPLEMENTATIONS[0])}
            result = subject.complete_guarded_hashes(original, base=root)
            self.assertEqual(result[alias], original[alias])
            self.assertNotIn(subject.IMPLEMENTATIONS[0], result)
            self.assertIn(subject.HELPER, result)
            self.assertEqual(len(result), len(subject.IMPLEMENTATIONS)+2)

    def test_stale_wrapper_conflicting_implementation_and_missing_source_refuse(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(subject, 'ROOT', Path(td)):
            root = Path(td); here = self.fixture(root)
            name = 'scoped_target_handle_v1.py'; good = {name: sha(here/name)}
            with self.assertRaises(ValueError):
                subject.complete_guarded_hashes({name: '0'*64}, base=here)
            conflict = dict(good, **{'../../'+subject.IMPLEMENTATIONS[0]: '0'*64})
            with self.assertRaises(ValueError):
                subject.complete_guarded_hashes(conflict, base=here)
            (root/subject.IMPLEMENTATIONS[0]).unlink()
            with self.assertRaises(FileNotFoundError):
                subject.complete_guarded_hashes(good, base=here)

    def test_unrelated_or_vendored_names_do_not_select_current_implementation(self):
        with tempfile.TemporaryDirectory() as td:
            old = {'scoped_target_handle_v1.py': 'historical'}
            self.assertEqual(subject.complete_guarded_hashes(old, base=Path(td)), old)
            self.assertEqual(subject.complete_guarded_hashes({}, base=Path(td)), {})

    def test_actual_chromium_and_openttd_generators_in_fresh_fixture_directories(self):
        for module_name in ('preregister_chromium_target_handle_pair_v1',
                            'preregister_openttd_target_handle_live_v1'):
            module = importlib.import_module(module_name)
            tree = ast.parse(Path(module.__file__).read_text())
            with self.subTest(module=module_name), tempfile.TemporaryDirectory() as td:
                root=Path(td);here=self.fixture(root)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List):
                        continue
                    name=node.targets[0].id if isinstance(node.targets[0], ast.Name) else ''
                    if name not in ('sources','live','task'):continue
                    for relative in ast.literal_eval(node.value):
                        path=(here.parent if name=='task' else here)/relative
                        path.parent.mkdir(parents=True,exist_ok=True)
                        if not path.exists():path.write_text('fixture dependency '+relative)
                with mock.patch.object(module,'HERE',here), mock.patch.object(subject,'ROOT',root), \
                     contextlib.redirect_stdout(io.StringIO()):
                    with mock.patch.object(module,'OUT',root/'first'):
                        module.main()
                    retained=(root/'first/preregistration.json').read_bytes()
                    initial=json.loads(retained)['sources']
                    (root/subject.IMPLEMENTATIONS[1]).write_text('changed frames')
                    with mock.patch.object(module,'OUT',root/'second'):
                        module.main()
                updated=json.loads((root/'second/preregistration.json').read_bytes())['sources']
                self.assertNotEqual(initial['../../runtime/guarded_x11_v1/frames.py'],
                                    updated['../../runtime/guarded_x11_v1/frames.py'])
                self.assertEqual(initial['scoped_target_handle_v1.py'],updated['scoped_target_handle_v1.py'])
                self.assertEqual((root/'first/preregistration.json').read_bytes(),retained)

    def test_affected_direct_and_inherited_manifest_fields_use_completion(self):
        here=Path(__file__).resolve().parent
        trees={p.name:ast.parse(p.read_text()) for p in here.glob('preregister_*.py')}
        wrapper_names={Path(n).name for n in subject.WRAPPERS}
        affected={name for name,tree in trees.items() if any(
            isinstance(n,ast.Constant) and isinstance(n.value,str) and Path(n.value).name in wrapper_names
            for n in ast.walk(tree))}
        # This successor takes its source names from a frozen predecessor JSON,
        # which intentionally does not change when the current implementation moves.
        affected.add('preregister_chromium_target_handle_model_abba_v2.py')
        while True:
            previous=set(affected)
            for name,tree in trees.items():
                imported={alias.name+'.py' for node in ast.walk(tree) if isinstance(node,ast.Import)
                          for alias in node.names}
                if imported & affected:affected.add(name)
            if previous==affected:break
        self.assertGreaterEqual(len(affected),31)
        probe='probe_scoped_target_handle_archive_v1.py'
        trees[probe]=ast.parse((here/probe).read_text());affected.add(probe)
        for name in sorted(affected):
            with self.subTest(writer=name):
                fields=[]
                for node in ast.walk(trees[name]):
                    if isinstance(node,ast.Dict):
                        fields.extend(v for k,v in zip(node.keys,node.values)
                            if isinstance(k,ast.Constant) and k.value in ('sources','source_sha256')
                            and isinstance(v,(ast.Dict,ast.DictComp,ast.Call))
                            and not (isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute)))
                self.assertTrue(fields)
                for value in fields:
                    self.assertIsInstance(value,ast.Call)
                    self.assertIsInstance(value.func,ast.Name)
                    self.assertEqual(value.func.id,'complete_guarded_hashes')

    def test_existing_runner_source_gates_reject_changed_shared_bytes_before_execution(self):
        here=Path(__file__).resolve().parent
        runners=('run_chromium_target_handle_pair_v1.py',
                 'run_openttd_target_handle_live_v1.py', 'run_integrated_efficiency_live_v1.py')
        with tempfile.TemporaryDirectory() as td, mock.patch.object(subject,'ROOT',Path(td)):
            root=Path(td);fixture=self.fixture(root);name='scoped_target_handle_v1.py'
            hashes=subject.complete_guarded_hashes({name:sha(fixture/name)},base=fixture)
            implementation=root/'runtime/guarded_x11_v1/handles_base.py'
            original=implementation.read_bytes()
            for runner in runners:
                tree=ast.parse((here/runner).read_text())
                main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
                gate=next(n for n in main.body if isinstance(n,ast.For))
                code=compile(ast.Module(body=[gate],type_ignores=[]),runner,'exec')
                env={'plan':{'sources':hashes},'HERE':fixture,'sha':sha,
                     'source_path':lambda name:fixture/name}
                with self.subTest(runner=runner):
                    exec(code,env)
                    implementation.write_bytes(original+b' changed')
                    with self.assertRaises((AssertionError,RuntimeError)):
                        exec(code,env)
                    implementation.write_bytes(original)

    def test_shared_package_relative_imports_are_in_recorded_implementation_set(self):
        root=subject.ROOT; recorded=set(subject.IMPLEMENTATIONS)
        for name in subject.IMPLEMENTATIONS:
            tree=ast.parse((root/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.level==1:
                    self.assertIn('runtime/guarded_x11_v1/'+node.module+'.py',recorded)
