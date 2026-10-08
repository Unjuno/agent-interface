import copy,json,unittest
from pathlib import Path
from candidate import run
from audit import audit

CONSTRUCTION={"schema":"amendment-effect-fixture-v1","allocation":"AMENDMENT-EFFECT-LEDGER-6219-T0-CPU-20261002-01","main_sha":"460f09c465a2ff0347917bc2a2805f78bcb5cdab","policies":["old_plan","prompt_reset","blanket_undo","obligation_ledger"],"cases":[
 {"id":"c_unknown","before":["x"],"amendment":{"kind":"retraction","authenticated":True,"clauses":[],"generation":2},"current_generation":1,"effects":[{"clause":"x","state":"UNKNOWN","reversible":False}],"proposals":[]},
 {"id":"c_irrev","before":["publish"],"amendment":{"kind":"retraction","authenticated":True,"clauses":["undo"],"generation":2},"current_generation":1,"effects":[{"clause":"publish","state":"COMMITTED_VERIFIED","reversible":False}],"proposals":[]},
 {"id":"c_stale","before":["open"],"amendment":{"kind":"addition","authenticated":True,"clauses":["read"],"generation":8},"current_generation":7,"effects":[],"proposals":[{"id":"old","generation":7}]},
 {"id":"c_forged","before":["send"],"amendment":{"kind":"retraction","authenticated":False,"clauses":[],"generation":2},"current_generation":1,"effects":[{"clause":"sent","state":"COMMITTED_VERIFIED","reversible":False}],"proposals":[]}]}
ORACLE={"expected_disposition":{"c_unknown":"HOLD_UNKNOWN_DELIVERY","c_irrev":"IMPOSSIBLE_TO_FULLY_SATISFY","c_stale":"CONTINUE_NEW_GENERATION","c_forged":"REJECT_UNAUTHENTICATED"}}
class MethodTests(unittest.TestCase):
 def setUp(self):
  self.raw=run(CONSTRUCTION); self.result=audit(CONSTRUCTION,ORACLE,self.raw)
 def test_construction_reconstructs_all_policy_rows(self):
  self.assertEqual(len(self.raw["rows"]),16); self.assertEqual(self.result["status"],"METHOD_PASS_SCOPED",self.result["errors"])
  self.assertEqual(self.result["exact_oracle_matches_by_policy"]["obligation_ledger"],4)
  for policy in ("old_plan","prompt_reset","blanket_undo"): self.assertEqual(self.result["exact_oracle_matches_by_policy"][policy],0)
 def test_unknown_and_irreversible_are_preserved(self):
  rows={(x["case_id"],x["policy"]):x["result"] for x in self.raw["rows"]}
  self.assertEqual(rows[("c_unknown","obligation_ledger")]["disposition"],"HOLD_UNKNOWN_DELIVERY")
  self.assertEqual(rows[("c_irrev","obligation_ledger")]["disposition"],"IMPOSSIBLE_TO_FULLY_SATISFY")
  self.assertEqual(rows[("c_forged","obligation_ledger")]["retained_effects"],CONSTRUCTION["cases"][3]["effects"])
 def test_four_mutation_controls_rejected(self):
  mutations=[]
  x=copy.deepcopy(self.raw); row=next(r for r in x["rows"] if r["case_id"]=="c_irrev" and r["policy"]=="obligation_ledger"); row["result"]["retained_effects"]=[]; mutations.append(x)
  x=copy.deepcopy(self.raw); row=next(r for r in x["rows"] if r["case_id"]=="c_stale" and r["policy"]=="obligation_ledger"); row["result"]["rejected_proposals"]=[]; mutations.append(x)
  x=copy.deepcopy(self.raw); row=next(r for r in x["rows"] if r["case_id"]=="c_unknown" and r["policy"]=="obligation_ledger"); row["result"]["disposition"]="SATISFIED_NO_EFFECT"; mutations.append(x)
  x=copy.deepcopy(self.raw); row=next(r for r in x["rows"] if r["case_id"]=="c_irrev" and r["policy"]=="obligation_ledger"); row["result"]["disposition"]="COMPENSATION_REQUIRED"; mutations.append(x)
  self.assertEqual(len(mutations),4)
  for raw in mutations: self.assertEqual(audit(CONSTRUCTION,ORACLE,raw)["status"],"METHOD_FAIL")
if __name__=="__main__": unittest.main(verbosity=2)
