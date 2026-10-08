"""Offline prefreeze checks of the real-artifact analyzer and declared controls."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
import runner

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        shutil.copytree(runner.ROOT/'evidence/preflight02/runtime',self.root/'runtime')
    def tearDown(self):self.tmp.cleanup()
    def edit(self,name,fn):
        p=self.root/'runtime'/name
        if name.endswith('jsonl'):
            rs=runner.rows(p);fn(rs);p.write_text(''.join(json.dumps(x)+'\n' for x in rs))
        else:
            obj=json.loads(p.read_text());fn(obj);runner.dump(p,obj)
    def check_fail(self,k):self.assertFalse(runner.analyze(self.root,'preflight')['gates'][k])
    def test_real_preflight_pass(self):self.assertTrue(runner.analyze(self.root,'preflight')['pass_hard_gates'])
    def test_delivery_divergence(self):
        self.edit('delivered.jsonl',lambda r:r.pop());self.check_fail('delivery_exact')
    def test_wrong_score(self):
        self.edit('score.json',lambda d:d.update(kill_count=99));self.check_fail('terminal_agreement')
    def test_bool_not_int(self):
        self.edit('score.json',lambda d:d.update(kill_count=False));self.check_fail('terminal_agreement')
    def test_source_digest(self):
        self.edit('sources.json',lambda d:d.update({'doom/session_map01_v12.py':'0'*64}));self.check_fail('source_hashes')
    def test_controller_leak(self):
        self.edit('events.jsonl',lambda r:r.append({'schema':'independent-progress-event-v2'}));self.check_fail('scorer_not_controller_visible')
    def test_unverified_release(self):
        def change(rs):
            t=next(r for r in rs if r.get('event')=='terminal');t['interruption']['record']['verified']=False
        self.edit('events.jsonl',change);self.check_fail('release_empty')
    def test_nonempty_release(self):
        def change(rs):
            t=next(r for r in rs if r.get('event')=='terminal');t['interruption']['record']['keys_down']=[38]
        self.edit('events.jsonl',change);self.check_fail('release_empty')
    def test_timing_units(self):
        r=runner.analyze(self.root,'preflight')
        self.assertAlmostEqual(r['deadline_to_empty_ms']*1e6,r['verified_empty_ns']-r['deadline_ns'])
    def test_no_kill_not_positive(self):self.assertFalse(runner.analyze(self.root,'preflight')['useful_observed_before_deadline'])
    def test_explicit_bindings(self):
        text=(runner.RUNTIME/'research/doom/session_map01_v12.py').read_text()
        for binding in ['s=+back','a=+moveleft','d=+moveright','space=+attack']:self.assertIn(binding,text)
        self.assertEqual(runner.POLICIES['back_left'][0]['keys'],['s','a','space'])
    def test_both_phase_holds_within_total_budget(self):
        for steps in runner.POLICIES.values():self.assertLessEqual(sum(x['duration_ms'] for x in steps),10000)
if __name__=='__main__':unittest.main()
