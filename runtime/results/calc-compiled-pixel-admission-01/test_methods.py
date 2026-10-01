import unittest
from unittest.mock import patch
from PIL import Image
from pathlib import Path
import hashlib
from runtime.guarded_x11_v1.test_compiled import Bridge
import methods

class AdmissionTests(unittest.TestCase):
 def exercise(self,values):
  b=Bridge();b._focus_within_target=lambda:b.phase<2
  b.out=Path('.');b.focused_client_window=lambda:20 if b.phase<2 else 21
  original=b.observe
  def observe():
   n=original();image=Image.new('RGB',(32,32),(0,20,30));image.putpixel((0,0),(b.phase,20,30))
   n['native']['artifact'].update(path='fake-image.png',sha256=hashlib.sha256(image.tobytes()).hexdigest())
   b.history[n['sequence']]=(n,image);return n
  b.observe=observe
  rgb=Image.new('RGB',(32,32),(0,20,30))
  refs={'sheet-context':{'offset':[2,2],'box':[2,2,10,10],'pixels':rgb.crop([2,2,10,10]).tobytes()}}
  def reading(image,regions,out):
   vals=[None,None] if b.phase==0 else values
   return {name:{'value':value} for name,value in zip(('A1','A2'),vals)}
  with patch.object(methods,'read_cells',side_effect=reading):
   return b,methods.run(b,refs,{'A1':[1,1,2,2],'A2':[2,2,3,3]})
 def test_correct_intermediate_cells_select_save_but_do_not_certify_saved_effect(self):
  b,r=self.exercise(['317','529'])
  self.assertEqual(len(b.inputs),2)
  self.assertEqual((r['receipt']['outcome'],r['receipt']['reason']),('SAFE_YIELD','effect_unavailable'))
  self.assertEqual(r['receipt']['pending_effect']['action'],'save')
  self.assertEqual(r['receipt']['completed_transitions'],2)
  self.assertIsNone(r['task_success'])
 def test_wrong_intermediate_cell_stops_before_save(self):
  b,r=self.exercise(['318','529'])
  self.assertEqual(len(b.inputs),1)
  self.assertEqual(r['receipt']['reason'],'effect_failed')
 def test_unknown_intermediate_cell_stops_before_save(self):
  b,r=self.exercise([None,'529'])
  self.assertEqual(len(b.inputs),1)
  self.assertEqual(r['receipt']['reason'],'effect_unavailable')
 def test_boolean_is_not_exact_visible_text(self):
  b,r=self.exercise([True,'529'])
  self.assertEqual(len(b.inputs),1)
  self.assertEqual(r['receipt']['reason'],'effect_failed')
if __name__=='__main__':unittest.main()
