"""Verify that each retained XTest manifest describes committed bytes."""
import hashlib
import json
from pathlib import Path
import unittest


EVIDENCE = Path(__file__).resolve().parent / "evidence"


class EvidenceManifestTests(unittest.TestCase):
    def test_each_attempt_matches_its_manifest_exactly(self):
        for attempt in range(1, 5):
            with self.subTest(attempt=attempt):
                root = EVIDENCE / f"construction-xtest-{attempt:02d}"
                manifest = json.loads((root / "manifest.json").read_text())
                declared = {entry["path"]: entry for entry in manifest["files"]}
                actual = {
                    path.name
                    for path in root.iterdir()
                    if path.is_file() and path.name != "manifest.json"
                }
                self.assertEqual(actual, set(declared))
                for relative, entry in declared.items():
                    payload = (root / relative).read_bytes()
                    self.assertEqual(len(payload), entry["bytes"], relative)
                    self.assertEqual(
                        hashlib.sha256(payload).hexdigest(),
                        entry["sha256"],
                        relative,
                    )
