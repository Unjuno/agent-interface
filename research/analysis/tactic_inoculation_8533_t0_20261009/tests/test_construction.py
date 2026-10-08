import importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/f"{n}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
c=load("candidate"); a=load("auditor"); S=json.loads((ROOT/"spec.json").read_text())
class ConstructionTests(unittest.TestCase):
 def test_truth_oracle_and_all_test_classes_reconstruct(self):
  raw=c.build(S); result=a.check(raw,S)
  self.assertEqual(result["training_examples"],12)
  self.assertEqual(result["test_examples"],16)
  self.assertEqual(result["unseen_tactics"],["social_proof"])
  self.assertEqual(result["truth_classes"],4)

 def test_arms_have_equal_facts_time_and_word_budget(self):
  raw=c.build(S); a.check(raw,S)
  arms=raw["training_arms"]
  for idx in range(12):
   values=[arms[k][idx] for k in S["arms"]]
   self.assertEqual({v["word_budget"] for v in values},{80})
   self.assertEqual({v["exposure_seconds"] for v in values},{60})
   self.assertEqual(len({json.dumps(v["evidence"],sort_keys=True) for v in values}),1)

 def test_test_prompts_do_not_include_truth_or_tactic_labels(self):
  raw=c.build(S)
  forbidden={"truth_class","oracle_label","expected_feedback","tactic_id","tactic_example_id"}
  for prompt in raw["test_prompts"]: self.assertFalse(forbidden & set(prompt))

 def test_seven_mutation_controls_are_rejected(self):
  raw=c.build(S)
  for mutation in ("swap_test_truth","hide_evidence","leak_layout","unknown_as_success","unequal_exposure","oracle_leak","authority"):
   self.assertTrue(a.mutation_rejected(raw,S,mutation),mutation)

if __name__=="__main__": unittest.main()
