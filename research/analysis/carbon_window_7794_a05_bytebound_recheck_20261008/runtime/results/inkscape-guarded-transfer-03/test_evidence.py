import unittest,tempfile,pathlib,shutil,json
import verify
class EvidenceTests(unittest.TestCase):
 def test_original_failed_task_evidence_passes(self):
  self.assertEqual(verify.verify()['normal_task_successes'],0)
 def mutated(self,path,change):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d)/'evidence';shutil.copytree(verify.ROOT,r,ignore=shutil.ignore_patterns('__pycache__','home','config','cache','data','run'))
   p=r/path;j=json.loads(p.read_text());change(j);p.write_text(json.dumps(j))
   with self.assertRaises(ValueError):verify.verify(r)
 def test_fabricated_success_is_rejected(self):
  self.mutated('positive-ordinary/evaluation.json',lambda j:j.update(success=True))
 def test_missing_release_verification_is_rejected(self):
  self.mutated('positive-compiled/replies/004.json',lambda j:j['reply']['release'].update(verified=False))
 def test_wrong_emission_count_is_rejected(self):
  self.mutated('positive-ordinary/method-inputs.json',lambda j:j[0]['execution'].update(program_emissions=0))
 def test_extra_input_program_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d)/'evidence';shutil.copytree(verify.ROOT,r,ignore=shutil.ignore_patterns('__pycache__','home','config','cache','data','run'))
   (r/'positive-ordinary/bridge/program-extra.json').write_text('{}')
   with self.assertRaises(ValueError):verify.verify(r)
 def test_tampered_original_image_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d)/'evidence';shutil.copytree(verify.ROOT,r,ignore=shutil.ignore_patterns('__pycache__','home','config','cache','data','run'))
   p=next((r/'positive-ordinary/bridge/images').glob('df40*.png'));p.write_bytes(b'changed')
   with self.assertRaises(ValueError):verify.verify(r)
if __name__=='__main__':unittest.main()
