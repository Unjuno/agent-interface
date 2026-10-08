"""Independent-process retained SQLite audit, never app/server/browser replay."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

PACKET = Path(__file__).resolve().parents[3] / "research/integration/semantic_endpoint_browser_5442_01a0ff58"


def materialize(root):
    mapping = json.loads((PACKET / "SOURCE_MAP.json").read_bytes())
    for original, published in mapping.items():
        shutil.copyfile(PACKET / published, root / original)
    shutil.copyfile(PACKET / "FREEZE.json", root / "FREEZE.json")
    output = root / "retained"
    shutil.copytree(PACKET / "run-01", output)
    # Copy all evidence except the exclusive destination; never unlink original.
    (output / "AUDIT.json").rename(root / "historical-audit.json")
    return output


def audit(root, output):
    return subprocess.run([sys.executable, "-B", str(root / "auditor.py"), "--out", str(output)], cwd=root, capture_output=True, text=True)


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_and_original_source_freeze(self):
        manifest = json.loads((PACKET / "MANIFEST.json").read_bytes())["files"]
        self.assertEqual(len(manifest), 60)
        self.assertEqual(set(manifest), {
            p.relative_to(PACKET).as_posix() for p in PACKET.rglob("*")
            if p.is_file() and p.name != "MANIFEST.json" and "__pycache__" not in p.parts
        })
        for name, entry in manifest.items():
            data = (PACKET / name).read_bytes()
            self.assertEqual(len(data), entry["bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"], name)
        mapping = json.loads((PACKET / "SOURCE_MAP.json").read_bytes())
        freeze = json.loads((PACKET / "FREEZE.json").read_bytes())
        self.assertEqual(len(mapping), 12)
        self.assertEqual(set(mapping), set(freeze["files"]))
        for original, published in mapping.items():
            self.assertEqual(hashlib.sha256((PACKET / published).read_bytes()).hexdigest(), freeze["files"][original])

    def test_whole_sqlite_trace_audit_and_ten_mutations(self):
        with tempfile.TemporaryDirectory(prefix="browser-6914-audit-") as directory:
            root = Path(directory)
            output = materialize(root)
            child = audit(root, output)
            self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
            observed = json.loads((output / "AUDIT.json").read_bytes())
            historical = json.loads((PACKET / "run-01/AUDIT.json").read_bytes())
            self.assertLessEqual(datetime.fromisoformat(observed["started_utc"]), datetime.fromisoformat(observed["ended_utc"]))
            for key in ("started_utc", "ended_utc"):
                observed.pop(key)
                historical.pop(key)
            self.assertEqual(observed, historical)
            self.assertEqual(len(observed["raw_matches"]), 14)
            self.assertEqual(len(observed["copied_raw_mutations"]), 10)
            self.assertTrue(all(r["decision"] == "UNKNOWN" for r in observed["copied_raw_mutations"]))
            self.assertEqual(json.loads(child.stdout), {"result": "PASS_APPLICATION_ENDPOINT_SCOPED", "raw_matches": 14, "mutation_rejections": 10})

    def test_copied_database_and_trace_corruptions_refused(self):
        # Additional integration checks prove the CLI checks whole SQL/trace,
        # not just the original endpoint_truth copied-row mutation controls.
        for mutation in ("database", "trace"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="browser-6914-corrupt-") as directory:
                root = Path(directory)
                output = materialize(root)
                if mutation == "database":
                    with sqlite3.connect(output / "endpoint-after-initial.sqlite") as database:
                        database.execute("UPDATE documents SET value='RESCUE-CORRUPTION' WHERE target='A'")
                    reason = "SQLite/raw disagreement:documents"
                else:
                    rows = [json.loads(line) for line in (output / "ui-trace.jsonl").read_text().splitlines()]
                    rows[1]["nonce"] = "RESCUE-CORRUPTION"
                    (output / "ui-trace.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
                    reason = "UI intent mismatch"
                child = audit(root, output)
                self.assertNotEqual(child.returncode, 0)
                self.assertIn(reason, child.stderr)
                self.assertFalse((output / "AUDIT.json").exists())


if __name__ == "__main__":
    unittest.main()
