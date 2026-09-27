"""I/O-free boundary checks; no formal allocation or task input."""
import unittest
from policy import Continuation

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.p=dict(session='dev',id='P',generation=1,parent='ROOT:1')
        self.c=dict(session='dev',id='C',generation=2,parent='P:1')
    def new(self): return Continuation([self.p,self.c],'LINEAGE_BOUND_POP')
    def receipt(self, frame, **changes): return dict(frame,status='RESOLVED',**changes)
    def test_normal_exactly_once(self):
        x=self.new();self.assertFalse(x.deliver(self.receipt(self.c))['resume'])
        self.assertTrue(x.deliver(self.receipt(self.p))['resume'])
        self.assertFalse(x.deliver(self.receipt(self.p))['resume'])
    def test_duplicate(self):
        x=self.new();x.deliver(self.receipt(self.c));self.assertFalse(x.deliver(self.receipt(self.c))['accepted'])
        self.assertEqual(x.stack,[self.p])
    def test_old_generation(self):
        x=self.new();v=self.receipt(self.c);v['generation']=1
        self.assertFalse(x.deliver(v)['accepted'])
    def test_missing_child(self):
        x=self.new();self.assertFalse(x.deliver(self.receipt(self.p))['accepted']);self.assertEqual(len(x.stack),2)
    def test_each_identity_field(self):
        for key in ('session','id','parent'):
            x=self.new();v=self.receipt(self.c);v[key]='bad';self.assertFalse(x.deliver(v)['accepted'])
    def test_strict_generation(self):
        for invalid in (True,2.0,'2',None):
            x=self.new();v=self.receipt(self.c);v['generation']=invalid;self.assertFalse(x.deliver(v)['accepted'])
    def test_missing_status_or_field(self):
        for key in ('session','id','generation','parent','status'):
            x=self.new();v=self.receipt(self.c);del v[key];self.assertFalse(x.deliver(v)['accepted'])
    def test_weak_is_diagnostic(self):
        x=Continuation([self.p,self.c],'COUNT_ONLY_POP');x.deliver(self.receipt(self.c))
        self.assertTrue(x.deliver(self.receipt(self.c))['resume'])

if __name__=='__main__': unittest.main()
