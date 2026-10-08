"""Removing doom script-directory admission breaks actual sibling imports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class EntryBoundary(unittest.TestCase):
    def test_real_sibling_import_receipt_and_unchanged_main_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            doom = root / 'source/research/doom'
            doom.mkdir(parents=True)
            (doom / 'entry_backend_fixture.py').write_text('class Backend: pass\n')
            (doom / 'session_map01_v12.py').write_text(
                'from entry_backend_fixture import Backend\n'
                'import json,sys\n'
                'def main(): print(json.dumps(sys.argv))\n')
            receipt = root / 'imports.json'
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('session_entry.py')),
                '--source', str(root / 'source'), '--receipt', str(receipt), '--sentinel', 'literal'],
                cwd=root, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [str(doom / 'session_map01_v12.py'), '--sentinel', 'literal'])
            actual = json.loads(receipt.read_text())
            self.assertEqual(actual['backend_module'], 'entry_backend_fixture')
            self.assertEqual([row['path'] for row in actual['loaded']],
                             ['research/doom/entry_backend_fixture.py'])


if __name__ == '__main__':
    unittest.main()
