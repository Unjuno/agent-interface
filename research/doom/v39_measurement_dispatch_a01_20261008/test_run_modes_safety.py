import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_MODES = HERE / "run_modes.py"
VERIFY = HERE / "verify.py"
SPEC = importlib.util.spec_from_file_location("dispatch_runner", RUN_MODES)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def retained_hashes():
    names = json.loads((HERE / "SHA256SUMS.json").read_text(encoding="utf-8"))
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names}


class SafeReplayTests(unittest.TestCase):
    def test_default_temp_root_is_safe_and_unique(self):
        temp_root = Path(os.environ.get("TEST_TEMP_ROOT", tempfile.gettempdir()))
        with tempfile.TemporaryDirectory(prefix="v39-dispatch-default-test-", dir=temp_root) as temp:
            with mock.patch.object(RUNNER.tempfile, "gettempdir", return_value=temp):
                first = RUNNER.output_directory(None)
                second = RUNNER.output_directory(None)
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, Path(temp))
            self.assertEqual(second.parent, Path(temp))
        with mock.patch.object(RUNNER.tempfile, "gettempdir", return_value=str(HERE)):
            with self.assertRaises(SystemExit):
                RUNNER.output_directory(None)

    def test_low_space_refuses_before_creating_output(self):
        with tempfile.TemporaryDirectory(prefix="v39-dispatch-low-space-test-",
                                         dir=Path(os.environ.get("TEST_TEMP_ROOT", tempfile.gettempdir()))) as temp:
            output = Path(temp) / "not-created"
            with mock.patch.object(RUNNER.shutil, "disk_usage", return_value=mock.Mock(free=0)):
                with self.assertRaisesRegex(SystemExit, "insufficient free space"):
                    RUNNER.output_directory(output)
            self.assertFalse(output.exists())

    def test_low_space_system_temp_refuses_before_creating_directory(self):
        with tempfile.TemporaryDirectory(prefix="v39-dispatch-default-low-space-test-",
                                         dir=Path(os.environ.get("TEST_TEMP_ROOT", tempfile.gettempdir()))) as temp:
            with mock.patch.object(RUNNER.tempfile, "gettempdir", return_value=temp), \
                 mock.patch.object(RUNNER.shutil, "disk_usage", return_value=mock.Mock(free=0)):
                with self.assertRaisesRegex(SystemExit, "insufficient free space"):
                    RUNNER.output_directory(None)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_external_new_output_and_refusals_preserve_retained_bundle(self):
        before = retained_hashes()
        temp_root = Path(os.environ.get("TEST_TEMP_ROOT", tempfile.gettempdir()))
        with tempfile.TemporaryDirectory(prefix="v39-dispatch-replay-test-", dir=temp_root) as temp:
            output = Path(temp) / "fresh-results"
            proc = subprocess.run([sys.executable, "-B", str(RUN_MODES), "--output-dir", str(output)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            summary = json.loads(proc.stdout)
            self.assertEqual(Path(summary["results_dir"]), output.resolve())
            verified = subprocess.run([sys.executable, "-B", str(VERIFY), "--results-dir", str(output)],
                                      capture_output=True, text=True, check=False)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertTrue(json.loads(verified.stdout)["verified"])
            after_success = retained_hashes()
            self.assertEqual(before, after_success)

            repeat = subprocess.run([sys.executable, "-B", str(RUN_MODES), "--output-dir", str(output)],
                                    capture_output=True, text=True, check=False)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertIn("refusing existing output directory", repeat.stderr)
            self.assertEqual(before, retained_hashes())

            unsafe = HERE / "must-not-create-rerun-output"
            refusal = subprocess.run([sys.executable, "-B", str(RUN_MODES), "--output-dir", str(unsafe)],
                                     capture_output=True, text=True, check=False)
            self.assertNotEqual(refusal.returncode, 0)
            self.assertFalse(unsafe.exists())
            self.assertEqual(before, retained_hashes())


if __name__ == "__main__":
    unittest.main()
