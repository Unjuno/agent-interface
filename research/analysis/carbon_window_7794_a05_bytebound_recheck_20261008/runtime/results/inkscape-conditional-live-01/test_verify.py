import pathlib,tempfile,shutil,json,unittest
import verify
ROOT=pathlib.Path(__file__).resolve().parent
class AuditTests(unittest.TestCase):
 def make_copy(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);out=pathlib.Path(temp.name)/'study';out.mkdir()
  for p in ROOT.glob('*'):
   if p.is_file():shutil.copy2(p,out/p.name)
  for row in json.loads((ROOT/'schedule.json').read_text()):
   source=ROOT/row['case'];target=out/row['case'];shutil.copytree(source,target,ignore=shutil.ignore_patterns('home','config','cache','data','run'))
  return out
 def mutate(self,relative,change):
  root=self.make_copy();p=root/relative;row=json.loads(p.read_text());change(row);p.write_text(json.dumps(row))
  with self.assertRaises(ValueError):verify.verify(root)
 def test_positive(self):self.assertEqual(verify.verify()['status'],'PASS')
 def test_unverified_release(self):self.mutate('positive-ordinary/method-dispatch-1.json',lambda x:x['raw']['result']['execution']['releases'][0].update(verified=False))
 def test_wrong_source_sequence(self):self.mutate('positive-compiled/method-dispatch-2.json',lambda x:x['program']['source'].update(observation_seq=999))
 def test_negative_save_claim(self):self.mutate('unknown-ordinary/method-common.json',lambda x:x.update(save_dispatched=True))
 def test_primary_image_mismatch(self):self.mutate('unknown-compiled/replies/002.json',lambda x:x['reply']['image_reference'].update(sha256='0'*64))
 def test_false_terminal(self):self.mutate('positive-compiled/cleanup.json',lambda x:x.update(all_owned_processes_terminal=False))
 def test_frozen_caller_change(self):
  root=self.make_copy();p=root/'methods.py';p.write_text(p.read_text()+'\n# changed\n')
  with self.assertRaises(ValueError):verify.verify(root)
if __name__=='__main__':unittest.main()
