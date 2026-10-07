import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

class ProcessTests(unittest.TestCase):
    def test_exact_streams_input_clock_and_once_only(self):
        self.assertIsNotNone(importlib.util.find_spec('model_runner'),'model process recorder missing')
        from model_runner import run_command
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'once'
            result=run_command([sys.executable,'-c','import sys; print(sys.stdin.read(),end=""); print("diagnostic",file=sys.stderr)'],b'literal-prompt\n',output,3)
            self.assertEqual((output/'stdout.bin').read_bytes(),b'literal-prompt\r\n' if sys.platform=='win32' else b'literal-prompt\n')
            self.assertEqual((output/'stderr.bin').read_bytes(),b'diagnostic\r\n' if sys.platform=='win32' else b'diagnostic\n')
            self.assertEqual(result['exit_code'],0)
            self.assertFalse(result['timed_out'])
            with self.assertRaises(FileExistsError):run_command([sys.executable,'-c','print("second")'],b'',output,3)

    def test_timeout_preserves_partial_output_without_retry(self):
        self.assertIsNotNone(importlib.util.find_spec('model_runner'),'model process recorder missing')
        from model_runner import run_command
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'first'
            result=run_command([sys.executable,'-c','import time; print("partial",flush=True); time.sleep(4)'],b'',output,.2)
            self.assertTrue(result['timed_out'])
            self.assertIn(b'partial',(output/'stdout.bin').read_bytes())

if __name__=='__main__':unittest.main()
