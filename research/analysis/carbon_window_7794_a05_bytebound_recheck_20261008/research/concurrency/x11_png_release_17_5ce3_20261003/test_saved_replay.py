"""Saved-record tests only: no producer/X server/session dispatch."""
import hashlib
import json
import unittest
from pathlib import Path
from PIL import Image
from auditor import audit

ROOT=Path(__file__).resolve().parent
class SavedReplayTests(unittest.TestCase):
    def test_saved_decision_and_raw_identity(self):
        raw=ROOT/"runs/candidate/evidence/raw.jsonl"
        rows=[json.loads(line) for line in raw.read_text().splitlines()]
        expected=json.loads((ROOT/"runs/auditor/AUDIT.json").read_text())
        actual=audit(rows,json.loads((ROOT/"PLAN.json").read_text()))
        actual["raw_sha256"]=hashlib.sha256(raw.read_bytes()).hexdigest()
        self.assertEqual(actual,expected)

    def test_all_twelve_saved_png_identities_and_dimensions(self):
        raw=ROOT/"runs/candidate/evidence/raw.jsonl"
        rows=[json.loads(line) for line in raw.read_text().splitlines()]
        self.assertEqual(len(rows),12)
        for row in rows:
            artifact=row["png"]; path=raw.parent/artifact["file"]
            self.assertEqual(path.stat().st_size,artifact["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),artifact["sha256"])
            with Image.open(path) as img:
                self.assertEqual(img.format,"PNG"); self.assertEqual(img.size,(280,180)); img.verify()

if __name__ == "__main__": unittest.main()
