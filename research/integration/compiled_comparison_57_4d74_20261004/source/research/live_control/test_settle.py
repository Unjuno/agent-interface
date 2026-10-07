import time,unittest
from types import SimpleNamespace
from session_v8 import Backend
from lease import Lease
from executor_v3 import Cancelled,DecisionRequired

class SettleTests(unittest.TestCase):
    def backend(self,changing=False):
        b=Backend.__new__(Backend);b.observed_focus=None;b.sequence=0;b.decoder=SimpleNamespace(frame=None)
        b.events=[];b.emit=b.events.append
        def snapshot(*args):
            b.sequence+=1;b.observed_focus=123
            b.decoder.frame=b.sequence if changing else 'same pixels'
        b.snapshot=snapshot
        return b

    def test_continuous_change_times_out_without_completion_claim(self):
        b=self.backend(True);lease=Lease(time.perf_counter_ns()+1_000_000_000)
        b.execute(dict(op='settle',quiet_ms=40,timeout_ms=60),lease,'wait',0)
        self.assertEqual(b.events[-1]['reason'],'timeout')
        self.assertEqual(b.events[-1]['semantic_completion'],'unknown')

    def test_settle_does_not_authorize_unknown_input_tail(self):
        b=self.backend();lease=Lease(time.perf_counter_ns()+1_000_000_000)
        b.execute(dict(op='settle',quiet_ms=40,timeout_ms=100),lease,'wait',0)
        self.assertEqual(b.events[-1]['reason'],'pixel_quiet')
        with self.assertRaises(DecisionRequired):b.execute(dict(op='text',text='a'),lease,'wait',1)

    def test_cancel_before_settle_has_no_capture(self):
        b=self.backend();lease=Lease(time.perf_counter_ns()+1_000_000_000);lease.set()
        with self.assertRaises(Cancelled):b.execute(dict(op='settle',quiet_ms=40,timeout_ms=100),lease,'wait',0)
        self.assertEqual(b.sequence,0)

if __name__=='__main__':unittest.main()
