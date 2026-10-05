"""E05 must pin its cleanup helper as well as the inherited execution closure."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from audit import audit


class E05Closure(unittest.TestCase):
    def test_accepts_complete_cleanup_pinned_partial_stop_fixture(self):
        predecessor = Path(__file__).resolve().parent.parent / 'v39_native_fault_59_e03_20261004_3cbf'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'root'; shutil.copytree(predecessor, root)
            freeze = json.loads((root / 'FREEZE.json').read_text())
            freeze['allocation'] = 'v39-native-fault-e05-3cbf-20261004'
            (root / 'FREEZE.json').write_text(json.dumps(freeze))
            for name in ('cleanup.py', 'partial_stop.py'):
                shutil.copyfile(Path(__file__).with_name(name), root / name)
            names = ['runner.py', 'gate.py', 'audit.py', 'session_entry.py', 'PROTOCOL.md',
                     'FREEZE.json', 'SOURCE_PINS.sha256', 'source-closure.tar.gz', 'COMMANDS.md',
                     'partial_stop.py', 'cleanup.py']
            (root / 'EXECUTION_PINS.sha256').write_text(''.join(
                hashlib.sha256((root / name).read_bytes()).hexdigest() + '  ' + name + '\n' for name in names))
            for directory in ('native', 'export'):
                path = root / f'raw/{directory}/RUNTIME.json'
                runtime = json.loads(path.read_text()); runtime['freeze'] = freeze; runtime['execution_pins'] = 11
                path.write_text(json.dumps(runtime))
            try:
                result = audit(root, root / 'raw/native')
            except Exception as exc:
                self.fail('complete E05 cleanup closure rejected: ' + repr(exc))
            self.assertIs(result['scientific_pass'], False)
            self.assertEqual(result['cell_dispositions'], ['VERIFIED_PARTIAL_STARTUP_STOP'])


if __name__ == '__main__':
    unittest.main()
