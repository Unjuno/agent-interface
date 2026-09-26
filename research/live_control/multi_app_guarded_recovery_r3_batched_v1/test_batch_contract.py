from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import run_batches


class DurableBatchContractTest(unittest.TestCase):
    def test_atomic_write_and_no_replace(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "session.json"
            run_batches.atomic_write(path, b"first\n", replace=False)
            self.assertEqual(path.read_bytes(), b"first\n")
            with self.assertRaises(FileExistsError):
                run_batches.atomic_write(path, b"second\n", replace=False)
            self.assertEqual(path.read_bytes(), b"first\n")

    def test_canonical_json_is_stable(self):
        value = {"z": 1, "a": [True, None]}
        self.assertEqual(run_batches.canonical(value), b'{"a":[true,null],"z":1}\n')
        self.assertEqual(hashlib.sha256(run_batches.canonical(value)).hexdigest(), hashlib.sha256(run_batches.canonical(value)).hexdigest())

    def test_source_bundle_extraction_is_hash_bound(self):
        with tempfile.TemporaryDirectory() as root:
            destination, files = run_batches.load_sources(Path(root) / "source")
            self.assertEqual(set(files), {"CONSTRUCTION_HISTORY.md", "CONSTRUCTION_RESULT.json", "PLAN.md", "audit.py", "common.py", "construction.py", "formal.py"})
            self.assertEqual(len((destination / "common.py").read_bytes()), 10791)


if __name__ == "__main__":
    unittest.main()
