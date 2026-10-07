import os,time,unittest
from pipe_transport import PipeSession
from pipe_receipt import encode_frame
import drift

class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(drift,'wait_for_drift'),'observer not implemented')
        self.binding=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64)
        self.start=time.monotonic_ns()
    def write(self,session,kind,sequence,widget,focus):
        value=dict(self.binding,schema='issue5260-a09-focus-pipe-v1',kind=kind,
                   sequence=sequence,widget=widget,focus_get=focus,
                   event_ns=time.monotonic_ns(),written_ns=time.monotonic_ns())
        os.write(session.write_fd,encode_frame(value))
    def test_actual_pipe_pair_observed_and_samples_retained(self):
        with PipeSession() as s:
            self.write(s,'FocusOut',2,'target','other')
            self.write(s,'FocusIn',3,'decoy','other')
            result=drift.wait_for_drift(s,self.binding,1,self.start,timeout_ns=10_000_000)
            self.assertEqual(result['status'],'OBSERVED_DRIFT')
            self.assertEqual(len(result['samples']),1)
            self.assertEqual(result['samples'][0]['errors'],[])
            self.assertEqual([f['sequence'] for f in result['frames']],[2,3])
            self.assertEqual(result['samples'][0]['read_attempts'],2)
    def test_empty_actual_pipe_timeout_is_not_drift(self):
        with PipeSession() as s:
            r=drift.wait_for_drift(s,self.binding,1,self.start,timeout_ns=2_000_000)
            self.assertEqual(r['status'],'STOP')
            self.assertEqual(r['reason'],'TIMEOUT')
            self.assertEqual(r['samples'][0]['frames'],[])
            self.assertGreaterEqual(r['decided_ns']-r['started_ns'],2_000_000)
    def test_actual_eof_is_terminal_not_timeout(self):
        with PipeSession() as s:
            s.release_parent_writer()
            r=drift.wait_for_drift(s,self.binding,1,self.start,timeout_ns=100_000_000)
            self.assertEqual(r['reason'],'EOF')
            self.assertEqual(len(r['samples']),1)
    def test_later_target_focus_invalidates_previous_pair(self):
        with PipeSession() as s:
            self.write(s,'FocusOut',2,'target','other')
            self.write(s,'FocusIn',3,'decoy','other')
            self.write(s,'FocusIn',4,'target','target')
            r=drift.wait_for_drift(s,self.binding,1,self.start,timeout_ns=10_000_000)
            self.assertEqual(r['status'],'STOP')
            self.assertEqual(r['reason'],'INVALID_TRANSITION')
    def test_invalid_bounds_reject_before_pipe_read(self):
        with PipeSession() as s:
            with self.assertRaises(ValueError):
                drift.wait_for_drift(s,self.binding,True,self.start)
            self.assertEqual(s.reads,[])

if __name__=='__main__':unittest.main()
