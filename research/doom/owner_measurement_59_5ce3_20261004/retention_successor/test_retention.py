"""Catch missing attempt reservation, lost failure/timeout, and rerun overwrite."""
import json
from pathlib import Path
import sys
import tempfile
import unittest


class RetentionTests(unittest.TestCase):
    def test_nonzero_child_retains_reserved_attempt_and_raw_stderr(self):
        from retain_attempt import run
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = run([sys.executable, '-c', 'raise ValueError("startup-fault")'], root, 2)
            self.assertEqual(result['disposition'], 'STOP_CHILD_EXIT')
            self.assertEqual(result['exit_code'], 1)
            self.assertIn('startup-fault', (root / 'stderr.txt').read_text())
            self.assertTrue((root / 'ATTEMPT.json').exists())
            self.assertEqual(json.loads((root / 'TERMINAL.json').read_text()), result)

    def test_timeout_retains_terminal_without_invoking_native_input(self):
        from retain_attempt import run
        with tempfile.TemporaryDirectory() as directory:
            result = run([sys.executable, '-c', 'import time; time.sleep(10)'], Path(directory), .1)
            self.assertEqual(result['disposition'], 'STOP_CHILD_TIMEOUT')
            self.assertIsInstance(result['exit_code'], int)

    def test_consumed_output_refuses_before_child_side_effect(self):
        from retain_attempt import run
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run([sys.executable, '-c', 'pass'], root, 2)
            original = (root / 'ATTEMPT.json').read_bytes()
            target = root / 'unexpected'
            with self.assertRaises(FileExistsError):
                run([sys.executable, '-c', 'from pathlib import Path; Path(' + repr(str(target)) + ').touch()'], root, 2)
            self.assertFalse(target.exists())
            self.assertEqual((root / 'ATTEMPT.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
