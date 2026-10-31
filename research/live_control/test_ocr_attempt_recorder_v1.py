import hashlib
import subprocess
import unittest

from research.live_control.ocr_attempt_recorder_v1 import OcrAttemptRecorder


class OcrAttemptRecorderTests(unittest.TestCase):
    def test_success_records_exact_command_and_hashes_without_raw_content(self):
        seen = []
        def runner(command, **kwargs):
            seen.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, b"result", b"warning")
        recorder = OcrAttemptRecorder(runner=runner)
        command = ["tesseract", "stdin", "stdout", "--psm", "7"]
        result = recorder(command, input=b"image", capture_output=True, timeout=1, check=False)
        command[-1] = "changed"
        row = recorder.records[0]
        self.assertEqual(result.stdout, b"result")
        self.assertEqual(row["command"], ["tesseract", "stdin", "stdout", "--psm", "7"])
        self.assertEqual(row["input_sha256"], hashlib.sha256(b"image").hexdigest())
        self.assertEqual(row["stdout_sha256"], hashlib.sha256(b"result").hexdigest())
        self.assertEqual(row["stderr_sha256"], hashlib.sha256(b"warning").hexdigest())
        self.assertEqual(row["status"], "returned")
        self.assertGreaterEqual(row["ended_ns"], row["started_ns"])
        self.assertNotIn("image", row.values())
        self.assertEqual(seen[0][1]["timeout"], 1)

    def test_timeout_is_recorded_and_reraised_without_retry(self):
        calls = []
        def runner(command, **kwargs):
            calls.append(command)
            raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"partial")
        recorder = OcrAttemptRecorder(runner=runner)
        with self.assertRaises(subprocess.TimeoutExpired):
            recorder(["tesseract"], input=b"x", capture_output=True, timeout=0.5, check=False)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(recorder.records), 1)
        self.assertEqual(recorder.records[0]["status"], "timeout")
        self.assertEqual(recorder.records[0]["stdout_sha256"], hashlib.sha256(b"partial").hexdigest())

    def test_os_error_is_recorded_and_reraised_without_retry(self):
        def runner(command, **kwargs):
            raise FileNotFoundError("unavailable")
        recorder = OcrAttemptRecorder(runner=runner)
        with self.assertRaises(FileNotFoundError):
            recorder(["tesseract"], input=b"x", capture_output=True, timeout=1, check=False)
        self.assertEqual(recorder.records[0]["status"], "error")
        self.assertEqual(recorder.records[0]["error_type"], "FileNotFoundError")
        self.assertIsNone(recorder.records[0]["stdout_sha256"])


if __name__ == "__main__":
    unittest.main()
