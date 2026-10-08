"""Construction tests for one-shot, source-frozen formal runners."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runner_utils import verify_manifest, write_json_once


class FrozenRunnerTests(unittest.TestCase):
    def test_candidate_manifest_covers_public_inputs_without_auditor_truth(self):
        package = Path(__file__).parent
        manifest = json.loads((package / "CANDIDATE_FREEZE.json").read_text(encoding="utf-8"))

        verify_manifest(package, manifest)

        self.assertNotIn("truth.json", manifest["files"])
        self.assertNotIn("auditor.py", manifest["files"])

    def test_manifest_verification_accepts_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "candidate.py"
            target.write_bytes(b"frozen source\n")
            manifest = {"files": {"candidate.py": hashlib.sha256(target.read_bytes()).hexdigest()}}

            verify_manifest(root, manifest)

    def test_manifest_verification_rejects_tampered_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "candidate.py"
            target.write_bytes(b"tampered source\n")
            manifest = {"files": {"candidate.py": hashlib.sha256(b"frozen source\n").hexdigest()}}

            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_manifest(root, manifest)

    def test_formal_output_uses_exclusive_creation_and_preserves_first_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "candidate_raw.json"
            payload = {"status": "first"}

            write_json_once(target, payload)
            first_bytes = target.read_bytes()
            with self.assertRaises(FileExistsError):
                write_json_once(target, {"status": "replacement"})

            self.assertEqual(json.loads(first_bytes), payload)
            self.assertEqual(target.read_bytes(), first_bytes)


if __name__ == "__main__":
    unittest.main()
