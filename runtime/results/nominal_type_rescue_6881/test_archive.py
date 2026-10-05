"""Read-only validation of the public #6881 evidence, not runtime promotion."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKET = Path(__file__).resolve().parent.parent / "kernel-type-boundary-01a0ff2d-eb8e"


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_and_publication_inverses(self):
        entries = {}
        for line in (PACKET / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(len(entries), 42)
        self.assertEqual(set(entries), {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts
        })
        publication = json.loads((PACKET / "PUBLICATION.json").read_text())
        self.assertEqual(len(publication["newline_derivatives"]), 18)
        for name, metadata in publication["newline_derivatives"].items():
            data = (PACKET / name).read_bytes()
            self.assertEqual(len(data), metadata["committed_bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), metadata["committed_sha256"], name)
            inverse = data.replace(b"\n", b"\r\n")
            self.assertEqual(len(inverse), metadata["pre_normalization_bytes"], name)
            self.assertEqual(hashlib.sha256(inverse).hexdigest(), metadata["pre_normalization_sha256"], name)
        self.assertEqual((PACKET / "before-tests.exit-code.txt").read_text().strip(), "1")

    def test_baseline_source_git_blob_pins(self):
        pins = json.loads((PACKET / "source-git-pins.json").read_text())
        self.assertEqual(len(pins["blobs"]), 5)
        for name, digest in pins["blobs"].items():
            data = (PACKET / name).read_bytes()
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            self.assertEqual(hashlib.sha1(blob).hexdigest(), digest, name)

    def test_whole_raw_audits_and_ten_corruptions(self):
        digests = {
            "baseline": "97e36f43460e50d0d565dbcda6c269eee1dac895ab3dc2e5f4a762477096cf3f",
            "candidate": "9a3e0e5b4f7d7901cc72ee1fe35cbfd7051bdf2751045afd8727d5e42e21d19d",
        }
        with tempfile.TemporaryDirectory(prefix="nominal-6881-audit-") as directory:
            output = Path(directory)
            for revision, digest in digests.items():
                raw = gzip.decompress(base64.b64decode((PACKET / (revision + "-raw.json.gz.b64")).read_bytes()))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                source = output / (revision + "-raw.json")
                source.write_bytes(raw)
                receipt = output / (revision + "-audit.json")
                child = subprocess.run([sys.executable, "-B", str(PACKET / "audit.py"), str(source), str(receipt)], capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
                observed = json.loads(receipt.read_text())
                self.assertEqual(observed, json.loads((PACKET / (revision + "-audit-v2.json")).read_text()))
                self.assertEqual(observed["rows"], 28)
                self.assertEqual(observed["status"], "PASS_RAW_RECONSTRUCTION")
                if revision == "candidate":
                    self.assertEqual(len(observed["controls"]), 10)
                    self.assertTrue(all(control["rejected"] for control in observed["controls"]))


if __name__ == "__main__":
    unittest.main()
