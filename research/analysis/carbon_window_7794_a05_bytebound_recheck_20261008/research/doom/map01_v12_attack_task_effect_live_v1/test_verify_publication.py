import json
import shutil
import tempfile
import unittest
from pathlib import Path

from verify_publication import verify

ROOT = Path(__file__).resolve().parent


class PublicationIntegrityTests(unittest.TestCase):
    def test_corrected_committed_package(self):
        self.assertEqual(verify(ROOT)["errors"], [])

    def test_rejects_wrong_result_blob_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "study"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
            path = target / "PUBLICATION.json"
            publication = json.loads(path.read_text())
            publication["result_summary_sha256"] = "0" * 64
            path.write_text(json.dumps(publication))
            self.assertIn("publication:result_summary_sha256", verify(target)["errors"])

    def test_rejects_wrong_archived_audit_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "study"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
            path = target / "SHA256SUMS.source"
            text = path.read_text().replace("4055a97229681f3f2cb41998424c775b1ed1181da2200f28df39307212e3d714", "0" * 64)
            path.write_text(text)
            self.assertIn("sidecar:audit.py", verify(target)["errors"])

    def test_rejects_wrong_recheck_manifest_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "study"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
            path = target / "INTEGRITY_RECHECK_SHA256SUMS"
            lines = path.read_text().splitlines()
            lines = [("0" * 64 + "  verify_publication.py") if line.endswith("  verify_publication.py") else line for line in lines]
            path.write_text("\n".join(lines) + "\n")
            self.assertIn("integrity_manifest:verify_publication.py", verify(target)["errors"])

    def test_rejects_missing_external_frozen_source(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "study"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
            (target / "PLAN.md").unlink()
            errors = verify(target)["errors"]
            self.assertIn("freeze_external_missing:PLAN.md", errors)

    def test_rejects_tampered_success_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "study"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
            path = target / "INTEGRITY_RECHECK.txt"
            path.write_text(path.read_text() + "tampered\n")
            self.assertIn("integrity_manifest:INTEGRITY_RECHECK.txt", verify(target)["errors"])


if __name__ == "__main__":
    unittest.main()
