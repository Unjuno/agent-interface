import threading,unittest
from types import SimpleNamespace
from gate import LifecycleGate,observe_and_cancel

class FakeExecutor:
    def __init__(self):self.lock=threading.RLock();self.active=('p',SimpleNamespace(intent_token='t'),None);self.calls=[]
    def cancel(self,i):self.calls.append(i);return True

class Tests(unittest.TestCase):
    def test_fresh_delivery_and_source_admits(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.require_open('e',now_ns=350)
    def test_fresh_delivery_stalled_source_rejects(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.observe(epoch='e',sequence=1,ended=False,observed_ns=350,source_generation=5)
        with self.assertRaisesRegex(ValueError,'source generation stale'):g.require_open('e',now_ns=401)
        self.assertFalse(g.ended)
    def test_source_advance_refreshes_progress(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.observe(epoch='e',sequence=1,ended=False,observed_ns=390,source_generation=6);g.require_open('e',now_ns=600)
    def test_timestamp_only_allows_fresh_false_running(self):
        g=LifecycleGate('e',300,None);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.observe(epoch='e',sequence=1,ended=False,observed_ns=1000,source_generation=5);g.require_open('e',now_ns=1100)
    def test_delivery_stale_still_rejects(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5)
        with self.assertRaisesRegex(ValueError,'delivery stale'):g.require_open('e',now_ns=401)
    def test_terminal_dominates(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=True,observed_ns=100,source_generation=5)
        with self.assertRaisesRegex(ValueError,'ended'):g.require_open('e',now_ns=101)
    def test_source_regression_rejects(self):
        g=LifecycleGate('e');g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5)
        with self.assertRaisesRegex(ValueError,'source generation regression'):g.observe(epoch='e',sequence=1,ended=False,observed_ns=101,source_generation=4)
    def test_duplicate_must_match_source(self):
        g=LifecycleGate('e');g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5)
        with self.assertRaisesRegex(ValueError,'conflicting'):g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=6)
    def test_foreign_epoch_ignored(self):
        g=LifecycleGate('e',300,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5)
        self.assertFalse(g.observe(epoch='old',sequence=1,ended=True,observed_ns=120,source_generation=9));g.require_open('e',now_ns=200)
    def test_terminal_cancels_once(self):
        g=LifecycleGate('e');e=FakeExecutor();observe_and_cancel(e,g,epoch='e',sequence=0,ended=True,observed_ns=10,source_generation=5);observe_and_cancel(e,g,epoch='e',sequence=0,ended=True,observed_ns=10,source_generation=5);self.assertEqual(e.calls,['p'])
    def test_stall_never_cancels(self):
        g=LifecycleGate('e',300,300);e=FakeExecutor();g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.observe(epoch='e',sequence=1,ended=False,observed_ns=500,source_generation=5)
        with self.assertRaises(ValueError):g.require_open('e',now_ns=501)
        self.assertEqual(e.calls,[])
    def test_invalid_thresholds(self):
        for args in [(0,None),(-1,None),(True,None),(None,0),(None,1.5)]:
            with self.subTest(args=args),self.assertRaises(ValueError):LifecycleGate('e',*args)
    def test_terminal_cannot_revive(self):
        g=LifecycleGate('e');g.observe(epoch='e',sequence=0,ended=True,observed_ns=10,source_generation=5)
        with self.assertRaises(ValueError):g.observe(epoch='e',sequence=1,ended=False,observed_ns=11,source_generation=6)
    def test_exact_progress_boundary_is_fresh(self):
        g=LifecycleGate('e',None,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5);g.require_open('e',now_ns=400)
    def test_one_ns_past_progress_boundary_stale(self):
        g=LifecycleGate('e',None,300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100,source_generation=5)
        with self.assertRaises(ValueError):g.require_open('e',now_ns=401)
if __name__=='__main__':unittest.main()
