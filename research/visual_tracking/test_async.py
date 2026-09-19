import threading,unittest
from types import SimpleNamespace
from PIL import Image
from async_session_v2 import Backend,Executor


class FakeBackend(Backend):
    def __init__(self,emit,cancel_after_snapshot=False):
        self.emit=emit;self.sequence=0;self.held={'Left'};self.released=False
        self.decoder=SimpleNamespace(frame=None);self.cancel_after_snapshot=cancel_after_snapshot
        self.inputs=[]
    def snapshot(self,identifier,index):
        self.sequence+=1
        im=Image.new('RGB',(80,80))
        self.decoder.frame=SimpleNamespace(mode='RGB',width=80,height=80,pixels=im.tobytes())
        if self.cancel_after_snapshot:self.cancel.set()
    def execute(self,step,cancel,identifier,index):
        self.cancel=cancel;return super().execute(step,cancel,identifier,index)
    def raw(self,key,down):self.inputs.append((key,down))
    def release_all(self):self.held.clear();self.released=True;return dict(verified=True)


class TestTracking(unittest.TestCase):
    def test_lost_target_fails_and_releases(self):
        rows=[];done=threading.Event()
        def emit(r):
            rows.append(r)
            if r['event']=='terminal':done.set()
        b=FakeBackend(emit);e=Executor(b,emit)
        try:
            e.submit('a',[dict(op='track_red',duration_ms=100)],0)
            self.assertTrue(done.wait(1));self.assertEqual(rows[-1]['status'],'failed')
            self.assertIn('visible target',rows[-1]['error']);self.assertTrue(b.released)
            self.assertEqual(b.inputs,[])
        finally:e.close()

    def test_invalid_tracking_tail_rejected_before_input(self):
        b=FakeBackend(lambda _:None);e=Executor(b,lambda _:None)
        try:
            for duration in (True,0,30001,float('nan')):
                with self.assertRaises(ValueError):
                    e.submit('a',[dict(op='key',key='Return'),dict(op='track_red',duration_ms=duration)],0)
            self.assertEqual(b.inputs,[])
        finally:e.close()


if __name__=='__main__':unittest.main()
