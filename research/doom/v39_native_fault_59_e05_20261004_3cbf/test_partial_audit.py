"""Full saved-audit entry must distinguish partial STOP from missing evidence."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from audit import audit


PREDECESSOR = Path(__file__).resolve().parent.parent / 'v39_native_fault_59_e03_20261004_3cbf'


class PartialAuditEntry(unittest.TestCase):
    def test_rejects_unlisted_later_cell(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / 'record'
            shutil.copytree(PREDECESSOR / 'raw/native', record)
            (record / 'candidate_fault').mkdir()
            with self.assertRaisesRegex(ValueError, 'saved cell set'):
                audit(PREDECESSOR, record)

    def test_rejects_export_byte_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / 'record'
            shutil.copytree(PREDECESSOR / 'raw/native', record)
            (record / 'extra.txt').write_text('unexported evidence')
            with self.assertRaisesRegex(ValueError, 'independent export equality'):
                audit(PREDECESSOR, record)

    def test_rejects_incomplete_execution_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'root'
            shutil.copytree(PREDECESSOR, root)
            pins = root / 'EXECUTION_PINS.sha256'
            pins.write_text(pins.read_text().splitlines()[0] + '\n')
            with self.assertRaisesRegex(ValueError, 'execution closure'):
                audit(root, root / 'raw/native')

    def test_cli_emits_valid_json_stop_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'result.json'
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('audit.py')),
                '--root', str(PREDECESSOR), '--record', str(PREDECESSOR / 'raw/native'),
                '--out', str(output)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            try:
                decoded = json.loads(output.read_text())
            except ValueError as exc:
                self.fail('CLI output is not parseable saved JSON: ' + repr(exc))
            self.assertIs(decoded['scientific_pass'], False)

    def test_saved_partial_stop_returns_stop_not_scientific_pass(self):
        try:
            result = audit(PREDECESSOR, PREDECESSOR / 'raw/native')
        except Exception as exc:
            self.fail('saved-only audit did not handle retained partial STOP: ' + repr(exc))
        self.assertEqual(result['native_verdict'], 'STOP_NATIVE_GATE')
        self.assertIs(result['scientific_pass'], False)
        self.assertEqual(result['cell_dispositions'], ['VERIFIED_PARTIAL_STARTUP_STOP'])

    def test_refuses_later_cells_after_partial_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / 'record'
            shutil.copytree(PREDECESSOR / 'raw/native', record)
            summary = json.loads((record / 'SUMMARY.json').read_text())
            summary['cases'] = ['original_fault', 'candidate_fault']; summary['cells'] = 2
            (record / 'SUMMARY.json').write_text(json.dumps(summary))
            with self.assertRaises(Exception) as caught:
                audit(PREDECESSOR, record)
            self.assertIsInstance(caught.exception, ValueError)

    def test_refuses_corrupt_partial_release_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / 'record'
            shutil.copytree(PREDECESSOR / 'raw/native', record)
            result = record / 'original_fault/RESULT.json'
            row = json.loads(result.read_text()); row['release_gate'] = 0
            result.write_text(json.dumps(row))
            with self.assertRaises(Exception) as caught:
                audit(PREDECESSOR, record)
            self.assertIsInstance(caught.exception, ValueError)


if __name__ == '__main__':
    unittest.main()
