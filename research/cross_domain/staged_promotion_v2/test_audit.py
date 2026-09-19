import json,os,shutil,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent)); import audit
ROOT=Path(os.environ.get('STAGED_PROMOTION_EVIDENCE_ROOT','/mnt/data/staged_promotion_v2_20260916'))
class T(unittest.TestCase):
 def fresh(self):
  td=tempfile.TemporaryDirectory();dst=Path(td.name)/'x';shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('.git','staged_promotion_evidence.tar.xz'));return td,dst
 def rejects(self,fn):
  td,r=self.fresh()
  try:
   fn(r)
   with self.assertRaises(Exception):audit.main(r)
  finally:td.cleanup()
 def test_control(self):
  td,r=self.fresh()
  try:self.assertEqual(audit.main(r)['decision'],'RETAIN_GENERATION_GATE')
  finally:td.cleanup()
 def test_release(self):
  def m(r):
   p=r/'evidence/v2-r1-generation_gate/final-input.json';x=json.loads(p.read_text());x['empty']=False;p.write_text(json.dumps(x))
  self.rejects(m)
 def test_stale_event(self):
  def m(r):
   p=r/'evidence/v2-r1-generation_gate/publish-events.json';x=json.loads(p.read_text());x[1]['outcome']='PUBLISHED';p.write_text(json.dumps(x))
  self.rejects(m)
 def test_final_artifact(self):
  def m(r):
   d=r/'evidence/v2-r1-generation_gate';(d/'final.png').write_bytes((d/'a-stage-retained.png').read_bytes())
  self.rejects(m)
 def test_order(self):
  def m(r):
   p=r/'evidence/v2-r1-generation_gate/process.json';x=json.loads(p.read_text());x['a_reaped_ns']=x['b_reaped_ns']-1;p.write_text(json.dumps(x))
  self.rejects(m)
if __name__=='__main__':unittest.main()
