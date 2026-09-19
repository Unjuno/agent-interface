"""Corruption tests on a COPY of the retained real-engine preflight, no live input."""
import json, os, shutil, tempfile, unittest
from pathlib import Path
from audit import analyze

class Tests(unittest.TestCase):
    def setUp(self):
        source=os.environ.get('AI_PREFLIGHT')
        if not source:self.skipTest('set AI_PREFLIGHT to the retained preflight-02 directory')
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'case'
        shutil.copytree(source,self.root)
    def tearDown(self):
        if hasattr(self,'temp'):self.temp.cleanup()
    def mutate(self,name,fn):
        p=self.root/'runtime'/name
        arr=[json.loads(s) for s in p.read_text().splitlines()]
        fn(arr);p.write_text(''.join(json.dumps(r)+'\n' for r in arr))
    def bad(self):self.assertFalse(analyze(self.root)['hard_pass'])
    def test_valid(self):self.assertTrue(analyze(self.root)['hard_pass'])
    def test_final_clock(self):
        self.mutate('scorer-samples.jsonl',lambda a:a[-1].update(sample_started_ns=a[-1]['payload']['sample_ns']+1));self.bad()
    def test_missing_final(self):
        self.mutate('scorer-samples.jsonl',lambda a:a[-1].pop('direct_final_sample'));self.bad()
    def test_final_duplicate(self):
        self.mutate('scorer-samples.jsonl',lambda a:a.append(a[-1]));self.bad()
    def test_score_type(self):
        p=self.root/'runtime/score.json';a=json.loads(p.read_text());a['map_exit']=0;p.write_text(json.dumps(a));self.bad()
    def test_release_corruption(self):
        self.mutate('events.jsonl',lambda a:next(r for r in a if r.get('event')=='terminal')['release'].update(keys_down=[1]));self.bad()
    def test_program_hash(self):
        self.mutate('events.jsonl',lambda a:next(r for r in a if r.get('event')=='accepted').update(program_sha256='0'*64));self.bad()
    def test_wrong_cause(self):
        self.mutate('events.jsonl',lambda a:next(r for r in a if r.get('event')=='terminal')['interruption'].update(intent_token='other'));self.bad()
    def test_thread(self):
        self.mutate('acquisitions.jsonl',lambda a:a[0].update(thread_id=-1));self.bad()
    def test_forged_diagnostic(self):
        self.mutate('acquisitions.jsonl',lambda a:a[0]['sample'].update(kill_count=9));self.bad()
    def test_leak(self):
        self.mutate('events.jsonl',lambda a:a.insert(0,{'event':'leak','kill_count':2}));self.bad()
    def test_truncated_diagnostic(self):
        self.mutate('acquisitions.jsonl',lambda a:a.pop());self.bad()
if __name__=='__main__':unittest.main()
