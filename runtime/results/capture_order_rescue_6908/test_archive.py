"""Retained #6908 audit: reproduce original FAIL and additive reconciliation."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "research/integration/compiled_observation_order_57_20261003_01a0ff33"


class ArchiveTests(unittest.TestCase):
    def test_complete_public_manifest(self):
        entries = {}
        for line in (PACKET / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(len(entries), 67)
        self.assertEqual(set(entries), {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts
        })
        for entry in json.loads((PACKET / "PUBLICATION_PROJECTION.json").read_bytes())["records"]:
            self.assertEqual(hashlib.sha256((PACKET / entry["file"]).read_bytes()).hexdigest(), entry["public_sha256"])

    def test_original_fail_and_supplement_on_complete_raw(self):
        # A private copy also prevents the old auditor from creating any witness
        # in retained evidence if its historical existence check ever changes.
        with tempfile.TemporaryDirectory(prefix="capture-6908-review-") as directory:
            copied = Path(directory) / "packet"
            shutil.copytree(PACKET, copied)
            for script, exit_code, saved in (("audit.py", 1, "audit.stdout.txt"), ("audit_v2.py", 0, "audit-v2.stdout.txt")):
                child = subprocess.run([sys.executable, "-B", str(copied / script)], cwd=copied, capture_output=True, text=True)
                self.assertEqual(child.returncode, exit_code, child.stdout + child.stderr)
                observed = json.loads(child.stdout)
                self.assertEqual(observed, json.loads((PACKET / saved).read_bytes()))
                self.assertEqual(observed["errors"], [])
                self.assertEqual(observed["counts"]["baseline"]["rows"], 33)
                self.assertEqual(observed["counts"]["candidate"]["rows"], 33)
                if script == "audit.py":
                    self.assertEqual(observed["disposition"], "FAIL_ORDER_GUARD_ENGINEERING_SCOPED")
                    self.assertTrue(all(c["rejected"] for c in observed["controls"]))
                else:
                    self.assertEqual(observed["disposition"], "RECONCILED_RAW_ONLY_SUPPLEMENT")
                    self.assertEqual(observed["mutation_controls_rejected"], 8)
                    self.assertEqual(observed["candidate_replays"], 0)


if __name__ == "__main__":
    unittest.main()
