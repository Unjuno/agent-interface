import time,threading,unittest
from lease import Lease,Expired
from executor_v3 import Executor


class Backend:
    sequence=1
    def __init__(self):self.actions=[];self.released=False
    def validate(self,steps):pass
    def execute(self,step,cancel,identifier,index):
        self.actions.append(step['op'])
        if step['op']=='hold':cancel.wait(1)
    def release_all(self):self.released=True;return dict(verified=True)


class Tests(unittest.TestCase):
    def test_absolute_expiry_does_not_restart_on_receipt(self):
        clock=[10];lease=Lease(20,lambda:clock[0]);lease.check()
        clock[0]=20
        with self.assertRaises(Expired):lease.check()
    def test_expired_submission_has_no_input(self):
        b=Backend();e=Executor(b,lambda _:None)
        with self.assertRaises(Expired):e.submit('a',[dict(op='tail')],1,time.perf_counter_ns()-1)
        self.assertEqual(b.actions,[]);e.close()
    def test_expiry_interrupts_hold_and_discards_tail(self):
        b=Backend();rows=[];done=threading.Event()
        def emit(r):
            rows.append(r)
            if r['event']=='terminal':done.set()
        e=Executor(b,emit)
        try:
            e.submit('a',[dict(op='hold'),dict(op='tail')],1,time.perf_counter_ns()+50_000_000)
            self.assertTrue(done.wait(1));self.assertEqual(rows[-1]['status'],'expired')
            self.assertEqual(b.actions,['hold']);self.assertTrue(b.released)
        finally:e.close()


if __name__=='__main__':unittest.main()
