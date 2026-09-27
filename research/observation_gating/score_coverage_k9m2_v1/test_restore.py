"""Postformal codec tests on copies; not scientific samples."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from restore import ROOT,restore

class RestoreTests(unittest.TestCase):
    def test_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"RAW.json"
            self.assertEqual(restore(p)["sha256"],json.loads((ROOT/"PACK.json").read_text())["raw_sha256"])
    def test_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"RAW.json";p.write_bytes(b"keep")
            with self.assertRaises(ValueError): restore(p)
            self.assertEqual(p.read_bytes(),b"keep")
    def copied(self,change):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)
            for p in [ROOT/"PACK.json",*ROOT.glob("RAW.columns.part*.b64")]: shutil.copyfile(p,r/p.name)
            change(r)
            with self.assertRaises((ValueError,FileNotFoundError)): restore(r/"RAW.json",r)
            self.assertFalse((r/"RAW.json").exists())
    def test_missing(self): self.copied(lambda r:(r/"RAW.columns.part00.b64").unlink())
    def test_changed(self): self.copied(lambda r:(r/"RAW.columns.part00.b64").write_bytes(b"AAAA"))
    def test_order(self):
        def change(r):
            p=r/"PACK.json";d=json.loads(p.read_text());d["parts"].reverse();p.write_text(json.dumps(d))
        self.copied(change)
    def test_denominator(self):
        def change(r):
            p=r/"PACK.json";d=json.loads(p.read_text());d["row_count"]+=1;p.write_text(json.dumps(d))
        self.copied(change)

if __name__=="__main__":unittest.main()
