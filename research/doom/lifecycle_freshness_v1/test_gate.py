import threading,unittest
from types import SimpleNamespace
from gate import LifecycleGate,observe_and_cancel

class FakeExecutor:
    def __init__(self):self.lock=threading.RLock();self.active=('p',SimpleNamespace(intent_token='t'),None);self.calls=[]
    def cancel(self,i):self.calls.append(i);return True

class Tests(unittest.TestCase):
    def test_running_fresh(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100);g.require_open('e',now_ns=350)
    def test_running_stale_blocks_new_only(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100)
        with self.assertRaisesRegex(ValueError,'stale'):g.require_open('e',now_ns=401)
        self.assertFalse(g.ended)
    def test_unavailable_blocks_when_freshness_required(self):
        with self.assertRaisesRegex(ValueError,'unavailable'):LifecycleGate('e',300).require_open('e',now_ns=1)
    def test_no_freshness_keeps_old_behavior(self):LifecycleGate('e',None).require_open('e',now_ns=10**9)
    def test_terminal_dominates_freshness(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=True,observed_ns=100)
        with self.assertRaisesRegex(ValueError,'ended'):g.require_open('e',now_ns=101)
    def test_foreign_terminal_ignored(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100)
        self.assertFalse(g.observe(epoch='old',sequence=1,ended=True,observed_ns=120));g.require_open('e',now_ns=200)
    def test_clock_regression_at_admission(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100)
        with self.assertRaisesRegex(ValueError,'clock regression'):g.require_open('e',now_ns=99)
    def test_delayed_terminal_cancels_only_on_delivery(self):
        g=LifecycleGate('e',300);e=FakeExecutor();g.observe(epoch='e',sequence=0,ended=False,observed_ns=100)
        self.assertEqual(e.calls,[])
        r=observe_and_cancel(e,g,epoch='e',sequence=1,ended=True,observed_ns=200,delivered_ns=700,clock_ns=lambda:701)
        self.assertEqual(e.calls,['p']);self.assertTrue(r['cancel_matched']);self.assertEqual(r['lifecycle_delivered_ns'],700)
    def test_duplicate_terminal_one_cancel(self):
        g=LifecycleGate('e');e=FakeExecutor()
        observe_and_cancel(e,g,epoch='e',sequence=0,ended=True,observed_ns=10)
        observe_and_cancel(e,g,epoch='e',sequence=0,ended=True,observed_ns=10)
        self.assertEqual(e.calls,['p'])
    def test_terminal_cannot_revive(self):
        g=LifecycleGate('e');g.observe(epoch='e',sequence=0,ended=True,observed_ns=10)
        with self.assertRaises(ValueError):g.observe(epoch='e',sequence=1,ended=False,observed_ns=11)
    def test_invalid_freshness(self):
        for x in (0,-1,True,1.5):
            with self.subTest(x=x),self.assertRaises(ValueError):LifecycleGate('e',x)
    def test_exact_boundary_is_fresh(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100);g.require_open('e',now_ns=400)
    def test_one_ns_past_boundary_stale(self):
        g=LifecycleGate('e',300);g.observe(epoch='e',sequence=0,ended=False,observed_ns=100)
        with self.assertRaises(ValueError):g.require_open('e',now_ns=401)

if __name__=='__main__':unittest.main()
