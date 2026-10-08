"""Regression tests for immutable replay output; the candidate is never invoked."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).parent


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, BASE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("a04_run_modes", "run_modes.py")
VERIFIER = load_module("a04_verify", "verify.py")


class ReplayOutputSafetyTests(unittest.TestCase):
    def test_existing_directory_is_refused_without_modifying_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            output = Path(temp) / "existing"
            output.mkdir()
            raw = output / "normal.stdout.txt"
            raw.write_bytes(b"first retained outcome")
            with self.assertRaisesRegex(ValueError, "already exists"):
                RUNNER.prepare_output_dir(output, package)
            self.assertEqual(raw.read_bytes(), b"first retained outcome")

    def test_main_refuses_before_starting_candidate_and_preserves_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            output = Path(temp) / "existing"
            output.mkdir()
            raw = output / "normal.stdout.txt"
            raw.write_bytes(b"first retained outcome")
            with patch.object(RUNNER.subprocess, "run") as candidate:
                with self.assertRaises(SystemExit):
                    RUNNER.main(["--output-dir", str(output)])
            candidate.assert_not_called()
            self.assertEqual(raw.read_bytes(), b"first retained outcome")

    def test_output_inside_package_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                RUNNER.prepare_output_dir(package / "rerun", package)
            self.assertFalse((package / "rerun").exists())

    def test_fresh_external_output_directory_is_created(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            output = RUNNER.prepare_output_dir(Path(temp) / "fresh-run", package)
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])

    def test_package_itself_is_refused_and_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            retained = package / "normal.stdout.txt"
            retained.write_bytes(b"do not overwrite")
            with self.assertRaisesRegex(ValueError, "outside"):
                RUNNER.prepare_output_dir(package, package)
            self.assertEqual(retained.read_bytes(), b"do not overwrite")


class VerificationPathTests(unittest.TestCase):
    def test_external_existing_results_directory_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "results"
            output.mkdir()
            self.assertEqual(VERIFIER.select_results_dir(output), output.resolve())

    def test_results_inside_retained_package_are_refused(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            VERIFIER.select_results_dir(BASE / "rerun")

    def test_missing_external_results_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "does not exist"):
                VERIFIER.select_results_dir(Path(temp) / "missing")

    def test_omitted_results_directory_selects_committed_package(self):
        self.assertEqual(VERIFIER.select_results_dir(None), VERIFIER.HERE)


if __name__ == "__main__":
    unittest.main()
