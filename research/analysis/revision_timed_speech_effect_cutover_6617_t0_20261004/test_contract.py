import hashlib,json,unittest
from pathlib import Path
import auditor,candidate
class SpeechCutoverContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(__file__).parent;cls.fixture=json.loads((cls.root/"fixture.json").read_text())
 def raw(self):
  r=candidate.run(self.fixture);r["fixture_sha256"]=hashlib.sha256((self.root/"fixture.json").read_bytes()).hexdigest();r["candidate_sha256"]=hashlib.sha256((self.root/"candidate.py").read_bytes()).hexdigest();return r
 def test_final_gate_and_stable_overlap_saving(self):
  r=self.raw();self.assertEqual(auditor.audit(r,self.fixture),[])
  by={(x["scenario"],x["policy"]):x for x in r["rows"]}
  self.assertLess(by[("stable_request","VERSION_BOUND_READ_ONLY_PREPARATION")]["verified_at_ms"],by[("stable_request","FINAL_ONLY")]["verified_at_ms"])
  for sid in ("mid_utterance_negation","changed_recipient","quoted_command","two_speakers_overlap","stale_completion_after_revision","stop_before_input"):
   self.assertFalse(any(e["phase"]=="PROVISIONAL_CONSEQUENTIAL" for e in by[(sid,"VERSION_BOUND_READ_ONLY_PREPARATION")]["events"]))
 def test_corruptions_rejected(self):
  for n,v in auditor.mutations(self.raw()).items():
   with self.subTest(name=n):self.assertTrue(auditor.audit(v,self.fixture))
if __name__=="__main__":unittest.main()
