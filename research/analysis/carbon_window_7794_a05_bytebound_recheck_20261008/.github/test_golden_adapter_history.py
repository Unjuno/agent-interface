"""Offline controls for historical-source/current-evidence separation."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STUDY = Path('research/integration/golden_v3_adapter_p2_rebase_2360_v1')
parser = argparse.ArgumentParser()
parser.add_argument('--historical-root', type=Path, default=ROOT / '.golden-p2-history')
args, remainder = parser.parse_known_args()
SOURCE = args.historical_root.resolve()


class HistoryIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='golden-history-control-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.historical = self.root / 'historical'
        self.current = self.root / 'current'
        for relative in ('runtime', 'research'):
            shutil.copytree(SOURCE / relative, self.historical / relative,
                            ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / STUDY, self.current / STUDY)

    def check(self, expected=None, optimized=False):
        process = subprocess.run([sys.executable, *(['-O'] if optimized else []), '-S', '-B',
            str(ROOT / '.github/check_golden_adapter_history.py'),
            '--historical-root', str(self.historical), '--current-root', str(self.current)],
            capture_output=True, text=True, timeout=5)
        if expected is None:
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result['historical_files_verified'], 9)
            self.assertEqual(result['current_frozen_files_preserved'], 4)
            self.assertEqual(result['scope'], 'source_identity_only')
        else:
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(expected, process.stderr)

    def test_exact_history_and_current_evidence_pass(self):
        self.check()

    def test_each_current_frozen_file_is_protected(self):
        for name in ('README.md', 'SOURCE_MANIFEST.json', 'audit.py', 'test_adapter.py'):
            with self.subTest(name=name):
                path = self.current / STUDY / name
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                self.check('CURRENT_FROZEN_CHANGED')
                path.write_bytes(original)

    def test_current_adapter_is_not_mistaken_for_historical(self):
        path = self.current / 'runtime/cli_v1/golden_v3.py'
        path.parent.mkdir(parents=True)
        path.write_text('current adapter is checked by separate semantic tests\n')
        self.check()

    def test_historical_adapter_tamper_rejects(self):
        path = self.historical / 'runtime/cli_v1/golden_v3.py'
        path.write_bytes(path.read_bytes() + b'\n')
        self.check('HISTORICAL_BLOB_CHANGED')

    def test_historical_import_dependency_tamper_rejects(self):
        path = self.historical / 'runtime/cli_v1/api.py'
        path.write_bytes(path.read_bytes() + b'\n')
        self.check('HISTORICAL_BLOB_CHANGED')

    def test_shared_manifest_rewrite_does_not_repin_history(self):
        for root in (self.historical, self.current):
            (root / STUDY / 'SOURCE_MANIFEST.json').write_text('{}\n')
        self.check('HISTORICAL_BLOB_CHANGED')

    def test_missing_dependency_rejects(self):
        (self.historical / 'runtime/selector_v1/selector.py').unlink()
        self.check('SOURCE_NOT_REGULAR')

    def test_symlink_rejects(self):
        path = self.historical / STUDY / 'audit.py'
        target = self.root / 'copied_audit.py'
        path.rename(target)
        path.symlink_to(target)
        self.check('SOURCE_NOT_REGULAR')

    def test_unexpected_python_import_source_rejects(self):
        (self.historical / 'runtime/__init__.py').write_text('# unexpected package code\n')
        self.check('UNEXPECTED_HISTORICAL_SOURCE')

    def test_optimized_python_preserves_refusal(self):
        self.check(optimized=True)
        path = self.current / STUDY / 'audit.py'
        path.write_bytes(path.read_bytes() + b'\n')
        self.check('CURRENT_FROZEN_CHANGED', optimized=True)

    def test_oversized_snapshot_rejects(self):
        (self.historical / 'runtime/cli_v1/api.py').write_bytes(b' ' * 131073)
        self.check('SOURCE_SIZE_LIMIT')


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remainder])
