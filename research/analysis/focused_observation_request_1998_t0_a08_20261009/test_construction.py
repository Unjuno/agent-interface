#!/usr/bin/env python3
"""Pre-freeze checks for matrix cardinality and auditor mutation mechanics."""
import copy,importlib.util,json,math,pathlib,unittest
PKG=pathlib.Path(__file__).resolve().parent
def load(name):
 spec=importlib.util.spec_from_file_location(name,PKG/(name+".py")); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
class Construction(unittest.TestCase):
 def setUp(self): self.design=json.loads((PKG/"design.json").read_text())
 def test_exhaustive_case_cardinality(self):
  frames=math.prod(len(v) for v in self.design["frame_domains"].values()); requests=math.prod(len(v) for v in self.design["request_domains"].values())
  self.assertEqual(frames,16); self.assertEqual(requests,1728); self.assertEqual(frames*requests+self.design["full_controls_per_frame"]*frames,27664)
 def test_candidate_request_generator_cardinality(self):
  candidate=load("candidate"); frame=candidate.make_frame(4,"window-A","focus-live",0,self.design)
  self.assertEqual(sum(1 for _ in candidate.request_rows(frame,self.design)),1728)
 def test_independent_request_generators_agree_on_canonical_input_rows(self):
  candidate=load("candidate"); auditor=load("auditor"); f1=candidate.make_frame(5,"window-B",None,1,self.design); f2=auditor.reconstruct_frame(5,"window-B",None,1,self.design)
  self.assertEqual(f1,f2); self.assertEqual(list(candidate.request_rows(f1,self.design)),list(auditor.request_permutations(f2,self.design["request_domains"])))
 def test_independent_oracle_cardinality(self): self.assertEqual(len(load("auditor").expected_cases(self.design)),27664)
 def test_independent_oracle_decision_census(self):
  cases=load("auditor").expected_cases(self.design); from collections import Counter
  counts=Counter(row[5] for row in cases); self.assertEqual(counts,{"FULL_FRAME":16,"DECLARED_FOCUS":16,"REFUSE":27632})
  for _,_,_,_,full_size,decision,evidence in cases:
   if decision=="DECLARED_FOCUS": self.assertLess(len(load("auditor").canonical(evidence)),full_size)
 def test_full_and_focus_regions_are_disjoint_from_distractor(self):
  candidate=load("candidate"); a=candidate.make_frame(4,"window-A","focus-live",0,self.design); b=candidate.make_frame(4,"window-A","focus-live",1,self.design)
  for name,region in a["regions"].items():
   x0,y0,x1,y1=region["bounds"]
   self.assertEqual([[a["pixels"][y][x] for x in range(x0,x1)] for y in range(y0,y1)],[[b["pixels"][y][x] for x in range(x0,x1)] for y in range(y0,y1)])
 def test_auditor_mutators_work_with_list_pixel_storage(self):
  auditor=load("auditor"); raw={"rows":[
   {"case_id":"frameX/FULL_FRAME","frame":"frameX","request":{"epoch":1},"frame_sha256":"f","result":{"decision":"FULL_FRAME","action_authorized":False,"evidence":{"pixels":[[1,2],[3,4]]}}},
   {"case_id":"frameX/MATRIX/1","frame":"frameX","request":{"epoch":1},"frame_sha256":"f","result":{"decision":"DECLARED_FOCUS","action_authorized":False,"evidence":{"pixels":[[5,6],[7,8]]}}},
   {"case_id":"frameX/MATRIX/2","frame":"frameX","request":{"epoch":0},"frame_sha256":"f","result":{"decision":"REFUSE","action_authorized":False}}]}
  for name,mutate,_ in auditor.mutation_cases(raw):
   altered=copy.deepcopy(raw); mutate(altered); self.assertNotEqual(altered,raw,name)
  cropped=copy.deepcopy(raw); dict((n,m) for n,m,_ in auditor.mutation_cases(raw))["corrupt-focused-pixels"](cropped)
  self.assertEqual(cropped["rows"][1]["result"]["evidence"]["pixels"][0][0],6)
 def test_mutation_detection_requires_a_new_specific_error(self):
  audit=load("auditor"); self.assertTrue(audit.detects_new_error(set(),["frame-hash:3"],"frame-hash:")); self.assertFalse(audit.detects_new_error({"frame-hash:3"},["frame-hash:3"],"frame-hash:"))
 def test_action_authority_is_disabled_in_design(self): self.assertIs(self.design["action_authorized"],False)
if __name__=="__main__": unittest.main()
