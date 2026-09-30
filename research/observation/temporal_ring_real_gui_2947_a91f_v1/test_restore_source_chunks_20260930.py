import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent
RESTORE = ROOT / "restore_source_chunks_20260930.py"


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.temp.name)
        self.capsule = self.base / "capsule"
        shutil.copytree(ROOT, self.capsule,
                        ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        self.temp.cleanup()

    def run_restore(self, capsule, destination):
        return subprocess.run(
            [sys.executable, "-I", "-S", "-B",
             str(capsule / RESTORE.name), str(destination)],
            cwd=capsule, capture_output=True, text=True, timeout=10)

    def test_exact_archive_and_frozen_sources_restore(self):
        destination = self.base / "restored"
        result = self.run_restore(self.capsule, destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        recovery = json.loads((self.capsule / "RECOVERY_20260930.json").read_text())
        frozen = json.loads((self.capsule / "FREEZE.json").read_text())
        archive = (destination / "temporal_ring_source.tar.xz").read_bytes()
        self.assertEqual(len(archive), recovery["archive_bytes"])
        self.assertEqual(hashlib.sha256(archive).hexdigest(),
                         recovery["archive_sha256"])
        for name, digest in frozen["source_sha256"].items():
            self.assertEqual(hashlib.sha256((destination / name).read_bytes()).hexdigest(),
                             digest, name)

    def test_corrupt_chunk_rejected_without_output(self):
        part = self.capsule / "SOURCE.chunk00.b64"
        part.write_bytes(part.read_bytes() + b"corruption")
        destination = self.base / "must-not-exist"
        result = self.run_restore(self.capsule, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(destination.exists())

    def test_existing_destination_is_not_overwritten(self):
        destination = self.base / "existing"
        destination.mkdir()
        sentinel = destination / "sentinel"
        sentinel.write_text("preserve")
        result = self.run_restore(self.capsule, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
