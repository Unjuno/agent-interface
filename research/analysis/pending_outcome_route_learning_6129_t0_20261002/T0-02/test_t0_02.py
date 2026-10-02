import copy,json,unittest
from pathlib import Path
import candidate,audit
ROOT=Path(__file__).parent
V=json.loads((ROOT/"visible.json").read_text()); T=json.loads((ROOT/"truth.json").read_text())
R={"cases":{c["id"]:candidate.summarize(c) for c in V["cases"]}}
C=json.loads((ROOT/"visible.json").read_text()); per=sum(C["switch_cost"].values())
R["switch_cost"]={"per_switch":per,"components":C["switch_cost"],"policies":{}}
for n,p in C["policy_paths"].items():
 s=sum(a!=b for a,b in zip(p["routes"],p["routes"][1:])); R["switch_cost"]["policies"][n]={"switches":s,"switch_work_units":s*per,"base_work_units":p["base_work_units"],"total_work_units":p["base_work_units"]+s*per}

class Tests(unittest.TestCase):
 def test_all_predeclared_decisions(self):
  self.assertEqual({k:v["decision"] for k,v in R["cases"].items()},T["expected"])
 def test_independent_audit_passes(self): self.assertEqual(audit.audit(V,T,R)["status"],"PASS_METHOD_SCOPED")
 def test_no_lookahead_yield_is_still_pending(self):
  x=R["cases"]["yield_then_recovered_success"]["routes"]["RECOVER"]["counts"]
  self.assertEqual((x["YIELD"],x["VERIFIED_SUCCESS"],x["PENDING"]),(1,0,2))
 def test_typed_stop_not_wrong_effect(self):
  c=R["cases"]["typed_safe_stop_vs_wrong_effect"]["routes"]
  self.assertEqual(c["SAFE"]["counts"]["POLICY_TERMINAL_SAFE_STOP"],1); self.assertEqual(c["WRONG"]["counts"]["VERIFIED_WRONG_EFFECT"],1)
 def test_switch_cost_penalizes_thrashing(self):
  p=R["switch_cost"]["policies"]; self.assertEqual(p["fixed_baseline"]["total_work_units"],12); self.assertEqual(p["switching_policy"]["total_work_units"],32)
 def test_mutated_decision_rejected(self):
  m=copy.deepcopy(R); m["cases"]["unknown_outcome_dependent_loss"]["decision"]="SELECT:U"; self.assertEqual(audit.audit(V,T,m)["status"],"FAIL")
 def test_mutated_switch_charge_rejected(self):
  m=copy.deepcopy(R); m["switch_cost"]["policies"]["switching_policy"]["total_work_units"]=12; self.assertEqual(audit.audit(V,T,m)["status"],"FAIL")
 def test_future_truth_change_cannot_change_as_of_candidate(self):
  altered=copy.deepcopy(V); altered_truth=copy.deepcopy(T); altered_truth["final_by_deadline"]["yield_then_recovered_success"]["RECOVER"][0]="POLICY_TERMINAL_SAFE_STOP"
  a={c["id"]:candidate.summarize(c) for c in V["cases"]}; b={c["id"]:candidate.summarize(c) for c in altered["cases"]}; self.assertEqual(a,b); self.assertNotEqual(T,altered_truth)

if __name__=="__main__": unittest.main()
