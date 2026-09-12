import threading
import time
import unittest
from executor import Executor,Cancelled


class FakeBackend:
    def __init__(self):self.entered=threading.Event();self.actions=[];self.released=False
    def validate(self,steps):
        if not steps or any(s.get('op') not in ('block','done') for s in steps):raise ValueError('bad program')
    def execute(self,step,cancel,identifier,index):
        self.actions.append(step['op']);self.entered.set()
        if step['op']=='block':
            if not cancel.wait(2):raise TimeoutError('test watchdog')
            raise Cancelled()
    def release_all(self):self.released=True;return dict(verified=True)


class ExecutorTest(unittest.TestCase):
    def test_accept_cancel_busy_and_release(self):
        b=FakeBackend();events=[];e=Executor(b,events.append)
        e.submit('a',[dict(op='block'),dict(op='done')])
        self.assertTrue(b.entered.wait(1));self.assertEqual(events[0]['event'],'accepted')
        with self.assertRaises(ValueError):e.submit('b',[dict(op='done')])
        self.assertFalse(e.cancel('wrong'));self.assertTrue(e.cancel('a'))
        e.close()
        self.assertEqual(b.actions,['block']);self.assertTrue(b.released)
        self.assertEqual(events[-1]['status'],'cancelled')
        self.assertEqual(events[-1]['steps_completed'],0)

    def test_invalid_tail_rejected_before_execution(self):
        b=FakeBackend();e=Executor(b,lambda _:None)
        with self.assertRaises(ValueError):e.submit('a',[dict(op='done'),dict(op='bad')])
        self.assertEqual(b.actions,[]);e.close()

    def test_release_failure_is_not_success(self):
        b=FakeBackend();events=[]
        def failed_release():raise RuntimeError('release failed')
        b.release_all=failed_release;e=Executor(b,events.append)
        e.submit('a',[dict(op='done')]);e.close()
        self.assertEqual(events[-1]['status'],'failed')
        self.assertFalse(events[-1]['release']['verified'])

    def test_unverified_release_and_accepted_program_snapshot(self):
        b=FakeBackend();events=[]
        b.release_all=lambda:dict(verified=False)
        e=Executor(b,events.append)
        steps=[dict(op='block')]
        e.submit('a',steps)
        self.assertTrue(b.entered.wait(1))
        steps.append(dict(op='done'))
        e.cancel('a');e.close()
        self.assertEqual(b.actions,['block'])
        self.assertEqual(events[-1]['status'],'failed')


if __name__=='__main__':unittest.main()
