import os
import time
import unittest
from pipe_receipt import encode_frame
from pipe_transport import PipeSession
from pipe_gate import wait_for_target


class GateTests(unittest.TestCase):
    def setUp(self):
        self.binding={'token':'fresh','pid':17,'target_id':42,'freeze_sha256':'a'*64}
        self.click=time.monotonic_ns()

    def frame(self,kind='FocusIn',sequence=1):
        return {**self.binding,'schema':'issue5260-a09-focus-pipe-v1',
            'kind':kind,'widget':'target','focus_get':'target' if kind=='FocusIn' else 'other',
            'sequence':sequence,'event_ns':time.monotonic_ns(),
            'written_ns':time.monotonic_ns()}

    def test_fresh_actual_pipe_receipt_admits(self):
        with PipeSession() as session:
            os.write(session.write_fd,encode_frame(self.frame()))
            result=wait_for_target(session,self.binding,self.click,timeout_ns=20_000_000)
            self.assertEqual(result['status'],'ADMITTED')
            self.assertEqual(result['ack']['sequence'],1)
            self.assertEqual(result['samples'][0]['errors'],[])

    def test_later_focusout_does_not_admit_older_target_receipt(self):
        with PipeSession() as session:
            os.write(session.write_fd,encode_frame(self.frame())+encode_frame(self.frame('FocusOut',2)))
            result=wait_for_target(session,self.binding,self.click,timeout_ns=2_000_000)
            self.assertEqual(result['status'],'REFUSED')
            self.assertTrue(result['samples'])
            self.assertIn('not_current_target',result['samples'][0]['errors'])
            self.assertEqual(result['samples'][0]['state']['sequence'],2)

    def test_empty_pipe_timeout_retains_first_failed_sample(self):
        with PipeSession() as session:
            started=time.monotonic_ns()
            result=wait_for_target(session,self.binding,self.click,timeout_ns=2_000_000)
            self.assertEqual(result['status'],'REFUSED')
            self.assertTrue(result['samples'])
            self.assertEqual(result['samples'][0]['errors'],['no_frame'])
            self.assertGreaterEqual(result['decided_ns']-started,2_000_000)

    def test_closed_empty_pipe_refuses_without_polling_until_timeout(self):
        with PipeSession() as session:
            session.release_parent_writer()
            result=wait_for_target(session,self.binding,self.click)
            self.assertEqual(result['status'],'REFUSED')
            self.assertEqual(result.get('reason'),'EOF_BEFORE_ADMISSION')


if __name__=='__main__':unittest.main()
