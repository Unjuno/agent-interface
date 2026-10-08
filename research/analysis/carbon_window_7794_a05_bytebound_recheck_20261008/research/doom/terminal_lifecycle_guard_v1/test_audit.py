"""Post-hoc adversarial evidence tests; never mutate the retained first outcomes."""
import json,os,shutil,tempfile,unittest
from pathlib import Path
from audit import analyze
HERE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('EVIDENCE_ROOT',HERE/'missing-evidence'))

@unittest.skipUnless((DATA/'evidence/matched-0').is_dir(),'needs retained evidence')
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'case'
        shutil.copytree(DATA/'evidence/matched-0',self.root)
    def tearDown(self):self.tmp.cleanup()
    def mutate(self,name,fn):
        p=self.root/name;rs=[json.loads(s) for s in p.read_text().splitlines()];fn(rs)
        p.write_text(''.join(json.dumps(x)+'\n' for x in rs))
    def check_bad(self):
        self.assertFalse(analyze(self.root,DATA/'runtime-source',HERE)['integrity_pass'])
    def test_original(self):self.assertTrue(analyze(self.root,DATA/'runtime-source',HERE)['integrity_pass'])
    def test_bitmap_tamper(self):
        def change(rs):
            r=next(r for r in rs if r['down']);r['bitmap']=[0]*32
        self.mutate('runtime/keymap.jsonl',change);self.check_bad()
    def test_keymap_clock(self):
        self.mutate('runtime/keymap.jsonl',lambda r:r[0].update(finished_ns=0));self.check_bad()
    def test_final_bracket(self):
        self.mutate('runtime/scorer-samples.jsonl',lambda r:r[-1].update(sample_finished_ns=0));self.check_bad()
    def test_extra_final(self):
        self.mutate('runtime/scorer-samples.jsonl',lambda r:r[0].update(direct_final_sample=True));self.check_bad()
    def test_unverified_release(self):
        def change(rs):next(r for r in rs if r.get('event')=='terminal')['release']['verified']=False
        self.mutate('runtime/events.jsonl',change);self.check_bad()
    def test_wrong_intent(self):
        def change(rs):next(r for r in rs if r.get('event')=='input_admission')['intent_token']='other'
        self.mutate('runtime/events.jsonl',change);self.check_bad()
    def test_score_leak(self):
        self.mutate('runtime/events.jsonl',lambda r:r[0].update(kill_count=0));self.check_bad()
    def test_diag_outside(self):
        self.mutate('runtime/acquisitions.jsonl',lambda r:r[0].update(finished_ns=0));self.check_bad()
    def test_wrong_timeout_cause(self):
        self.mutate('runtime/acquisitions.jsonl',lambda r:r[-1].update(timeout_reached=False));self.check_bad()
    def test_wrong_program_hash(self):
        def change(rs):next(r for r in rs if r.get('event')=='accepted')['program_sha256']='0'*64
        self.mutate('runtime/events.jsonl',change);self.check_bad()

if __name__=='__main__':unittest.main()
