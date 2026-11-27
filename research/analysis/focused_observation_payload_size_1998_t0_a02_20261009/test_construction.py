"""Pre-freeze fixture checks; no formal result is written."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def import_module(name):
 s=importlib.util.spec_from_file_location(name,ROOT/(name+'.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
candidate=import_module('candidate'); auditor=import_module('auditor')
class Construction(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/'design.json').read_text()); self.pix=(ROOT/'source/frame.bin').read_bytes()
 def test_fixture_has_nine_valid_sizes_and_five_invalid_controls(self):
  self.assertEqual(len(self.d['scenarios']),14); self.assertEqual(len(self.pix),4096)
 def test_candidate_exactly_reconstructs_and_uses_fallback(self):
  raw=candidate.run(self.d,self.pix); errors,expected=auditor.validate(raw,self.d,self.pix)
  self.assertEqual(errors,[]); self.assertEqual(len([r for r in expected if r['focused_payload']]),9)
  self.assertEqual(len([r for r in expected if r['focused_payload'] is None]),5)
  self.assertTrue(any(r['bytes_saved_vs_full']>0 for r in expected))
  self.assertTrue(all(r['selected_kind']=='FULL_FRAME' for r in expected if r['focused_payload'] is None))
  self.assertTrue(all(r['selected_kind']=='FULL_FRAME' for r in expected if r['focused_bytes'] is not None and r['focused_bytes']>=r['full_frame_bytes']))
 def test_crop_bytes_and_metadata_are_counted(self):
  raw=candidate.run(self.d,self.pix); errors,exp=auditor.validate(raw,self.d,self.pix); self.assertFalse(errors)
  self.assertEqual(sum(r['full_frame_bytes'] for r in exp),sum(len(candidate.canonical(r['full_frame_payload'])) for r in raw['rows']))
  self.assertGreater(sum(r['selected_bytes'] for r in exp),0)
 def test_independent_mutation_controls_reject_changes(self):
  raw=candidate.run(self.d,self.pix)
  muts=[
   lambda x:x['rows'][0]['focused_payload'].__setitem__('pixels_b64','AAAA'),
   lambda x:x['rows'][9].__setitem__('selected_kind','FOCUSED_REGION'),
   lambda x:x['rows'][0]['focused_payload'].__setitem__('region_id','other'),
   lambda x:x['rows'][13].__setitem__('decision','FOCUSED_REGION_SELECTED'),
   lambda x:x['rows'][7].__setitem__('selected_kind','FOCUSED_REGION'),
   lambda x:x['rows'][0].__setitem__('selected_bytes',1),
  ]
  for mutate in muts:
   changed=json.loads(json.dumps(raw)); mutate(changed); self.assertTrue(auditor.validate(changed,self.d,self.pix)[0])
if __name__=='__main__': unittest.main()
