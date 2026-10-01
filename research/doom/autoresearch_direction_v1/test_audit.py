"""Post-hoc negative-control replay tests; never modify retained source data."""
import json,shutil,tempfile,unittest
from pathlib import Path
import audit,runner

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Path(self.tmp.name)
        (self.w/'source_runtime').symlink_to(runner.RUNTIME,target_is_directory=True)
        (self.w/'research').symlink_to(runner.ROOT/'research',target_is_directory=True)
        p=json.loads((runner.HERE/'plan_stage1.json').read_text());self.alloc=p['allocation'];self.spec=p['cases'][0]
        self.copy_case(self.alloc,self.spec)
    def copy_case(self,allocation,spec):
        dst=self.w/'evidence'/allocation/spec['id'];src=runner.ROOT/'evidence'/allocation/spec['id']
        shutil.copytree(src,dst,ignore=shutil.ignore_patterns('*.png','*.ait','*.bin'))
    def tearDown(self):self.tmp.cleanup()
    def rt(self):return self.w/'evidence'/self.alloc/self.spec['id']/'runtime'
    def mutate_events(self,fn):
        rs=audit.rows(self.rt()/'events.jsonl');fn(rs)
        text=''.join(json.dumps(r)+'\n' for r in rs)
        (self.rt()/'events.jsonl').write_text(text);(self.rt()/'delivered.jsonl').write_text(text)
    def fail(self):
        with self.assertRaises((ValueError,KeyError,StopIteration)):audit.audit_case(self.w,self.spec,self.alloc,False)
    def test_valid(self):self.assertTrue(audit.audit_case(self.w,self.spec,self.alloc,False)['pass'])
    def test_missing_down(self):
        self.mutate_events(lambda r:r.__delitem__(next(i for i,x in enumerate(r) if x.get('event')=='input_admission')));self.fail()
    def test_duplicate_down(self):
        self.mutate_events(lambda r:r.append(next(x for x in r if x.get('event')=='input_admission')));self.fail()
    def test_wrong_intent(self):
        self.mutate_events(lambda r:next(x for x in r if x.get('event')=='input_admission').update(intent_token='wrong'));self.fail()
    def test_deadline_changed(self):
        self.mutate_events(lambda r:next(x for x in r if x.get('event')=='accepted').update(valid_until_ns=1));self.fail()
    def test_unverified(self):
        self.mutate_events(lambda r:next(x for x in r if x.get('event')=='terminal')['release'].update(verified=False));self.fail()
    def test_privileged_before_finish(self):
        self.mutate_events(lambda r:r.insert(1,{'event':'hidden-leak','nested':{'kill_count':1}}));self.fail()
    def test_false_summary(self):
        p=self.rt().parent/'analysis.json';d=audit.load(p);d['useful_observed_before_deadline']=True;p.write_text(json.dumps(d));self.fail()
    def test_changed_source_hash(self):
        p=self.rt()/'sources.json';d=audit.load(p);d['doom/session_map01_v12.py']='0'*64;p.write_text(json.dumps(d));self.fail()
    def test_duplicated_final(self):
        p=self.rt()/'scorer-samples.jsonl';r=audit.rows(p);r.append(r[-1]);p.write_text(''.join(json.dumps(x)+'\n' for x in r));self.fail()
    def test_bool_score(self):
        p=self.rt()/'score.json';d=audit.load(p);d['death_count']=False;p.write_text(json.dumps(d));self.fail()
    def test_refresh_interval_inverted(self):
        p=audit.load(runner.HERE/'plan_stage3.json');self.alloc=p['allocation'];self.spec=p['cases'][1];self.copy_case(self.alloc,self.spec)
        f=self.rt()/'evaluator-trace.jsonl';r=audit.rows(f);r[0]['finished_ns']=0;f.write_text(''.join(json.dumps(x)+'\n' for x in r));self.fail()
if __name__=='__main__':unittest.main()
