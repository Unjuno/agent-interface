"""Exercise actual child/file boundaries, with only wait interruption injected."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import capture_run


class CaptureTests(unittest.TestCase):
    def call(self, output, command, timeout=10):
        argv = ["capture_run.py", "--output", str(output), "--purpose", "pure-capture-fixture",
                "--timeout", str(timeout), "--", *command]
        with patch.object(sys, "argv", argv):
            return capture_run.main()

    def test_interrupted_wait_retains_actual_child_streams_and_attempt(self):
        original_wait = subprocess.Popen.wait
        interrupted = False

        def wait_then_interrupt(process, *args, **kwargs):
            nonlocal interrupted
            result = original_wait(process, *args, **kwargs)
            if not interrupted:
                interrupted = True
                raise KeyboardInterrupt("controlled interruption after child completed")
            return result

        with tempfile.TemporaryDirectory(prefix="a01-capture-") as temp:
            output = Path(temp) / "attempt"
            command = [sys.executable, "-B", "-c",
                       "import sys; print('child-out', flush=True); print('child-err', file=sys.stderr, flush=True)"]
            with patch.object(subprocess.Popen, "wait", wait_then_interrupt):
                code = self.call(output, command)
            self.assertEqual(code, 130)
            self.assertIn(b"child-out", (output / "stdout.txt").read_bytes())
            self.assertIn(b"child-err", (output / "stderr.txt").read_bytes())
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertTrue(receipt["interrupted"])
            self.assertEqual(receipt["retries"], 0)
            self.assertEqual(receipt["attempt_state"], "INTERRUPTED")
            self.assertIsNotNone(receipt["pid"])

    def test_attempt_is_recorded_before_launch_and_nonzero_exit_preserved(self):
        original_popen = subprocess.Popen
        with tempfile.TemporaryDirectory(prefix="a01-capture-") as temp:
            output = Path(temp) / "attempt"

            def check_then_launch(*args, **kwargs):
                receipt = json.loads((output / "receipt.json").read_text())
                self.assertEqual(receipt["attempt_state"], "ATTEMPT_STARTED")
                self.assertEqual((output / "stdout.txt").read_bytes(), b"")
                self.assertEqual((output / "stderr.txt").read_bytes(), b"")
                return original_popen(*args, **kwargs)

            with patch.object(subprocess, "Popen", check_then_launch):
                code = self.call(output, [sys.executable, "-B", "-c", "raise SystemExit(7)"])
            self.assertEqual(code, 7)
            self.assertEqual(json.loads((output / "receipt.json").read_text())["exit_code"], 7)

    def test_launch_failure_is_terminal_and_attempt_directory_cannot_be_reused(self):
        with tempfile.TemporaryDirectory(prefix="a01-capture-") as temp:
            output = Path(temp) / "attempt"
            self.assertEqual(self.call(output, ["a01-no-such-program-61f15"]), 127)
            receipt_before = (output / "receipt.json").read_bytes()
            self.assertEqual(json.loads(receipt_before)["retries"], 0)
            with self.assertRaises(FileExistsError):
                self.call(output, [sys.executable, "-B", "-c", "raise SystemExit(0)"])
            self.assertEqual((output / "receipt.json").read_bytes(), receipt_before)

    def test_timeout_keeps_output_and_records_no_retry(self):
        with tempfile.TemporaryDirectory(prefix="a01-capture-") as temp:
            output = Path(temp) / "attempt"
            command = [sys.executable, "-B", "-c", "import time; print('before-timeout', flush=True); time.sleep(5)"]
            self.assertEqual(self.call(output, command, timeout=1), 124)
            self.assertIn(b"before-timeout", (output / "stdout.txt").read_bytes())
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertTrue(receipt["timed_out"])
            self.assertEqual(receipt["retries"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
