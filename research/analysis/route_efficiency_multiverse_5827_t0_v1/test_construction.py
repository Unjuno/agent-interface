import copy,json,unittest
from pathlib import Path
FIXTURE_TEXT=(Path(__file__).parent/"fixtures.json").read_text(encoding="utf-8")
import candidate,audit
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=json.loads(FIXTURE_TEXT); cls.r=candidate.run(cls.f); cls.by={x["cohort_id"]:x for x in cls.r["analyses"]}
 def test_audit(self): self.assertEqual(audit.audit(self.r,self.f)["status"],"PASS_METHOD_SCOPED")
 def test_stable_positive_denominator_phase(self):
  x=self.by["stable_positive"]; self.assertEqual(x["primary_completion"]["n_pairs_total"],3); self.assertEqual(x["primary_completion"]["mean_lower_ms"],-4000); self.assertEqual(x["phase_pair_counts"],{"cold":2,"warm":1})
 def test_same_estimand_sensitivity(self):
  c=self.by["definition_sensitive"]["primary_completion"]; self.assertEqual((c["mean_lower_ms"],c["mean_upper_ms"]),(-5000,25000)); self.assertEqual(c["status"],"HOLD_ROBUSTNESS_FOR_THAT_CLAIM")
 def test_distinct_estimands_tradeoff(self):
  x=self.by["different_estimands_tradeoff"]; self.assertEqual(x["primary_completion"]["mean_lower_ms"],-10000); self.assertEqual(x["different_estimands"]["human_residual_work"]["mean_delta"],15000)
 def test_safe_stop_is_not_completion(self):
  x=self.by["safe_stop_control"]; self.assertEqual(x["primary_completion"]["status"],"HOLD_OPEN_CENSOR_BOUND"); self.assertEqual(x["different_estimands"]["safe_termination"]["mean_delta"],-4000)
 def test_safety_missing_and_endpoints(self):
  self.assertEqual(self.by["collateral_control"]["quality"]["safety_gate"],"FAIL_COLLATERAL_ERROR")
  s=self.by["stable_positive"]["different_estimands"]; self.assertEqual(s["token_usage"]["status"],"HOLD_MISSING_DATA")
  self.assertNotEqual(s["capture_to_effect"]["delta_sum_ms"],s["delivery_to_effect"]["delta_sum_ms"])
 def test_five_mutations_rejected(self):
  ms=[]
  x=copy.deepcopy(self.r); x["analyses"][1]["primary_completion"]["pair_rows"].clear(); ms.append(x)
  x=copy.deepcopy(self.r); x["analyses"][0]["different_estimands"]["token_usage"].update({"status":"METHOD_ONLY","n_pairs_missing":0,"mean_delta":0}); ms.append(x)
  x=copy.deepcopy(self.r); x["analyses"][0]["primary_completion"]["pair_rows"][0].update({"delta_lower_ms":0,"delta_upper_ms":0}); ms.append(x)
  x=copy.deepcopy(self.r); x["analyses"][0]["different_estimands"]["capture_to_effect"]["start_field"]="image_delivery_ms"; ms.append(x)
  x=copy.deepcopy(self.r); x["analyses"].pop(); ms.append(x)
  self.assertTrue(all(audit.audit(x,self.f)["status"]=="FAIL_RAW_AUDIT" for x in ms))
