"""Receipt tests: a missing capture module must fail before implementation."""
import importlib.util
import json
import inspect
from pathlib import Path
import sys
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name("host_capture.py")


class HostCaptureTests(unittest.TestCase):
    def capture(self):
        self.assertTrue(MODULE_PATH.is_file(), "once-only receipt capture is missing")
        spec = importlib.util.spec_from_file_location("tested_capture", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.execute

    def test_exact_streams_and_nonzero_exit_are_retained(self):
        execute = self.capture()
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / "out"
            receipt = execute([sys.executable, "-c",
                "import sys;sys.stdout.buffer.write(b'raw\\x00out');"
                "sys.stderr.buffer.write(b'warning\\n');sys.exit(7)"], out)
            self.assertEqual(receipt["exit_code"], 7)
            self.assertEqual((out / "stdout.bin").read_bytes(), b"raw\x00out")
            self.assertEqual((out / "stderr.bin").read_bytes(), b"warning\n")
            self.assertEqual(json.loads((out / "receipt.json").read_bytes()), receipt)
            self.assertEqual(receipt["output_sha256"]["stdout.bin"],
                "95e6efb279ca575818b93b2e52c017bd542ae831d652f8126994813670a8e8da")

    def test_occupied_output_refuses_to_launch(self):
        execute = self.capture()
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / "out"
            out.mkdir()
            (out / "first.txt").write_bytes(b"first")
            with self.assertRaises(FileExistsError):
                execute([sys.executable, "-c", "raise SystemExit(99)"], out)
            self.assertEqual([p.name for p in out.iterdir()], ["first.txt"])

    def test_missing_executable_preserves_launch_error(self):
        execute = self.capture()
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / "out"
            receipt = execute([str(Path(scratch) / "missing-executable")], out)
            self.assertIsNone(receipt["exit_code"])
            self.assertTrue(receipt["launch_error"])
            self.assertTrue((out / "attempt.json").is_file())
            self.assertEqual((out / "stdout.bin").read_bytes(), b"")

    def test_freeze_binding_is_part_of_attempt_and_receipt(self):
        execute = self.capture()
        self.assertIn("binding", inspect.signature(execute).parameters,
                      "formal source binding is missing")
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / "out"
            binding = {"source_commit": "literal-test-source",
                       "freeze_sha256": "literal-test-freeze"}
            receipt = execute([sys.executable, "-c", "pass"], out, binding=binding)
            self.assertEqual(receipt["binding"], binding)
            self.assertEqual(json.loads((out / "attempt.json").read_bytes())["binding"], binding)

    def test_changed_frozen_source_is_rejected(self):
        execute = self.capture()
        module = sys.modules.get(execute.__module__)
        # The importlib test loader need not register modules: use globals.
        validate = execute.__globals__.get("validate_sources")
        self.assertIsNotNone(validate, "source hash gate is missing")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "source.py").write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError, "STOP_SOURCE_HASH_MISMATCH:source.py"):
                validate(root, {"source.py":
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"})


if __name__ == "__main__":
    unittest.main()
