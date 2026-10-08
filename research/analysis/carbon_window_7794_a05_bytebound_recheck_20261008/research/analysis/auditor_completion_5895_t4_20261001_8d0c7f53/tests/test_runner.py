"""Tests for safe source binding and candidate output ownership."""

import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class CandidateRunnerTests(unittest.TestCase):
    def load(self):
        try:
            return importlib.import_module("run_candidate")
        except ModuleNotFoundError:
            return None

    def test_source_identity_binds_both_git_blob_and_sha256(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 candidate runner must exist")
        data = b"frozen test source\n"
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        digest = hashlib.sha256(data).hexdigest()
        with patch.dict(module.FROZEN, {"fixture": (blob, digest)}):
            self.assertEqual(module.hashes("fixture", data), (blob, digest))
            with self.assertRaises(SystemExit):
                module.hashes("fixture", data + b"changed")

    def test_nonempty_output_directory_is_refused_and_preserved(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 candidate runner must exist")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            output.mkdir()
            marker = output / "owner-data"
            marker.write_bytes(b"preserve")
            with self.assertRaises(SystemExit):
                module.prepare_output(output)
            self.assertEqual(marker.read_bytes(), b"preserve")

    def test_fixture_import_returns_rows_without_changing_fixture_file(self):
        module = self.load()
        self.assertIsNotNone(module, "T4 candidate runner must exist")
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            source = target / "test_audit_formal_x11.py"
            body = "def fixture_rows():\n    return [{'event': 'runner_complete', 'exit_code': 0}]\n"
            source.write_text(body, encoding="utf-8")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(module.load_fixture_rows(target), [{"event": "runner_complete", "exit_code": 0}])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
