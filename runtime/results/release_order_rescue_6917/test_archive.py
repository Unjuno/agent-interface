"""Preserve integrity PASS separately from modeled identifiability FAIL."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "research/integration/release_order_observability_57_20261003_5156"


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest(self):
        entries = {}
        for line in (PACKET / "SHA256SUMS.txt").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(len(entries), 40)
        self.assertEqual(set(entries), {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "SHA256SUMS.txt" and "__pycache__" not in p.parts
        })

    def test_entire_raw_audit_preserves_model_fail_and_twelve_controls(self):
        with tempfile.TemporaryDirectory(prefix="release-6917-audit-") as directory:
            receipt = Path(directory) / "audit.json"
            child = subprocess.run([sys.executable, "-B", str(PACKET / "audit.py"), str(PACKET / "run01/raw.json"), str(receipt)], capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            observed = json.loads(receipt.read_bytes())
            self.assertEqual(observed, json.loads((PACKET / "run01/audit.json").read_bytes()))
            self.assertEqual(observed["integrity"], "PASS")
            self.assertEqual(observed["model_decision"], "FAIL_TERMINAL_RELEASE_IDENTIFIABILITY")
            self.assertEqual(observed["rows"], 36)
            self.assertEqual(len(observed["mixed_full_projection_classes"]), 6)
            self.assertEqual(len(observed["corruption_controls"]), 12)
            self.assertTrue(all(c["refused"] for c in observed["corruption_controls"]))

    def test_original_git_readback_public_scope_without_private_capture(self):
        with tempfile.TemporaryDirectory(prefix="release-6917-readback-") as directory:
            receipt = Path(directory) / "readback.json"
            child = subprocess.run([sys.executable, "-B", str(PACKET / "readback_checks.py"), "--repo", str(ROOT), "--output", str(receipt)], capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            observed = json.loads(receipt.read_bytes())
            historical = json.loads((PACKET / "run01/readback.json").read_bytes())
            self.assertEqual(observed["original_capture_receipts_and_stream_pairs"], 0)
            self.assertEqual(historical["original_capture_receipts_and_stream_pairs"], 3)
            # Author private captures are unavailable, explicitly not verified.
            historical["original_capture_receipts_and_stream_pairs"] = 0
            for key in ("start_utc", "end_utc"):
                observed.pop(key)
                historical.pop(key)
            self.assertEqual(observed, historical)
            self.assertEqual(observed["frozen_inputs_working_and_committed"], 18)
            self.assertEqual(sum(g["git_byte_matches"] for g in observed["source_groups"]), 8)
            self.assertEqual(observed["public_stream_pairs"], 3)


if __name__ == "__main__":
    unittest.main()
