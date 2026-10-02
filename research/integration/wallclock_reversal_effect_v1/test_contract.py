import time, unittest
from candidate import decide, admit

class Contract(unittest.TestCase):
    def records(self,post=1,age=75,dup=False,cross=False):
        b=10_000_000_000; epoch='A'
        rel=[-25_000_000,-125_000_000,-225_000_000] if age==75 else [0,-100_000_000,-200_000_000]
        rev=-age*1_000_000; out=[]
        for i,t in enumerate(rel):
            pre=-post; x=(pre if t<=rev else post)*73*((t-rev)/1e9)
            ts=b+t
            if dup and i==1: ts=b+rel[0]
            out.append({'source_ns':ts,'x':x,'epoch':'B' if cross and i==2 else epoch})
        return out
    def test_recent_right_left(self):
        self.assertEqual(decide(self.records(1,75),session_id='s',window_id=1)['decision'],'RIGHT')
        self.assertEqual(decide(self.records(-1,75),session_id='s',window_id=1)['decision'],'LEFT')
    def test_age200_unknown(self):
        self.assertEqual(decide(self.records(1,200),session_id='s',window_id=1)['decision'],'UNKNOWN')
        self.assertEqual(decide(self.records(-1,200),session_id='s',window_id=1)['decision'],'UNKNOWN')
    def test_duplicate_cross_unknown(self):
        self.assertEqual(decide(self.records(1,75,dup=True),session_id='s',window_id=1)['decision'],'UNKNOWN')
        self.assertEqual(decide(self.records(1,75,cross=True),session_id='s',window_id=1)['decision'],'UNKNOWN')
    def test_fresh_binding_and_stale(self):
        d=decide(self.records(1,75),session_id='s',window_id=1); n=time.perf_counter_ns()
        self.assertTrue(admit(d,now_ns=n,decision_created_ns=n,session_id='s',epoch='A',window_id=1)['admitted'])
        self.assertFalse(admit(d,now_ns=n,decision_created_ns=n,session_id='bad',epoch='A',window_id=1)['admitted'])
        self.assertFalse(admit(d,now_ns=n+151_000_000,decision_created_ns=n,session_id='s',epoch='A',window_id=1)['admitted'])
if __name__=='__main__': unittest.main()
