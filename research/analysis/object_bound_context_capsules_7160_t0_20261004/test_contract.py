import hashlib,json,unittest
from pathlib import Path
import auditor,candidate
class CapsuleContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(__file__).parent;cls.fixture=json.loads((cls.root/"fixture.json").read_text())
 def raw(self):
  r=candidate.run(self.fixture);r["fixture_sha256"]=hashlib.sha256((self.root/"fixture.json").read_bytes()).hexdigest();r["candidate_sha256"]=hashlib.sha256((self.root/"candidate.py").read_bytes()).hexdigest();return r
 def test_identity_lifecycle_and_mutable_field_contract(self):
  raw=self.raw();self.assertEqual(auditor.audit(raw,self.fixture),[])
  exact=next(r for r in raw["rows"] if r["policy"]=="IDENTITY_BOUND" and r["case"]=="same_object_appearance_change")
  moved=next(r for r in raw["rows"] if r["policy"]=="IDENTITY_BOUND" and r["case"]=="same_object_moved")
  self.assertTrue(exact["retrieved"]);self.assertIn("appearance",exact["stale_fields"]);self.assertIn("location",moved["stale_fields"])
 def test_mutations_rejected(self):
  for name,v in auditor.mutations(self.raw()).items():
   with self.subTest(name=name):self.assertTrue(auditor.audit(v,self.fixture))
if __name__=="__main__":unittest.main()
