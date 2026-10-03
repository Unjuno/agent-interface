"""Fresh interpreter must save source STOP before importing missing dependencies."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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
