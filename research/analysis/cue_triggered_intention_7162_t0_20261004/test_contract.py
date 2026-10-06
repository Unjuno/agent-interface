import hashlib, json, unittest
from pathlib import Path
import auditor, candidate

class CueRetrievalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).parent; cls.fixture=json.loads((cls.root/"fixture.json").read_text())
    def raw(self):
        value=candidate.run(self.fixture)
        value["fixture_sha256"]=hashlib.sha256((self.root/"fixture.json").read_bytes()).hexdigest()
        value["candidate_sha256"]=hashlib.sha256((self.root/"candidate.py").read_bytes()).hexdigest()
        return value
    def test_lifecycle_cue_and_no_authority(self):
        raw=self.raw(); self.assertEqual(auditor.audit(raw,self.fixture),[])
        for row in raw["rows"]:
            if row["policy"]!="PLAIN_TEXT":
                self.assertFalse(row["input_authorized"])
                if row["lifecycle"]!="PENDING" or row["cue"]!="EXACT_OBJECT_STATE": self.assertFalse(row["recalled"])
        self.assertTrue(any(r["recalled"] for r in raw["rows"] if r["policy"]=="TYPED_LIFECYCLE" and r["lifecycle"]=="PENDING" and r["cue"]=="EXACT_OBJECT_STATE"))
    def test_mutations_rejected(self):
        raw=self.raw()
        for name,value in auditor.corruptions(raw).items():
            with self.subTest(name=name): self.assertTrue(auditor.audit(value,self.fixture))
if __name__=="__main__": unittest.main()
