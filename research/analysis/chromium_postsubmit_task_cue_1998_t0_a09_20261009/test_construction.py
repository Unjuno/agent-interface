#!/usr/bin/env python3
"""Pre-freeze construction guards; no Tesseract crop OCR is invoked."""
import ast,copy,json,pathlib,unittest
PKG=pathlib.Path(__file__).resolve().parent
class Construction(unittest.TestCase):
 def test_candidate_binds_tesseract_before_identity_hash_use(self):
  tree=ast.parse((PKG/"candidate.py").read_text()); main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
  loads=[n.lineno for n in ast.walk(main) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id=="tess"]
  assigns=[n.lineno for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="tess" for t in n.targets)]
  self.assertTrue(assigns); self.assertLess(min(assigns),min(loads))
 def test_candidate_iterates_only_fixed_focus_rows(self):
  s=(PKG/"candidate.py").read_text(); self.assertIn('r["selected_kind"]=="FOCUSED_REGION"',s); self.assertNotIn('selected_kind"]=="FULL_FRAME"',s)
 def test_formal_output_dir_is_created_at_formal_boundary(self):
  self.assertFalse((PKG/"results").exists()); tree=ast.parse((PKG/"formal_runner.py").read_text()); calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="mkdir"]
  self.assertEqual(len(calls),1); self.assertTrue(any(k.arg=="exist_ok" and isinstance(k.value,ast.Constant) and k.value.value is False for k in calls[0].keywords))
 def test_mutation_controls_are_type_safe_and_effective(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location("a09_auditor",PKG/"auditor.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
  raw={"rows":[{"case_id":"one","ocr_exit":0,"input_sha256":"a","payload_bytes":10,"ocr_text":"plain","ocr_stdout_b64":"cGxhaW4="},{"case_id":"two","ocr_exit":0,"input_sha256":"b","payload_bytes":20,"ocr_text":"other","ocr_stdout_b64":"b3RoZXI="}]}
  for name,mutate,_ in mod.mutations(raw):
   changed=copy.deepcopy(raw); mutate(changed); self.assertNotEqual(changed,raw,name)
  text=copy.deepcopy(raw); dict((n,m) for n,m,_ in mod.mutations(raw))["ocr-text-tamper"](text); self.assertIn("t001101",text["rows"][0]["ocr_text"])
 def test_no_formal_output_dir_precreated(self): self.assertFalse((PKG/"results").exists())
if __name__=="__main__": unittest.main()
