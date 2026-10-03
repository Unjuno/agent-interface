"""Fresh interpreter must save source STOP before importing missing dependencies."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import ast
import hashlib
from unittest.mock import patch
import runner


class FreshPreflightControl(unittest.TestCase):
    def test_missing_dependencies_before_first_import_save_stop(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); package = root / 'packages' / 'f03'; package.mkdir(parents=True)
            script = package / 'runner.py'
            script.write_bytes(Path(__file__).with_name('runner.py').read_bytes())
            output = root / 'output'
            result = subprocess.run([sys.executable, '-B', str(script), str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertTrue((output / 'SUMMARY.json').is_file(), result.stderr)
            summary = json.loads((output / 'SUMMARY.json').read_text())
            self.assertEqual(summary['verdict'], 'STOP_PREFLIGHT_SOURCE')
            self.assertEqual(summary['error_type'], 'FileNotFoundError')
            self.assertEqual(summary['cases'], [])
            self.assertEqual({p.name for p in output.iterdir()}, {'SUMMARY.json'})

    def test_factory_code_comes_from_hash_pinned_bytes_despite_poisoned_modules(self):
        base = Path(__file__).resolve().parent.parent
        candidate = (base / 'v39_eof_59_f02_20261004_3cbf/candidate.py').read_bytes()
        helper = (base / 'v39_os_pipe_59_f01_20261004_3cbf/probe.py').read_bytes()
        candidate_hash = '2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1'
        helper_hash = '8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0'
        self.assertEqual(hashlib.sha256(candidate).hexdigest(), candidate_hash)
        self.assertEqual(hashlib.sha256(helper).hexdigest(), helper_hash)
        tree = ast.parse(candidate)
        self.assertTrue(any(isinstance(node, ast.ImportFrom) and node.module == 'probe'
                            for node in tree.body))
        # Guard against reverting to a normal cached import when factories load.
        sentinel = type('Poison', (), {'factory': lambda *_: None})
        with patch.dict(sys.modules, {'probe': sentinel}):
            _, loaded = runner.load_factories(candidate, helper)
        self.assertIsNot(loaded, sentinel.factory)
        self.assertEqual(loaded.__code__.co_filename, '<frozen-F02-candidate-bytes>')
        with self.assertRaisesRegex(ValueError, 'candidate source pin'):
            runner.load_factories(candidate + b'\n', helper)
        with self.assertRaisesRegex(ValueError, 'helper source pin'):
            runner.load_factories(candidate, helper + b'\n')
