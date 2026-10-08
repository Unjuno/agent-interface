import json,shutil,tempfile,unittest
from pathlib import Path
from verify import verify,ROOT
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'copy'
  shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'))
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,relative,fn):
  p=self.root/relative;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 def rejected(self):
  with self.assertRaises(ValueError):verify(self.root)
 def test_original(self):self.assertEqual(verify(self.root)['normal_tasks_succeeded'],2)
 def test_selection_effect_must_be_proven(self):
  self.mutate('normal-compiled/method-trace.json',lambda v:v[1]['predicates'].update(selected_shape=False));self.rejected()
 def test_graph_effect_history_not_just_success_label(self):
  self.mutate('normal-compiled/method-raw.json',lambda v:v.update(critical_events=[e for e in v['critical_events'] if e['event']!='effect_checked']));self.rejected()
 def test_missing_pending_movement_not_hidden(self):
  self.mutate('short-compiled/method-raw.json',lambda v:v.update(pending_effect=None));self.rejected()
 def test_input_inventory_must_match_native_raw(self):
  self.mutate('normal-ordinary/method-inputs.json',lambda v:v[0]['execution'].update(program_emissions=0));self.rejected()
 def test_unverified_close_release(self):
  self.mutate('normal-compiled/replies/005.json',lambda v:v['reply']['release'].update(verified=False));self.rejected()
 def test_extra_control_save_is_rejected(self):
  p=next((self.root/'short-ordinary/bridge').glob('program-*.json'));v=json.loads(p.read_text());v['ops'].append({'op':'key_chord','keys':['CTRL','s']});p.write_text(json.dumps(v));self.rejected()
 def test_wrong_pointer_endpoint_is_rejected(self):
  for p in (self.root/'normal-ordinary/bridge').glob('program-*.json'):
   v=json.loads(p.read_text())
   if any(x['op']=='pointer_move' for x in v['ops']):
    for x in v['ops']:
     if x['op']=='pointer_move':x['x']=338
    p.write_text(json.dumps(v));break
  self.rejected()
 def test_wrong_saved_geometry_is_rejected(self):
  p=self.root/'normal-compiled/two-rectangles.svg';p.write_text(p.read_text().replace('x="80"','x="60"'));self.rejected()
if __name__=='__main__':unittest.main()
