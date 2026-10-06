"""Read-only socket-scope evidence audit; never starts producer or socket."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "research/concurrency/singleflight_socket_scope_6501_20261003_01a0ff53"


class ArchiveTests(unittest.TestCase):
    def test_complete_manifests_freezes_and_public_derivatives(self):
        for folder, count in ((PACKET, 41), (PACKET / "posthoc-v2", 26)):
            entries = {}
            for line in (folder / "SHA256SUMS").read_text().splitlines():
                digest, name = line.split("  ", 1)
                self.assertNotIn(name, entries)
                entries[name] = digest
                self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest, name)
            self.assertEqual(len(entries), count)
            observed = {
                p.relative_to(folder).as_posix() for p in folder.rglob("*")
                if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts
                and (folder != PACKET or "posthoc-v2" not in p.relative_to(folder).parts)
            }
            self.assertEqual(set(entries), observed)
            freeze = json.loads((folder / "FREEZE.json").read_text())
            for field in ("sha256", "source_sha256", "original_input_sha256"):
                for name, digest in freeze.get(field, {}).items():
                    self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest, name)
            for entry in json.loads((folder / "RETENTION.json").read_text())["redactions"]:
                self.assertEqual(hashlib.sha256((folder / entry["file"]).read_bytes()).hexdigest(), entry["public_sha256"])

    def test_complete_original_raw_receipt(self):
        with tempfile.TemporaryDirectory(prefix="socket-6895-v1-") as directory:
            receipt = Path(directory) / "audit.json"
            child = subprocess.run([sys.executable, "-B", str(PACKET / "audit.py"), str(PACKET / "fixtures.json"), str(PACKET / "run-a01/raw.json"), str(receipt)], capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            self.assertEqual(json.loads(receipt.read_text()), json.loads((PACKET / "run-a01/audit.json").read_text()))

    def test_complete_corrected_receipt_and_fourteen_controls(self):
        with tempfile.TemporaryDirectory(prefix="socket-6895-v2-") as directory:
            receipt = Path(directory) / "audit.json"
            child = subprocess.run([sys.executable, "-B", str(PACKET / "posthoc-v2/audit_v2.py"), "--fixtures", str(PACKET / "fixtures.json"), "--raw", str(PACKET / "run-a01/raw.json"), "--output", str(receipt)], capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            observed = json.loads(receipt.read_text())
            self.assertEqual(observed, json.loads((PACKET / "posthoc-v2/run-01/audit.json").read_text()))
            self.assertEqual(observed["wire_events"], 126)
            self.assertFalse(observed["candidate_replay"])
            self.assertEqual(len(observed["controls"]), 14)
            self.assertTrue(all(c["rejected_for_required_reason"] for c in observed["controls"]))
            self.assertEqual(sum(c["original_disposition"]["accepted"] for c in observed["controls"]), 6)


if __name__ == "__main__":
    unittest.main()
