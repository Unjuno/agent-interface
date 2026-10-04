"""Real OS pipes and byte effects; no GUI result or authenticated authority."""
import copy
import os
import time
import unittest
from pipe_transport import PipeSession
from pipe_receipt import encode_frame
try:
    from recovery import RecoveryAttempt
except ImportError:
    RecoveryAttempt=None

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(RecoveryAttempt,'bounded recovery not implemented')
        self.binding=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64)
        self.prior=dict(dispatch={'status':'REFUSED','reason':'OBSERVED_DRIFT'},
            drift={'status':'OBSERVED_DRIFT','frames':[{'sequence':3},{'sequence':4}]})
        self.emissions=[];self.clicks=[]
    def frame(self,sequence,event=None):
        now=time.monotonic_ns()
        return dict(self.binding,schema='issue5260-a09-focus-pipe-v1',kind='FocusIn',
            widget='target',focus_get='target',sequence=sequence,
            event_ns=now if event is None else event,written_ns=now)
    def click(self,session,sequence=6,publish=True):
        started=time.monotonic_ns();self.clicks.append(started)
        if publish:os.write(session.write_fd,encode_frame(self.frame(sequence)))
        return dict(widget='target',started_ns=started,completed_ns=time.monotonic_ns())
    def run_attempt(self,attempt,session,click,requested=True,prior_keys=0,prior_saves=0):
        return attempt.run(requested,self.prior,prior_keys,prior_saves,session,self.binding,
            click,'hxy',lambda c:self.emissions.append(c),lambda:self.emissions.append('Save'),
            timeout_ns=2_000_000,poll_ns=100_000,max_age_ns=50_000_000)
    def test_new_post_click_receipt_emits_one_task_and_preserves_refusal(self):
        prior=copy.deepcopy(self.prior)
        with PipeSession() as session:
            result=self.run_attempt(RecoveryAttempt(),session,lambda:self.click(session))
        self.assertEqual(result['status'],'EMITTED')
        self.assertEqual(result['gate']['ack']['sequence'],6)
        self.assertEqual(self.emissions,['h','x','y','Save'])
        self.assertEqual(len(self.clicks),1)
        self.assertEqual(self.prior,prior)
    def test_old_target_receipt_cannot_transfer_after_new_click(self):
        with PipeSession() as session:
            os.write(session.write_fd,encode_frame(self.frame(2,event=time.monotonic_ns()-1_000_000)))
            result=self.run_attempt(RecoveryAttempt(),session,lambda:self.click(session,publish=False))
        self.assertEqual(result['status'],'STOP')
        self.assertEqual(result['gate']['status'],'REFUSED')
        self.assertEqual(self.emissions,[])
    def test_no_explicit_request_or_partial_input_never_clicks(self):
        for requested,keys,saves in [(False,0,0),(True,1,0),(True,0,1)]:
            with self.subTest(requested=requested,keys=keys,saves=saves),PipeSession() as session:
                result=self.run_attempt(RecoveryAttempt(),session,lambda:self.click(session),requested,keys,saves)
                self.assertEqual(result['status'],'STOP')
                self.assertEqual(session.reads,[])
        self.assertEqual(self.clicks,[]);self.assertEqual(self.emissions,[])
    def test_recovery_attempt_is_not_retried_after_timeout(self):
        attempt=RecoveryAttempt()
        with PipeSession() as session:
            first=self.run_attempt(attempt,session,lambda:self.click(session,publish=False))
            second=self.run_attempt(attempt,session,lambda:self.click(session))
        self.assertEqual(first['status'],'STOP')
        self.assertEqual(second['reason'],'RECOVERY_ALREADY_ATTEMPTED')
        self.assertEqual(len(self.clicks),1);self.assertEqual(self.emissions,[])
    def test_new_clock_with_old_sequence_is_not_new_admission(self):
        with PipeSession() as session:
            result=self.run_attempt(RecoveryAttempt(),session,lambda:self.click(session,sequence=2))
        self.assertEqual(result['reason'],'RECOVERY_SEQUENCE_NOT_NEW')
        self.assertEqual(self.emissions,[])
    def test_invalid_refusal_does_not_create_recovery_input(self):
        self.prior['dispatch']['status']='EMITTED'
        with PipeSession() as session:
            result=self.run_attempt(RecoveryAttempt(),session,lambda:self.click(session))
        self.assertEqual(result['status'],'STOP');self.assertEqual(self.clicks,[])

if __name__=='__main__':unittest.main()
