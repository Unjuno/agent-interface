import json,tempfile,shutil,unittest
from pathlib import Path
from verify import verify
ROOT=Path(__file__).resolve().parent
class AuditTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  files=json.loads((ROOT/'FROZEN.json').read_text())['files']
  for name in [*files,'FROZEN.json']:shutil.copyfile(ROOT/name,self.root/name)
  for case in ['normal-compiled','short-compiled']:
   for path in (ROOT/case).rglob('*'):
    if path.is_file() and path.suffix in ['.json','.png','.svg'] and not any(x in path.parts for x in ['home','config','cache','data','run','__pycache__']):
     dest=self.root/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
  self.case=self.root/'normal-compiled';owner=json.loads((self.case/'owner.json').read_text());self.bridge=self.case/owner['bridge_relative']
 def change(self,path,fn):
  d=json.loads(path.read_text());fn(d);path.write_text(json.dumps(d))
 def test_original(self):self.assertEqual(verify(self.root)['status'],'PASS_RETAINED_COMPOSITION_MECHANICS')
 def test_activation_request_must_be_recorded(self):
  self.change(self.case/'activation-result.json',lambda d:d['result']['execution']['activations'][0].update(request_attempted=False))
  with self.assertRaisesRegex(ValueError,'confirmed WM'):verify(self.root)
 def test_mint_from_old_scope_observation_refused(self):
  self.change(self.case/'public/003-raw.json',lambda d:d.update(source_sequence=1))
  with self.assertRaisesRegex(ValueError,'grounding'):verify(self.root)
 def test_extra_save_in_control(self):
  c=self.root/'short-compiled';owner=json.loads((c/'owner.json').read_text());bridge=c/owner['bridge_relative'];path=next(x for x in bridge.glob('program-guarded-*.json') if any(op['op']=='key_chord' for op in json.loads(x.read_text())['ops']))
  self.change(path,lambda d:d['ops'].append({'op':'key_chord','keys':['CTRL','s']}))
  with self.assertRaisesRegex(ValueError,'Save gate'):verify(self.root)
 def test_false_selection_prefix(self):
  self.change(self.case/'owner-compiled-result.json',lambda d:d['method_receipt']['observations'][1]['predicates'].update(selected_shape=False))
  with self.assertRaisesRegex(ValueError,'selection gates'):verify(self.root)
 def test_returned_image_bytes_not_reference_only(self):
  self.change(self.case/'owner-compiled-result.json',lambda d:d['feedback']['image'].update(data='AAAA'))
  with self.assertRaisesRegex(ValueError,'returned image bytes'):verify(self.root)
 def test_persistence_independent_of_success_receipt(self):
  (self.case/'two-rectangles.svg').write_text('modified')
  with self.assertRaisesRegex(ValueError,'saved bytes'):verify(self.root)
 def test_actual_capture_corruption(self):
  artifact=json.loads(next(self.bridge.glob('public-observation-*.json')).read_text())['observation']['artifact'];path=self.case/artifact['path'].split('/normal-compiled/',1)[1];path.write_bytes(b'corrupt')
  with self.assertRaisesRegex(ValueError,'PNG identity'):verify(self.root)
 def test_close_release_required(self):
  self.change(self.case/'public/005-raw.json',lambda d:d['release'].update(verified=False))
  with self.assertRaisesRegex(ValueError,'terminal release'):verify(self.root)
if __name__=='__main__':unittest.main()
