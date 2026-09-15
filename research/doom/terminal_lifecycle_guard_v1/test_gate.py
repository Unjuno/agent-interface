import threading,unittest
from types import SimpleNamespace
from gate import TerminalGate,observe_and_cancel

class FakeExecutor:
    def __init__(self):
        self.lock=threading.RLock();self.active=('primary',SimpleNamespace(intent_token='lease1'),None)
        self.calls=[]
    def cancel(self,identifier):
        with self.lock:self.calls.append(identifier);return self.active is not None and self.active[0]==identifier

class Tests(unittest.TestCase):
    def setUp(self):self.g=TerminalGate('epoch');self.e=FakeExecutor()
    def obs(self,seq=0,ended=False,ns=10,epoch='epoch'):
        return self.g.observe(epoch=epoch,sequence=seq,ended=ended,observed_ns=ns)
    def test_open(self):self.g.require_open('epoch')
    def test_running(self):self.assertFalse(self.obs());self.g.require_open('epoch')
    def test_terminal(self):
        self.assertTrue(self.obs(ended=True))
        with self.assertRaises(ValueError):self.g.require_open('epoch')
    def test_duplicate_once(self):
        self.assertTrue(self.obs(ended=True));self.assertFalse(self.obs(ended=True))
    def test_terminal_repeat(self):
        self.obs(ended=True);self.assertFalse(self.obs(1,True,20));self.assertEqual(self.g.first_end_ns,10)
    def test_cannot_revive(self):
        self.obs(ended=True)
        with self.assertRaises(ValueError):self.obs(1,False,20)
        with self.assertRaises(ValueError):self.g.require_open('epoch')
    def test_old_sequence_ignored(self):
        self.obs(2,False,20);self.assertFalse(self.obs(1,True,10));self.g.require_open('epoch')
    def test_foreign_epoch_ignored(self):
        self.assertFalse(self.obs(ended=True,epoch='old'));self.g.require_open('epoch')
    def test_foreign_submit(self):
        with self.assertRaises(ValueError):self.g.require_open('new')
    def test_inconsistent_duplicate(self):
        self.obs()
        with self.assertRaises(ValueError):self.obs(ended=True)
        self.g.require_open('epoch')
    def test_clock_regression(self):
        self.obs(ns=20)
        with self.assertRaises(ValueError):self.obs(1,True,10)
    def test_boolean_not_integer(self):
        for value in (0,1,None,'True'):
            with self.subTest(value=value),self.assertRaises(TypeError):self.obs(ended=value)
    def test_invalid_clocks(self):
        for x in (-1,True,1.0,None):
            with self.subTest(x=x),self.assertRaises(ValueError):self.obs(ns=x)
    def test_invalid_sequences(self):
        for x in (-1,True,1.0,None):
            with self.subTest(x=x),self.assertRaises(ValueError):self.obs(seq=x)
    def test_no_cancel_while_running(self):
        self.assertEqual(observe_and_cancel(self.e,self.g,epoch='epoch',sequence=0,ended=False,observed_ns=10),{})
        self.assertEqual(self.e.calls,[])
    def test_exact_one_scoped_cancel(self):
        def trigger():return observe_and_cancel(self.e,self.g,epoch='epoch',sequence=0,ended=True,observed_ns=10,clock_ns=lambda:12)
        self.assertEqual(trigger(),dict(revoked_intent='lease1',cancel_called_ns=12,cancel_matched=True))
        self.assertEqual(trigger(),{});self.assertEqual(self.e.calls,['primary'])
    def test_no_active_still_latches(self):
        self.e.active=None
        self.assertEqual(observe_and_cancel(self.e,self.g,epoch='epoch',sequence=0,ended=True,observed_ns=10),{})
        with self.assertRaises(ValueError):self.g.require_open('epoch')
    def test_old_epoch_cannot_cancel_current(self):
        observe_and_cancel(self.e,self.g,epoch='old',sequence=0,ended=True,observed_ns=10)
        self.assertEqual(self.e.calls,[])
    def test_concurrent_duplicates(self):
        threads=[threading.Thread(target=observe_and_cancel,args=(self.e,self.g),kwargs=dict(epoch='epoch',sequence=0,ended=True,observed_ns=10)) for _ in range(8)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(self.e.calls,['primary'])

if __name__=='__main__':unittest.main()
