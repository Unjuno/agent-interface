import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_audit


class AuditCliControls(unittest.TestCase):
    def test_saved_only_audit_creates_once_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); data = root / 'data'; data.mkdir()
            test_audit.AuditControls().directory(data)
            output = root / 'AUDIT.json'
            command = [sys.executable, '-B', str(Path(__file__).with_name('audit_saved.py')), str(data), str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists(), 'saved-only auditor did not retain AUDIT.json')
            record = json.loads(output.read_text())
            self.assertEqual(record['verdict'], 'VERIFIED_SAVED_PIPE_RECORD')
            self.assertEqual(record['scope'], 'saved-row-and-directory-semantics-only')
            previous = output.read_bytes()
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), previous)
