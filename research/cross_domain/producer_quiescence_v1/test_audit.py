import copy,json,shutil,tempfile,unittest,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit
ROOT=Path(os.environ.get('PRODUCER_QUIESCENCE_EVIDENCE_ROOT','/mnt/data/ffmpeg_retry_quiescence_20260916'))
class AuditMutation(unittest.TestCase):
    def fresh(self):
        td=tempfile.TemporaryDirectory();dst=Path(td.name)/'x';shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('.git','producer_quiescence_evidence.tar.xz'))
        return td,dst
    def rejects(self,mut):
        td,r=self.fresh()
        try:
            mut(r)
            with self.assertRaises(Exception):audit.main(r)
        finally:td.cleanup()
    def test_control(self):
        td,r=self.fresh()
        try:self.assertEqual(audit.main(r)['cases'],16)
        finally:td.cleanup()
    def test_release_mutation(self):
        def m(r):
            p=r/'evidence/r1-immediate/final-input.json';x=json.loads(p.read_text());x['empty']=False;p.write_text(json.dumps(x))
        self.rejects(m)
    def test_process_order_mutation(self):
        def m(r):
            p=r/'evidence/r1-immediate/process.json';x=json.loads(p.read_text());x['a_reaped_ns']=x['b_spawned_ns']-1;p.write_text(json.dumps(x))
        self.rejects(m)
    def test_after_b_image_mutation(self):
        def m(r):
            src=r/'evidence/r1-immediate/final.png';dst=r/'evidence/r1-immediate/after_b.png';dst.write_bytes(src.read_bytes())
        self.rejects(m)
    def test_final_image_mutation(self):
        def m(r):
            src=r/'evidence/r1-immediate/after_b.png';dst=r/'evidence/r1-immediate/final.png';dst.write_bytes(src.read_bytes())
        self.rejects(m)
    def test_plan_pin_mutation(self):
        def m(r):
            p=r/'research/cross_domain/producer_quiescence_v1/contract.py';p.write_text(p.read_text()+'\n# corrupt\n')
        self.rejects(m)
if __name__=='__main__':unittest.main()
