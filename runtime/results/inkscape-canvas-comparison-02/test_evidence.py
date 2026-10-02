import unittest,pathlib,tempfile,shutil,json
import verify
class EvidenceTests(unittest.TestCase):
 def test_original(self):self.assertEqual(len(verify.verify()['cases']),4)
 def mutate(self,name,fn):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'case';shutil.copytree(verify.ROOT,root,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'));p=root/name;j=json.loads(p.read_text());fn(j);p.write_text(json.dumps(j))
   with self.assertRaises(ValueError):verify.verify(root)
 def test_unverified_release(self):self.mutate('normal-compiled/replies/006.json',lambda j:j['reply']['release'].update(verified=False))
 def test_wrong_emissions(self):self.mutate('normal-ordinary/method-inputs.json',lambda j:j[0]['execution'].update(program_emissions=0))
 def test_missing_effect(self):self.mutate('normal-compiled/method-trace.json',lambda j:j[1]['predicates'].update(moved_shape=False))
 def test_false_negative_success(self):self.mutate('short-ordinary/evaluation.json',lambda j:j.update(success=True))
 def test_lost_pending_effect(self):self.mutate('short-compiled/method-raw.json',lambda j:j['pending_effect'].update(action='save'))
 def test_extra_save_program(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'case';shutil.copytree(verify.ROOT,root,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'));(root/'short-compiled/bridge/program-extra.json').write_text('{"ops":[]}')
   with self.assertRaises(ValueError):verify.verify(root)
if __name__=='__main__':unittest.main()
