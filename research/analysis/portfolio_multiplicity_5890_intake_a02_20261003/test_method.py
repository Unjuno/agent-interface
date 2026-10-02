"""Construction tests use inline rows only, never the formal fixture."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import candidate, auditor

class MethodTests(unittest.TestCase):
    def setUp(self):
        self.raw=b"inline-only"
        self.data={"fixture_id":"inline","rows":[
            {"id":"idea","kind":"intake","screen":"NOT_TESTED_DUPLICATE","test_started":False,"claim_id":None,"statistical_eligible":False,"p_value":None},
            {"id":"neg","kind":"test","test_started":True,"claim_id":"N","statistical_eligible":True,"p_value":0.2,"outcome":"TEST_STARTED_FAIL","abandoned_after_interim":True},
            {"id":"stop","kind":"test","test_started":True,"claim_id":"S","statistical_eligible":False,"p_value":None,"outcome":"TEST_STARTED_STOP","abandoned_after_interim":False},
            {"id":"safe","kind":"deterministic","test_started":True,"claim_id":"M","statistical_eligible":False,"p_value":None,"outcome":"HARD_SAFETY_FAIL","hard_safety":True}
        ]}
    def test_screened_idea_not_in_family(self):
        out=candidate.project(self.data,self.raw)
        self.assertEqual(out["counts"]["screened_out_not_tested"],1); self.assertEqual(out["statistical_family"],[{"id":"neg","claim_id":"N","p_value":0.2}])
    def test_abandoned_negative_counted(self):
        self.assertEqual(candidate.project(self.data,self.raw)["counts"]["started_negative_abandoned"],1)
    def test_stop_is_started_not_eligible(self):
        out=candidate.project(self.data,self.raw)
        self.assertEqual(len(out["started_opportunities"]),2); self.assertEqual(len(out["statistical_family"]),1)
    def test_independent_replay(self):
        self.assertEqual(candidate.project(self.data,self.raw),auditor.replay(self.data,self.raw))
    def test_five_corruption_controls(self):
        controls=auditor.mutations_rejected(auditor.replay(self.data,self.raw))
        self.assertEqual(len(controls),5); self.assertTrue(all(controls.values()))

if __name__=="__main__": unittest.main(verbosity=2)
