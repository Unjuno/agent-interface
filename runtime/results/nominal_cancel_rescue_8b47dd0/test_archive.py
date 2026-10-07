"""Full retained N/U call-history audit, no arm imports or producer replay."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "runtime/results/kernel-nominal-cancel-composition-01a0ff2c"


def decode(record):
    encoded = (PACKET / record["public_name"]).read_bytes()
    if len(encoded) != record["public_bytes"] or hashlib.sha256(encoded).hexdigest() != record["public_sha256"]:
        raise ValueError("public projection")
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded))) as stream:
        data = stream.read(1_048_577)
    if len(data) > 1_048_576 or len(data) != record["original_bytes"] or hashlib.sha256(data).hexdigest() != record["original_sha256"]:
        raise ValueError("original projection")
    return data


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_freeze_and_six_historical_git_sources(self):
        entries = {}
        for line in (PACKET / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(len(entries), 47)
        self.assertEqual(set(entries), {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts
        })
        freeze = json.loads((PACKET / "FREEZE.public.json").read_bytes())
        self.assertEqual(len(freeze["source_files"]), 26)
        for name, digest in freeze["source_files"].items():
            self.assertEqual(hashlib.sha256((PACKET / name).read_bytes()).hexdigest(), digest, name)
        binding = json.loads((PACKET / "SOURCE_BINDING.json").read_bytes())
        self.assertEqual(len(binding["sources"]), 6)
        for source in binding["sources"]:
            revision = source["ref"] + ":runtime/kernel/" + source["name"]
            blob = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", revision]).decode().strip()
            self.assertEqual(blob, source["blob_oid"])
            data = subprocess.check_output(["git", "-C", str(ROOT), "cat-file", "blob", blob])
            self.assertEqual(data, (PACKET / source["saved"]).read_bytes())
            self.assertEqual(len(data), source["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])

    def test_all_nine_lossless_projections_full_receipt_and_controls(self):
        projections = json.loads((PACKET / "PUBLICATION.json").read_bytes())["lossless_raw_projections"]
        self.assertEqual(len(projections), 9)
        data = {record["original_name"]: decode(record) for record in projections}
        with tempfile.TemporaryDirectory(prefix="nominal-cancel-review-") as directory:
            copied = Path(directory) / "packet"
            shutil.copytree(PACKET, copied)
            (copied / "raw.json").write_bytes(data["raw.json"])
            child = subprocess.run([sys.executable, "-B", str(copied / "audit_histories.py")], cwd=copied, capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            observed = json.loads((copied / "audit.json").read_bytes())
            self.assertEqual(observed, json.loads((PACKET / "audit.json").read_bytes()))
            self.assertEqual(observed["rows"], 40)
            self.assertEqual(len(observed["controls"]), 8)
            self.assertTrue(all(control["rejected"] for control in observed["controls"]))
            for number in range(8):
                name = f"control-{number}.json"
                self.assertEqual((copied / name).read_bytes(), data[name])
        raw = json.loads(data["raw.json"])
        missing = {"begun_typed", "begun_shaped_current", "begun_shaped_stale", "begun_missing", "begun_unrelated"}
        summaries = []
        for arm in ("n0u0", "n0u1", "n1u0", "n1u1"):
            rows = [row for row in raw["rows"] if row["arm"] == arm]
            self.assertEqual(len(rows), 10)
            invalid = [call for row in rows for call in row["calls"] if call["call"] == "invalid_stop"]
            summaries.append({"arm": arm, "rows": len(rows),
                "possible_flags_lost": sum(row["case"] in missing and row["outcome"]["effect_occurred"] is False for row in rows),
                "invalid_stop_accepted": sum(call["status"] == "returned" for call in invalid),
                "invalid_stop_attribute_errors": sum(call["status"] == "AttributeError" for call in invalid)})
        self.assertEqual(summaries, json.loads((PACKET / "SUMMARY.json").read_bytes()))

    def test_original_read_only_verifier(self):
        child = subprocess.run([sys.executable, "-B", str(PACKET / "verify_retained.py")], capture_output=True, text=True)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        self.assertEqual(json.loads(child.stdout), {"retained_rows": 40, "lossless_projections": 9, "rejected_controls": 8, "producer_invocations": 0})


if __name__ == "__main__":
    unittest.main()
