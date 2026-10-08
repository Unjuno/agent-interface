import importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/f"{n}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
c=load("candidate"); a=load("auditor"); S=json.loads((ROOT/"spec.json").read_text())
class ConstructionTests(unittest.TestCase):
 def test_full_rows_and_all_scenario_gates_reconstruct(self):
  raw=c.run(S); result=a.check(raw,S)
  self.assertEqual(result["rows_reconstructed"],18000)
  self.assertEqual(raw["scenario_results"]["uniform_dif"]["classification"]["items"]["target_uniform"],"UNIFORM_DIF")
  self.assertEqual(raw["scenario_results"]["nonuniform_dif"]["classification"]["items"]["target_nonuniform"],"NONUNIFORM_DIF")
  self.assertEqual(raw["scenario_results"]["invariant"]["classification"]["items"]["null_item"],"NO_FLAG")
  self.assertEqual(raw["scenario_results"]["placebo_labels"]["classification"]["items"]["null_item"],"NO_FLAG")
  self.assertEqual(raw["scenario_results"]["low_discrimination"]["classification"]["items"]["low_discrimination"],"LOW_INFORMATION")
  self.assertEqual(raw["scenario_results"]["no_common_support"]["classification"]["disposition"],"HOLD_COMMON_SUPPORT")
  self.assertEqual(raw["scenario_results"]["invalid_anchors"]["classification"]["disposition"],"HOLD_ANCHOR_INVALID")
  self.assertEqual(raw["scenario_results"]["missing_unknown"]["classification"]["items"]["target_uniform"],"UNKNOWN_LOW_SUPPORT")

 def test_missing_outcomes_remain_in_assigned_denominator(self):
  raw=c.run(S); r=raw["scenario_results"]["missing_unknown"]
  self.assertEqual(r["row_count"],2400)
  self.assertEqual(r["known_count"],2350)
  self.assertEqual(r["row_count"]-r["known_count"],50)

 def test_independent_mutation_controls_reject_seven_failures(self):
  raw=c.run(S)
  for mutation in ("drop_response","flip_label","impute_unknown","false_uniform_null","accept_nonoverlap","ignore_bad_anchors","authority"):
   self.assertTrue(a.mutation_rejected(raw,S,mutation),mutation)

if __name__=="__main__": unittest.main()
