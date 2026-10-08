#!/usr/bin/env python3
"""Construction checks only; no OCR invocation."""
import ast,pathlib,unittest
PKG=pathlib.Path(__file__).resolve().parent
class Construction(unittest.TestCase):
 def test_candidate_binds_tesseract_before_hash_identity_check(self):
  tree=ast.parse((PKG/"candidate.py").read_text()); main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main"); lines={n.id:n.lineno for n in ast.walk(main) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}; assigns=[n.lineno for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="tesseract" for t in n.targets)]; self.assertTrue(assigns); self.assertLess(min(assigns),lines["tesseract"])
 def test_candidate_only_has_crop_loop_no_full_control(self):
  s=(PKG/"candidate.py").read_text(); self.assertIn('"selected_kind"] == "FOCUSED_REGION"',s); self.assertNotIn("full_frame_control",s)
 def test_formal_wrapper_has_one_candidate_and_auditor_call_site(self):
  s=(PKG/"formal_runner.py").read_text(); self.assertEqual(s.count('"candidate.py"'),1); self.assertEqual(s.count('"auditor.py"'),1); self.assertIn('"retries":0',s)
if __name__=="__main__": unittest.main()
