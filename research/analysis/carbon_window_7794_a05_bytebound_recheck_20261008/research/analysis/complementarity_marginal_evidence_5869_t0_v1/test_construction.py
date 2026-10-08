import json, unittest
import candidate, audit
with open("fixture.json",encoding="utf-8") as h: FIXTURE=json.load(h)
def candidate_raw():
 rows=[]
 for case in FIXTURE["cases"]:
  _,bp=candidate.bellman(case)
  plans={"fixed":candidate.fixed(case),"myopic":candidate.myopic(case),"bellman2":bp,"pair_gate":candidate.pair(case)}
  rows.append({"case_id":case["id"],"information_bits":{x["id"]:candidate.ig(case,[x["id"]]) for x in case["checks"]},"strategies":{k:{"plan":p,"claim":candidate.evalplan(case,case["worlds"],p)} for k,p in plans.items()}})
 return {"allocation_id":FIXTURE["allocation_id"],"cases":rows}
class Construction(unittest.TestCase):
 def test_finite_population_and_case_count(self):
  self.assertEqual(len(FIXTURE["cases"]),9)
  self.assertTrue(all(abs(sum(w["weight"] for w in c["worlds"])-1)<1e-12 for c in FIXTURE["cases"]))
 def test_xor_zero_individual_positive_joint(self):
  c=FIXTURE["cases"][0]
  self.assertAlmostEqual(candidate.risk(c,c["worlds"],[])-candidate.risk(c,c["worlds"],["a"]),0)
  self.assertAlmostEqual(candidate.risk(c,c["worlds"],[])-candidate.risk(c,c["worlds"],["b"]),0)
  self.assertAlmostEqual(candidate.risk(c,c["worlds"],[])-candidate.risk(c,c["worlds"],["a","b"]),1.0)
 def test_myopic_stops_and_bellman_buys(self):
  c=FIXTURE["cases"][0]
  self.assertEqual(candidate.myopic(c),{"stop":True})
  self.assertLess(candidate.bellman(c)[0],candidate.terminal(c,c["worlds"])[0])
 def test_pair_gate_detects_xor(self):
  plan=candidate.pair(FIXTURE["cases"][0])
  self.assertEqual(plan["test"],"a")
  self.assertTrue(all(x["test"]=="b" for x in plan["branches"].values()))
 def test_redundant_source_does_not_trigger_pair(self):
  self.assertEqual(candidate.pair(FIXTURE["cases"][1]),{"stop":True})
 def test_diminishing_returns_spends_once(self):
  c=FIXTURE["cases"][2]
  self.assertEqual(candidate.myopic(c),candidate.seq(c,["a"]))
  self.assertEqual(candidate.pair(c),{"stop":True})
 def test_cost_deadline_epoch_source_gates(self):
  for c in FIXTURE["cases"][3:7]:
   self.assertEqual(candidate.pair(c),{"stop":True})
 def test_mandatory_gate_blocks_evidence_acquisition(self):
  c=FIXTURE["cases"][7]
  self.assertFalse(candidate.feasible(c,["a"]))
  self.assertEqual(candidate.bellman(c)[1],{"stop":True})
 def test_one_bit_can_have_low_decision_value(self):
  c=FIXTURE["cases"][8]
  self.assertAlmostEqual(candidate.ig(c,["a"]),1.0)
  self.assertEqual(candidate.pair(c),{"stop":True})
 def test_probability_utility_and_cost_mutations_are_not_hardcoded(self):
  c=json.loads(json.dumps(FIXTURE["cases"][0]))
  base=candidate.risk(c,c["worlds"],[])
  c["worlds"][0]["weight"]=.5
  self.assertNotAlmostEqual(candidate.risk(c,c["worlds"],[]),base)
  u=json.loads(json.dumps(FIXTURE["cases"][0]))
  u["loss"]["abstain"]["true"]=.1
  self.assertNotAlmostEqual(candidate.risk(u,u["worlds"],[]),base)
  expensive=json.loads(json.dumps(FIXTURE["cases"][0]))
  for x in expensive["checks"]:x["cost"]=.6
  expensive["budget"]=1.5
  self.assertEqual(candidate.pair(expensive),{"stop":True})
 def test_raw_only_audit_and_mutations(self):
  raw=candidate_raw()
  baseline=audit.audit(FIXTURE,raw)
  self.assertEqual(baseline["status"],"PASS_METHOD_SCOPED",baseline["errors"])
  omitted=json.loads(json.dumps(raw));omitted["cases"].pop()
  self.assertEqual(audit.audit(FIXTURE,omitted)["status"],"FAIL_AUDIT")
  altered=json.loads(json.dumps(raw));altered["cases"][0]["strategies"]["pair_gate"]["claim"]["total_loss"]+=1
  self.assertEqual(audit.audit(FIXTURE,altered)["status"],"FAIL_AUDIT")
if __name__=="__main__":unittest.main(verbosity=2)
