import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_manifest import verify


class CustodyManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        (self.raw / "event.jsonl").write_bytes(b"{}\n")
        self.summary = self.root / "summary.json"
        summary = {"allocation": "a15", "source_main_sha": "abc",
                   "experiment_tree_commit": "def"}
        self.summary.write_text(json.dumps(summary), encoding="utf-8")
        self.manifest = self.root / "manifest.jsonl"
        self.readback = self.root / "readback.json"
        self.write_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def write_manifest(self, rows=None):
        data = (rows if rows is not None else [{
            "path": "event.jsonl", "bytes": 3,
            "sha256": hashlib.sha256(b"{}\n").hexdigest()}])
        payload = b"".join((json.dumps(row, sort_keys=True) + "\n").encode()
                           for row in data)
        self.manifest.write_bytes(payload)
        summary_bytes = self.summary.read_bytes()
        readback = {"manifest_sha256": hashlib.sha256(payload).hexdigest(),
                    "manifest_entries": len(data), "manifest_total_bytes": 3,
                    "public_summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
                    "allocation": "a15", "source_main_sha": "abc",
                    "experiment_tree_commit": "def", "run_record_sha256": {}}
        self.readback.write_text(json.dumps(readback), encoding="utf-8")

    def test_complete_manifest_and_public_summary_pass(self):
        result = verify(self.raw, self.manifest, self.readback, self.summary)
        self.assertEqual(result["status"], "PASS_A15_RAW_CUSTODY")
        self.assertEqual(result["entries"], 1)

    def test_modified_raw_bytes_fail(self):
        (self.raw / "event.jsonl").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "manifest content mismatch"):
            verify(self.raw, self.manifest, self.readback, self.summary)

    def test_path_traversal_fails(self):
        self.write_manifest([{"path": "../outside", "bytes": 3,
                              "sha256": hashlib.sha256(b"{}\n").hexdigest()}])
        with self.assertRaisesRegex(ValueError, "unsafe relative path"):
            verify(self.raw, self.manifest, self.readback, self.summary)

    def test_unlisted_file_fails_completeness_check(self):
        (self.raw / "extra.txt").write_text("extra", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "complete raw root"):
            verify(self.raw, self.manifest, self.readback, self.summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
