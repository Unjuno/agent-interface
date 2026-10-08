import json,shutil,tempfile,unittest
from pathlib import Path
from verify import verify,ROOT
class FailureEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)/'copy';shutil.copytree(ROOT,self.p,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'))
 def tearDown(self):self.t.cleanup()
 def mutate(self,path,fn):
  p=self.p/path;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 def rejects(self):
  with self.assertRaises(ValueError):verify(self.p)
 def test_original_failure_preserved(self):self.assertFalse(verify(self.p)['primary_end_to_end_success'])
 def test_presentation_failure_cannot_be_relabeled_success(self):
  self.mutate('normal-ordinary/replies/003.json',lambda v:v['reply'].update(image_status='image'));self.rejects()
 def test_censored_denominator_not_removed(self):
  self.mutate('DISPOSITION.json',lambda v:v.update(cases=v['cases'][:1]));self.rejects()
 def test_neutral_release_required(self):
  self.mutate('normal-ordinary/replies/004.json',lambda v:v['reply']['release'].update(verified=False));self.rejects()
if __name__=='__main__':unittest.main()
