"""Contract tests for publication-closure auditing."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit import audit


class PublicationClosureAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.bundle = Path(self.temp.name)
        self.evidence = self.bundle / "evidence"
        self.evidence.mkdir()
        self.write_file("evidence/a.json", b'{"a":1}\n')
        self.write_file("evidence/nested/b.bin", b"\x00\x01\x02")
        self.write_manifest([
            self.row("evidence/a.json", b'{"a":1}\n'),
            self.row("evidence/nested/b.bin", b"\x00\x01\x02"),
        ])

    def tearDown(self):
        self.temp.cleanup()

    def write_file(self, name, content):
        path = self.bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    @staticmethod
    def row(name, content):
        return {"path": name, "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest()}

    def write_manifest(self, rows):
        (self.evidence / "manifest.json").write_text(
            json.dumps({
                "schema": "agent-interface/issue-3370-delivery-pair-manifest-v1",
                "evidence_root": "evidence/",
                "files": rows,
            }), encoding="utf-8")

    def test_complete_tree_passes(self):
        result = audit(self.bundle)
        self.assertEqual(result["result"], "PASS_PUBLICATION_CLOSED")
        self.assertEqual(result["present_and_matching"], 2)

    def test_missing_manifest_file_is_gap(self):
        (self.evidence / "nested/b.bin").unlink()
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_PUBLICATION_GAP")
        self.assertEqual(result["missing"], ["evidence/nested/b.bin"])

    def test_changed_bytes_are_drift(self):
        self.write_file("evidence/a.json", b'{"a":2}\n')
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_PUBLICATION_DRIFT")
        self.assertEqual(result["mismatched"][0]["path"], "evidence/a.json")

    def test_unlisted_file_is_held(self):
        self.write_file("evidence/extra.txt", b"extra")
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_UNLISTED_FILES")
        self.assertEqual(result["unlisted"], ["evidence/extra.txt"])

    def test_parent_traversal_is_rejected(self):
        self.write_manifest([self.row("evidence/../outside", b"x")])
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_MANIFEST_INVALID")

    def test_duplicate_manifest_path_is_rejected(self):
        row = self.row("evidence/a.json", b'{"a":1}\n')
        self.write_manifest([row, row])
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_MANIFEST_INVALID")

    def test_unregistered_manifest_schema_is_rejected(self):
        self.write_manifest([self.row("evidence/a.json", b'{"a":1}\n')])
        manifest = json.loads((self.evidence / "manifest.json").read_text())
        manifest["schema"] = "unknown-v99"
        (self.evidence / "manifest.json").write_text(json.dumps(manifest))
        result = audit(self.bundle)
        self.assertEqual(result["result"], "HOLD_MANIFEST_INVALID")


if __name__ == "__main__":
    unittest.main()
