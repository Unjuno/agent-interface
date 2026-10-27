#!/usr/bin/env python3
"""Pre-freeze construction coverage checks; does not invoke formal candidate/auditor."""
import json,pathlib,unittest
PKG=pathlib.Path(__file__).resolve().parent
class Construction(unittest.TestCase):
 def setUp(self): self.d=json.loads((PKG/"design.json").read_text())
 def test_exact_finite_scope(self): self.assertEqual(len(self.d["frames"])*len(self.d["requests"]),22)
 def test_required_contract_boundaries(self): self.assertEqual(set(self.d["required_cases"]),{r["case"] for r in self.d["requests"]})
 def test_positive_and_negative_controls_present(self):
  names={r["case"] for r in self.d["requests"]}; self.assertIn("full-frame-exact",names); self.assertIn("declared-focus-exact",names); self.assertTrue({"stale-epoch","replaced-identity","focus-lost","ambiguous-candidates","out-of-bounds","empty-region"}<=names)
 def test_distractor_mutation_is_outside_declared_region(self):
  a,b=self.d["frames"]; bounds=a["regions"]["target"]["bounds"]; x0,y0,x1,y1=bounds
  for y in range(len(a["pixels"])):
   for x in range(len(a["pixels"][y])):
    if x0<=x<x1 and y0<=y<y1: self.assertEqual(a["pixels"][y][x],b["pixels"][y][x])
    else: self.assertNotEqual(a["pixels"][y][x],b["pixels"][y][x])
 def test_focused_output_has_no_authority_flag_in_design(self): self.assertIs(self.d["action_authorized"],False)
 def test_invalid_regions_are_represented_as_geometry_faults(self):
  f=self.d["frames"][0]; self.assertEqual(f["regions"]["outside"]["bounds"],[7,7,9,9]); self.assertEqual(f["regions"]["empty"]["bounds"],[3,3,3,4])
if __name__=="__main__": unittest.main()
