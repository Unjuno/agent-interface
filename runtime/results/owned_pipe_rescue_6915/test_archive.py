"""Read-only six-row OS evidence and copied controls; no candidate execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

PACKET = Path(__file__).resolve().parents[3] / "research/concurrency/owned_pipe_cancel_6501_20261003_01a0ff52"


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_freeze_and_tar_readback(self):
        entries = json.loads((PACKET / "MANIFEST.json").read_bytes())["files"]
        self.assertEqual(len(entries), 52)
        self.assertEqual({r["path"] for r in entries}, {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "MANIFEST.json" and "__pycache__" not in p.parts
        })
        for entry in entries:
            data = (PACKET / entry["path"]).read_bytes()
            self.assertEqual(len(data), entry["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
        freeze = json.loads((PACKET / "FREEZE.json").read_bytes())
        self.assertEqual(len(freeze["source_sha256"]), 15)
        for name, digest in freeze["source_sha256"].items():
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        readback = json.loads((PACKET / "results/tar_readback.json").read_bytes())
        self.assertEqual(len(readback["files"]), 7)
        with tarfile.open(PACKET / "results/guest_output.tar") as archive:
            self.assertEqual({m.name.removeprefix("./") for m in archive.getmembers() if m.isfile()}, {r["path"] for r in readback["files"]})
            for entry in readback["files"]:
                data = archive.extractfile("./" + entry["path"]).read()
                self.assertEqual(data, (PACKET / "results" / entry["path"]).read_bytes())
                self.assertEqual(len(data), entry["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

    def test_whole_raw_original_receipt_normal_and_optimized(self):
        raw = PACKET / "results/raw.jsonl"
        records = [json.loads(line) for line in raw.read_text().splitlines()]
        self.assertEqual(len(records), 8)
        self.assertEqual(sum(len(row["events"]) for row in records[1:-1]), 127)
        for optimized in (False, True):
            with self.subTest(optimized=optimized), tempfile.TemporaryDirectory(prefix="pipe-6915-audit-") as directory:
                receipt = Path(directory) / "audit.json"
                flags = ["-O"] if optimized else []
                child = subprocess.run([sys.executable, *flags, "-B", str(PACKET / "audit.py"), str(raw), str(receipt)], capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
                self.assertEqual(json.loads(receipt.read_bytes()), json.loads((PACKET / "results/audit.json").read_bytes()))
                self.assertEqual(json.loads(child.stdout)["trials"], 6)

    def test_all_sixteen_control_variants_and_diagnostics(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized), tempfile.TemporaryDirectory(prefix="pipe-6915-controls-") as directory:
                output = Path(directory) / "controls"
                flags = ["-O"] if optimized else []
                child = subprocess.run([sys.executable, *flags, "-B", str(PACKET / "negative_controls.py"), str(PACKET / "results/raw.jsonl"), str(output)], capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
                observed = json.loads((output / "summary.json").read_bytes())
                self.assertEqual(observed, json.loads((PACKET / "results/negative_controls/summary.json").read_bytes()))
                self.assertEqual(observed["rejected"], 16)
                for control in observed["controls"]:
                    name = control["name"] + ".jsonl"
                    self.assertEqual((output / name).read_bytes(), (PACKET / "results/negative_controls" / name).read_bytes())
                    self.assertTrue(control["errors"], name)


if __name__ == "__main__":
    unittest.main()
