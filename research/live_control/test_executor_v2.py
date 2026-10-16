import unittest
import threading
from executor_v2 import Executor,DecisionRequired


class Backend:
    sequence=7
    def __init__(self):self.actions=[];self.released=False
    def validate(self,steps):
        if not steps or any(s.get('op') not in ('done','decide') for s in steps):
            raise ValueError('invalid program')
    def execute(self,step,cancel,identifier,index):
        self.actions.append(step['op']);self.sequence+=1
        if step['op']=='decide':raise DecisionRequired()
    def release_all(self):self.released=True;return dict(verified=True)


class TestBoundary(unittest.TestCase):
    def test_boundary_discards_tail_and_requires_fresh_observation(self):
        b=Backend();events=[];ended=threading.Event()
        def emit(e):
            events.append(e)
            if e['event']=='terminal':ended.set()
        e=Executor(b,emit)
        try:
            e.submit('first',[dict(op='done'),dict(op='decide'),dict(op='done')],7)
            self.assertTrue(ended.wait(1))
            self.assertEqual(events[-1]['status'],'needs_decision')
            self.assertEqual(b.actions,['done','decide']);self.assertTrue(b.released)
            with self.assertRaises(ValueError):e.submit('stale',[dict(op='done')],7)
            self.assertEqual(b.actions,['done','decide'])
            ended.clear();e.submit('fresh',[dict(op='done')],9)
            self.assertTrue(ended.wait(1));self.assertEqual(events[-1]['status'],'completed')
        finally:e.close()

    def test_missing_invalid_or_boolean_sequence_rejected(self):
        b=Backend();e=Executor(b,lambda _:None)
        try:
            for sequence in (None,True,7.0,'7',6):
                with self.assertRaises(ValueError):e.submit('x',[dict(op='done')],sequence)
            self.assertEqual(b.actions,[])
        finally:e.close()


if __name__=='__main__':unittest.main()
