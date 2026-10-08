#!/usr/bin/env python3
"""Non-model construction checks; no Ollama generation calls."""
import json, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
import audit_model
sys.path.insert(0,str(ROOT/"candidate_inputs"))
import run_model

class ConstructionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tasks=json.loads((ROOT/"candidate_inputs"/"task_prompts.json").read_text())
  cls.truth=json.loads((ROOT/"oracle"/"oracle_truth.json").read_text())
 def test_case_count_and_ids(self):
  self.assertEqual(len(self.tasks),8)
  self.assertEqual(len({x["case_id"] for x in self.tasks}),8)
  self.assertEqual({x["expected"] for x in self.truth},{"select","abstain"})
 def test_duplicate_and_absent_controls(self):
  cases={x["case_id"]:x for x in self.truth}
  self.assertEqual(cases["duplicate-context-top-left"]["target_label"],"Save")
  self.assertEqual(cases["duplicate-context-bottom-right"]["target_label"],"Open")
  self.assertEqual(cases["target-absent"]["expected"],"abstain")
  self.assertEqual(cases["ambiguous-duplicate-target"]["expected"],"abstain")
 def test_scoring_requires_in_box_source_coordinate(self):
  truth=next(x for x in self.truth if x["case_id"]=="duplicate-context-top-left")
  b=truth["target_box"]
  self.assertTrue(audit_model.score({"abstain":False,"x":(b[0]+b[2])//2,"y":(b[1]+b[3])//2},truth)[0])
  self.assertFalse(audit_model.score({"abstain":False,"x":1023,"y":639},truth)[0])
 def test_abstention_and_crop_selection_deterministic(self):
  truth=next(x for x in self.truth if x["case_id"]=="target-absent")
  self.assertTrue(audit_model.score({"abstain":True,"x":None,"y":None},truth)[0])
  image_path=ROOT/"candidate_inputs"/"screens"/"target-missed-candidate.png"
  from PIL import Image
  image=Image.open(image_path).convert("RGB")
  self.assertEqual(audit_model.selected_tile(image),audit_model.selected_tile(image))
 def test_candidate_arm_images_match_independent_builder(self):
  for task in self.tasks:
   for arm in run_model.ARMS:
    actual,selected,_=run_model.build_images(task,arm)
    tile,box,expected=audit_model.expected_images(task,arm)
    self.assertEqual(selected["tile"],tile)
    self.assertEqual(tuple(selected["box"]),box)
    self.assertEqual([(r,b,list(x),list(s)) for (r,b,x,s) in actual],
      [(r,audit_model.png(im),list(x),list(im.size)) for (r,im,x) in expected])

if __name__=="__main__": unittest.main()
