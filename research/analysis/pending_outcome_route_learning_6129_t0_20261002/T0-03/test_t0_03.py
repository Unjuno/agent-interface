import copy,json,unittest
from pathlib import Path
import candidate,audit
ROOT=Path(__file__).parent;V=json.loads((ROOT/"visible.json").read_text());T=json.loads((ROOT/"truth.json").read_text())
R={"cases":{c["id"]:candidate.analyze(c) for c in V["cases"]}}; unit=sum(V["switch_cost"].values());R["switching"]={"per_change":unit,"policies":{}}
for n,p in V["policy_paths"].items():
 k=sum(a!=b for a,b in zip(p["routes"],p["routes"][1:]));R["switching"]["policies"][n]={"changes":k,"switch_cost":k*unit,"total_work":p["base_work"]+k*unit}

class Tests(unittest.TestCase):
 def test_complete_case_vs_pending_inversion(self):
  x=R["cases"]["delay_inversion"];self.assertEqual(x["complete_case"],"SELECT:B");self.assertEqual(x["pending_aware"],"NO_RANKING")
 def test_deadline_truth_reverses_complete_case(self):
  rows={x[0]:x for x in T["terminal_events"]["delay_inversion"]};self.assertEqual(sum(x[1]=="VERIFIED_SUCCESS" for x in rows.values() if x[0].startswith("A")),3);self.assertEqual(sum(x[1]=="VERIFIED_SUCCESS" for x in rows.values() if x[0].startswith("B")),2)
 def test_typed_terminals_and_recovery(self):
  c=R["cases"]["typed_terminals"]["routes"];self.assertEqual(c["SAFE"]["counts"]["POLICY_TERMINAL_SAFE_STOP"],1);self.assertEqual(c["WRONG"]["counts"]["VERIFIED_WRONG_EFFECT"],1)
  self.assertEqual(R["cases"]["yield_recovery"]["routes"]["RECOVER"]["counts"]["YIELD"],1)
 def test_null_unknown_and_state_mismatch(self):
  self.assertEqual(R["cases"]["equal_delay_null"]["pending_aware"],"NO_PREFERENCE");self.assertEqual(R["cases"]["unknown_loss"]["pending_aware"],"NONIDENTIFIABLE");self.assertEqual(R["cases"]["state_coupled"]["pending_aware"],"MODEL_MISMATCH_UNKNOWN")
 def test_switching_work_costed(self):self.assertEqual(R["switching"]["policies"]["fixed"]["total_work"],12);self.assertEqual(R["switching"]["policies"]["switching"]["total_work"],32)
 def test_independent_audit_pass(self):self.assertEqual(audit.audit(V,T,R)["status"],"PASS_METHOD_SCOPED")
 def test_audit_rejects_future_rate_mutation(self):
  m=copy.deepcopy(R);m["cases"]["delay_inversion"]["complete_case"]="NO_PREFERENCE";self.assertEqual(audit.audit(V,T,m)["status"],"FAIL")
 def test_audit_rejects_switch_mutation(self):
  m=copy.deepcopy(R);m["switching"]["policies"]["switching"]["total_work"]=12;self.assertEqual(audit.audit(V,T,m)["status"],"FAIL")
 def test_truth_future_never_changes_candidate(self):
  changed=copy.deepcopy(T);changed["terminal_events"]["delay_inversion"][0][1]="POLICY_TERMINAL_SAFE_STOP";self.assertNotEqual(changed,T);self.assertEqual({c["id"]:candidate.analyze(c) for c in V["cases"]},R["cases"])

if __name__=="__main__":unittest.main()
