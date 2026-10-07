import hashlib,json,unittest
from pathlib import Path
import auditor,candidate
class ArtifactSurvivalScorer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(__file__).parent;cls.fixture=json.loads((cls.root/"fixture.json").read_text())
 def raw(self):
  r=candidate.run(self.fixture);r["fixture_sha256"]=hashlib.sha256((self.root/"fixture.json").read_bytes()).hexdigest();r["candidate_sha256"]=hashlib.sha256((self.root/"candidate.py").read_bytes()).hexdigest();return r
 def test_initial_and_later_properties_are_separate(self):
  raw=self.raw();self.assertEqual(auditor.audit(raw,self.fixture),[])
  self.assertTrue(all(x["pass"] for x in raw["initial"]))
  by={(x["scenario"],x["route"]):x for x in raw["later"]}
  self.assertEqual(by[("silent_formula_drop","route_fast")]["later_status"],"FAIL")
  self.assertEqual(by[("harmless_cosmetic_change","route_fast")]["later_status"],"PASS")
  self.assertEqual(by[("external_dependency_missing","route_fast")]["later_status"],"UNKNOWN")
 def test_metric_mutations_rejected(self):
  for name,value in auditor.corruptions(self.raw()).items():
   with self.subTest(name=name):self.assertTrue(auditor.audit(value,self.fixture))
if __name__=="__main__":unittest.main()
