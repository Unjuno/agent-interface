import importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/f"{n}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
c=load("candidate"); a=load("auditor"); S=json.loads((ROOT/"spec.json").read_text())
class ConstructionTests(unittest.TestCase):
 def test_all_four_cells_show_paired_feedback_access_interaction(self):
  raw=c.build(S); r=a.check(raw,S)
  self.assertEqual(r["trials"],48)
  self.assertAlmostEqual(r["optimism_gaps"]["FULL+SEALED"],.6)
  self.assertEqual(r["optimism_gaps"]["CONTROLLED+SEALED"],0.0)
  self.assertAlmostEqual(r["optimism_gaps"]["CONTROLLED+RAW_BYPASS"],.6)
  self.assertEqual(r["hypothesis_disposition"],"BYPASS_DEFEATS_FEEDBACK_SCOPED")

 def test_access_audit_distinguishes_denial_return_unknown_and_publication(self):
  raw=c.build(S); a.check(raw,S)
  table={(x["feedback_mode"],x["artifact_access_mode"]):x for x in raw["trials"]}
  self.assertEqual(table[("CONTROLLED","SEALED")]["raw_access"]["status"],"DENIED")
  self.assertEqual(table[("CONTROLLED","RAW_BYPASS")]["raw_access"]["status"],"RETURNED")
  self.assertEqual(table[("FULL","SEALED")]["raw_access"]["status"],"NO_ATTEMPT")
  self.assertEqual(raw["access_audit_controls"]["unmonitored_route"]["disposition"],"UNKNOWN_UNMONITORED_ROUTE")
  self.assertTrue(all(t["fresh_prelock_probe"]["status"]=="DENIED" for t in raw["trials"]))

 def test_safety_veto_is_disclosed_and_vetoed_candidate_never_selected(self):
  raw=c.build(S); a.check(raw,S)
  self.assertTrue(all(t["immediate_safety_disclosure"]["disclosure"]=="IMMEDIATE_ALL_ARMS" for t in raw["trials"]))
  self.assertNotIn("unsafe",{t["candidate_update"]["selected_candidate"] for t in raw["trials"]})

 def test_eight_mutations_are_rejected(self):
  raw=c.build(S)
  for m in ("hide_access_log","forge_denial","tamper_canary","leak_fresh","hide_safety","trust_unmonitored","block_benign_docs","unsafe_selection"):
   self.assertTrue(a.mutation_rejected(raw,S,m),m)

if __name__=="__main__": unittest.main()
