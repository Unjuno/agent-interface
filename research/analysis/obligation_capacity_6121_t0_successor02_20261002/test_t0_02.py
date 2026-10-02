import copy,json,unittest
from pathlib import Path
import candidate,audit
ROOT=Path(__file__).parent;F=json.loads((ROOT/"fixture.json").read_text());R=candidate.run(F)

class Tests(unittest.TestCase):
 def test_class_aware_backlog_age_and_useful_completion_tradeoff(self):
  n=R["cases"]["near_saturated_burst_drain"];a=n["CLASS_AWARE"];self.assertLess(a["max_system_backlog"],n["LEDGER_ONLY"]["max_system_backlog"]);self.assertLess(a["max_age"],n["LEDGER_ONLY"]["max_age"]);self.assertGreater(len(a["verified_effects"]),len(n["GLOBAL_WAIT"]["verified_effects"]))
 def test_below_capacity_feasible_control(self):
  self.assertEqual(R["cases"]["below_capacity_control"]["CLASS_AWARE"]["status"],"FEASIBLE_SERVICE_REGION")
 def test_above_capacity_is_contained_and_defers(self):
  x=R["cases"]["above_capacity_burst"]["CLASS_AWARE"];self.assertEqual(x["status"],"SATURATED_BUT_CONTAINED");self.assertTrue(x["deferred"])
 def test_unknown_oracle_and_capacity_never_claim_stability(self):
  self.assertEqual(R["cases"]["missing_effect_oracle"]["CLASS_AWARE"]["status"],"UNRESOLVABLE_ORACLE_GAP");self.assertEqual(R["cases"]["unknown_capacity"]["CLASS_AWARE"]["status"],"UNKNOWN_CAPACITY")
 def test_mandatory_release_bypasses_gate_and_is_serviced(self):
  for policy in F["policies"]:self.assertEqual(R["cases"]["above_capacity_burst"][policy]["mandatory_releases"],[{"id":"REL2","tick":0}])
 def test_transfer_timeout_and_failed_compensation_conserve_system_count(self):
  x=R["ledger_replay"];self.assertEqual([s["system_pending"] for s in x["snapshots"]],[1,1,1,1,2,1]);self.assertEqual(x["records"]["C"]["status"],"PENDING");self.assertEqual(x["system_pending"],1)
 def test_independent_audit_passes(self):self.assertEqual(audit.audit(F,R)["status"],"PASS_METHOD_SCOPED")
 def test_auditor_rejects_transfer_as_discharge(self):
  x=copy.deepcopy(R);x["ledger_replay"]["snapshots"][1]["system_pending"]=0;self.assertEqual(audit.audit(F,x)["status"],"FAIL")
 def test_auditor_rejects_suppressed_mandatory_release(self):
  x=copy.deepcopy(R);x["cases"]["above_capacity_burst"]["CLASS_AWARE"]["mandatory_releases"]=[];self.assertEqual(audit.audit(F,x)["status"],"FAIL")
 def test_auditor_rejects_unresolved_id_drop(self):
  x=copy.deepcopy(R);x["cases"]["near_saturated_burst_drain"]["LEDGER_ONLY"]["unresolved_ids"]=[];self.assertEqual(audit.audit(F,x)["status"],"FAIL")
 def test_auditor_rejects_false_boundedness(self):
  x=copy.deepcopy(R);x["cases"]["unknown_capacity"]["CLASS_AWARE"]["status"]="FEASIBLE_SERVICE_REGION";self.assertEqual(audit.audit(F,x)["status"],"FAIL")

if __name__=="__main__":unittest.main()
