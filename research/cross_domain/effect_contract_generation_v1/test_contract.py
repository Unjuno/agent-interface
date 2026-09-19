import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent; EXP=ROOT/'experiment.py'; AUD=ROOT/'audit.py'
class T(unittest.TestCase):
 def run_case(self,policy,scenario):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td); p=t/'p.json'; o=t/'o'; p.write_text(json.dumps({'cases':[{'id':'x','policy':policy,'scenario':scenario}]})+'\n')
   subprocess.run([sys.executable,str(EXP),str(p),str(o)],check=True)
   r=json.loads((o/'x'/'result.json').read_text()); a=json.loads(subprocess.run([sys.executable,str(AUD),str(o)],check=True,text=True,capture_output=True).stdout)
   return r,a
 def test_stable_both_incomplete(self):
  for policy in ['latest_contract','effect_bound']:
   r,a=self.run_case(policy,'stable'); self.assertEqual(r['outcome'],'COMPENSATION_INCOMPLETE'); self.assertTrue(r['ground_truth_correct'])
 def test_pre_effect_update_accepted(self):
  for policy in ['latest_contract','effect_bound']:
   r,a=self.run_case(policy,'pre_effect_narrow'); self.assertEqual(r['outcome'],'COMPENSATION_COMPLETE'); self.assertTrue(r['ground_truth_correct'])
 def test_post_effect_latest_launders(self):
  r,a=self.run_case('latest_contract','post_effect_narrow'); self.assertEqual(r['outcome'],'COMPENSATION_COMPLETE'); self.assertFalse(r['ground_truth_correct'])
 def test_post_effect_bound_rejects(self):
  r,a=self.run_case('effect_bound','post_effect_narrow'); self.assertEqual(r['outcome'],'COMPENSATION_INCOMPLETE'); self.assertTrue(r['ground_truth_correct'])
 def test_audit_integrity(self):
  r,a=self.run_case('effect_bound','stable'); self.assertTrue(a['all_integrity'])
if __name__=='__main__': unittest.main()
