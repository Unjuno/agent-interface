import threading,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
import session_v8
from session_v8 import Backend
from lease import Lease
from executor_v3 import Cancelled,DecisionRequired,Executor

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
        with self.assertRaises(DecisionRequired):
            b.execute(dict(op='settle',quiet_ms=40,timeout_ms=60),lease,'wait',0)
        self.assertEqual(b.events[-1]['reason'],'timeout')
        self.assertEqual(b.events[-1]['semantic_completion'],'unknown')

    def test_settle_timeout_stops_preplanned_input_tail(self):
        settle_backend=self.backend(True)
        class ProgramBackend:
            sequence=0
            def __init__(self):self.executed=[]
            def validate(self,steps):settle_backend.validate(steps)
            def execute(self,step,cancel,identifier,index):
                self.executed.append(step['op'])
                if step['op']=='settle':
                    settle_backend.execute(step,cancel,identifier,index)
            def release_all(self):return {'verified':True}
        backend=ProgramBackend();events=[];terminal=threading.Event()
        def emit(record):
            events.append(record)
            if record.get('event')=='terminal':terminal.set()
        executor=Executor(backend,emit)
        self.addCleanup(executor.close)
        executor.submit('timeout-tail',[
            {'op':'settle','quiet_ms':40,'timeout_ms':60},
            {'op':'hold','keys':['Left'],'duration_ms':1}],
            expected_sequence=0,valid_until_ns=time.perf_counter_ns()+2_000_000_000)
        self.assertTrue(terminal.wait(2),'executor did not publish a terminal result')
        with executor.lock:active=executor.active
        self.assertIsNone(active,'executor did not finish its program')
        self.assertEqual(backend.executed,['settle'])
        self.assertEqual(settle_backend.events[-1]['reason'],'timeout')
        self.assertEqual(events[-1]['status'],'needs_decision')

    def test_capture_returning_after_timeout_cannot_report_pixel_quiet(self):
        b=self.backend();now=[0]
        def delayed_snapshot(*args):
            b.sequence+=1;b.observed_focus=123;b.decoder.frame='same pixels'
            now[0]=1_000_000 if b.sequence==1 else 61_000_000
        b.snapshot=delayed_snapshot
        cancel=SimpleNamespace(is_set=lambda:False,wait=lambda timeout:False)
        clock=SimpleNamespace(perf_counter_ns=lambda:now[0])
        with patch.object(session_v8,'time',clock),self.assertRaises(DecisionRequired):
            b.execute(dict(op='settle',quiet_ms=40,timeout_ms=60),cancel,'late',0)
        self.assertEqual(b.sequence,2)
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
