import copy,json,unittest
from pathlib import Path
import candidate,audit
ROOT=Path(__file__).parent;DATA=json.loads((ROOT/"fixture.json").read_text());RAW=candidate.run(DATA)

class Tests(unittest.TestCase):
 def test_sunk_only_pair_forwards_switch_invariantly(self):
  self.assertTrue(RAW["pairs"]["sunk_only_pair"]["forward_equivalent"]);self.assertEqual(RAW["cards"]["low_sunk"]["choice"],"SWITCH");self.assertEqual(RAW["cards"]["high_sunk"]["choice"],"SWITCH")
 def test_positive_forward_cost_control_changes_choice(self):
  self.assertEqual(RAW["cards"]["positive_future_cost"]["choice"],"CONTINUE")
 def test_each_legitimate_forward_difference_rejects_pair(self):
  for key in ["artifact_control","evidence_control","deadline_control","budget_control","action_set_control","future_cost_control"]:self.assertFalse(RAW["pairs"][key]["forward_equivalent"])
 def test_unknown_stays_unknown(self):self.assertEqual(RAW["cards"]["unknown_probability"]["choice"],"UNKNOWN")
 def test_independent_oracle_passes(self):self.assertEqual(audit.audit(DATA,RAW)["status"],"PASS_METHOD_SCOPED")
 def test_auditor_rejects_sunk_choice_flip(self):
  x=copy.deepcopy(RAW);x["cards"]["high_sunk"]["choice"]="CONTINUE";self.assertEqual(audit.audit(DATA,x)["status"],"FAIL")
 def test_auditor_rejects_informative_pair_labeled_equivalent(self):
  x=copy.deepcopy(RAW);x["pairs"]["future_cost_control"]["forward_equivalent"]=True;self.assertEqual(audit.audit(DATA,x)["status"],"FAIL")
 def test_auditor_rejects_positive_control_miscalculation(self):
  x=copy.deepcopy(RAW);x["cards"]["positive_future_cost"]["values"]["SWITCH"]="5";self.assertEqual(audit.audit(DATA,x)["status"],"FAIL")
 def test_prior_cost_not_used_in_forward_values(self):
  low=candidate.evaluate(DATA["cards"][0]);high=candidate.evaluate(DATA["cards"][1]);self.assertEqual(low,high)

if __name__=="__main__":unittest.main()
