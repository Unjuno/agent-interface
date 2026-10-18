import os,subprocess,sys,tempfile,time,unittest,json
import threading
from unittest.mock import patch
from doom_controller_failure_cleanup_v1 import send_failure_finish
from pathlib import Path
from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

class Planner:
    def __init__(self, fail=False): self.closed=False;self.fail=fail
    def close(self, timeout=1):
        self.closed=True
        if self.fail: raise RuntimeError('planner close failed')
class Pipe:
    def __init__(self, fail=False): self.data='';self.fail=fail
    def write(self, data):
        if self.fail: raise BrokenPipeError()
        self.data+=data
    def flush(self): pass
    def close(self): pass
class Child:
    def __init__(self, fail=False): self.stdin=Pipe(fail);self.exited=False
    def poll(self): return 0 if self.exited else None
    def wait(self,timeout): self.exited=True;return 0
    def terminate(self): self.exited=True
    def kill(self): self.exited=True

class DelayedReader:
    def __init__(self, events, late_rows, stop=True):
        self.events=events;self.late_rows=late_rows;self.stop=stop;self.join_calls=[]
        self.alive=True
    def is_alive(self): return self.alive
    def join(self,timeout):
        self.join_calls.append(timeout);self.events.extend(self.late_rows)
        if self.stop:self.alive=False
class Tests(unittest.TestCase):
    def setUp(self):
        def fake_finish(stream, timeout=.25):
            stream.write('{"op":"finish"}\n');stream.flush()
        self.finish_patch=patch('doom_controller_failure_cleanup_v1.send_failure_finish',
                                side_effect=fake_finish)
        self.finish_patch.start()
        self.addCleanup(self.finish_patch.stop)
    @unittest.skipUnless(os.name=='posix','pipe filling uses POSIX nonblocking descriptor flags')
    def test_full_child_stdin_pipe_does_not_block_cleanup_reachability(self):
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);planner=Planner()
            child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],
                stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                text=True,bufsize=1)
            fd=child.stdin.fileno();old_flags=fcntl.fcntl(fd,fcntl.F_GETFL)
            fcntl.fcntl(fd,fcntl.F_SETFL,old_flags|os.O_NONBLOCK)
            filled=0
            while True:
                try:filled+=os.write(fd,b'x'*4096)
                except BlockingIOError:break
            fcntl.fcntl(fd,fcntl.F_SETFL,old_flags)
            self.assertGreater(filled,0)
            error=ValueError('primary under pipe pressure')
            started=time.monotonic()
            self.finish_patch.stop()
            with self.assertRaises(ValueError) as caught:
                with ControllerFailureCleanup(planner,out,finish_timeout=.15,
                        child_wait_timeout=.15,escalation_wait_timeout=.5) as scope:
                    scope.track(child);scope.set_stage('source_refresh');raise error
            elapsed=time.monotonic()-started
            self.assertIs(caught.exception,error)
            self.assertLess(elapsed,3.0)
            self.assertIsNotNone(child.poll())
            self.assertTrue(planner.closed)
            receipt=json.loads((out/'controller-failure.json').read_text())
            self.assertEqual(receipt['failed_stage'],'source_refresh')
            self.finish_patch.start()
            self.assertEqual(next(row for row in receipt['stages']
                                  if row['stage']=='finish_send')['status'],'failed')
            self.assertFalse(receipt['cleanup_complete'])

    def test_reader_is_joined_before_terminal_evidence_is_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);runtime=out/'runtime';runtime.mkdir()
            (runtime/'score.json').write_text('{"event":"post_control_score"}\n')
            (runtime/'owner-events.json').write_text('[{"reason":"close","verified":true}]\n')
            events=[{'event':'accepted','id':'passive-1'}]
            reader=DelayedReader(events,[
                {'event':'terminal','id':'passive-1','status':'completed',
                 'release':{'verified':True,'keys_down':[],'buttons_down':[]}},
                {'event':'post_control_score'}])
            planner=Planner();child=Child();error=ValueError('typed source unavailable')
            wait_calls=[]
            def event_wait(predicate,timeout):
                wait_calls.append(timeout)
                row={'event':'post_control_score'}
                self.assertTrue(predicate(row));return row
            with self.assertRaises(ValueError) as caught:
                with ControllerFailureCleanup(planner,out) as scope:
                    scope.track(child)
                    scope.set_stage('source_refresh')
                    scope.observe_output(events,reader,event_wait,runtime)
                    raise error
            self.assertIs(caught.exception,error)
            self.assertEqual(reader.join_calls,[5])
            self.assertTrue(planner.closed and child.exited)
            self.assertEqual(wait_calls,[10])
            receipt=json.loads((out/'controller-failure.json').read_text())
            self.assertEqual(receipt['failed_stage'],'source_refresh')
            self.assertTrue(receipt['stdout_reader_retired'])
            self.assertTrue(receipt['input_terminals_complete'])
            self.assertTrue(receipt['input_releases_verified_empty'])
            self.assertTrue(receipt['scorer_terminal_observed'])
            self.assertTrue(receipt['owner_events_closed'])
            self.assertTrue(receipt['cleanup_complete'])

    def test_reader_timeout_fails_closed_on_event_set_completeness(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);runtime=out/'runtime';runtime.mkdir()
            events=[{'event':'accepted','id':'passive-1'}]
            reader=DelayedReader(events,[],stop=False)
            planner=Planner();child=Child()
            event_wait=lambda predicate,timeout:{'event':'post_control_score'}
            with self.assertRaises(ValueError):
                with ControllerFailureCleanup(planner,out) as scope:
                    scope.track(child);scope.observe_output(events,reader,event_wait,runtime)
                    raise ValueError('primary')
            receipt=json.loads((out/'controller-failure.json').read_text())
            self.assertFalse(receipt['stdout_reader_retired'])
            self.assertFalse(receipt['input_terminals_complete'])
            self.assertFalse(receipt['input_releases_verified_empty'])
            self.assertFalse(receipt['cleanup_complete'])

    def test_original_error_preserved_child_finished_planner_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            planner=Planner();child=Child();error=ValueError('original')
            with self.assertRaises(ValueError) as caught:
                with ControllerFailureCleanup(planner,Path(tmp)) as scope:
                    scope.track(child);raise error
            self.assertIs(caught.exception,error)
            self.assertEqual(child.stdin.data,'{"op":"finish"}\n')
            self.assertTrue(child.exited and planner.closed)
            self.assertFalse(json.loads((Path(tmp)/'controller-failure.json').read_text())['input_release_verified'])
    def test_secondary_close_failure_does_not_replace_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            error=KeyboardInterrupt('original');planner=Planner(True)
            with self.assertRaises(KeyboardInterrupt) as caught:
                with ControllerFailureCleanup(planner,Path(tmp)): raise error
            self.assertIs(caught.exception,error);self.assertTrue(planner.closed)
    def test_planner_close_that_ignores_timeout_cannot_block_failure_receipt(self):
        class StuckPlanner:
            def close(self, timeout=1):
                threading.Event().wait()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);error=ValueError('primary')
            started=time.monotonic()
            with self.assertRaises(ValueError) as caught:
                with ControllerFailureCleanup(StuckPlanner(),out): raise error
            elapsed=time.monotonic()-started
            self.assertIs(caught.exception,error)
            self.assertLess(elapsed,2.5)
            receipt=json.loads((out/'controller-failure.json').read_text())
            planner_stage=next(row for row in receipt['stages']
                               if row['stage']=='planner_close')
            self.assertEqual(planner_stage['status'],'timed_out')
            self.assertFalse(receipt['cleanup_complete'])
    def test_timed_out_planner_close_unregisters_atexit_callback(self):
        class StuckPlanner:
            def close(self, timeout=1):
                threading.Event().wait()
        callbacks=[]
        planner=StuckPlanner();callback=planner.close
        register=patch('doom_controller_failure_cleanup_v1.atexit.register',
                       side_effect=callbacks.append)
        unregister=patch('doom_controller_failure_cleanup_v1.atexit.unregister',
                         side_effect=lambda fn: callbacks.remove(fn)
                         if fn in callbacks else None)
        with register,unregister:
            import atexit
            atexit.register(callback)
            with tempfile.TemporaryDirectory() as tmp:
                error=ValueError('primary')
                with self.assertRaises(ValueError) as caught:
                    with ControllerFailureCleanup(planner,Path(tmp)):
                        raise error
                self.assertIs(caught.exception,error)
                receipt=json.loads((Path(tmp)/'controller-failure.json').read_text())
                planner_stage=next(row for row in receipt['stages']
                                   if row['stage']=='planner_close')
                self.assertEqual(planner_stage['status'],'timed_out')
                self.assertFalse(receipt['cleanup_complete'])
            self.assertNotIn(callback,callbacks)
    def test_broken_finish_still_waits_and_closes_planner(self):
        with tempfile.TemporaryDirectory() as tmp:
            planner=Planner();child=Child(True)
            with self.assertRaises(ValueError):
                with ControllerFailureCleanup(planner,Path(tmp)) as scope:
                    scope.track(child);raise ValueError('original')
            self.assertTrue(child.exited and planner.closed)
    def test_success_path_has_no_duplicate_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            planner=Planner();child=Child()
            with ControllerFailureCleanup(planner,Path(tmp)) as scope: scope.track(child)
            self.assertFalse(planner.closed);self.assertEqual(child.stdin.data,'')
    def test_poll_fault_preserves_primary_and_attempts_planner_close(self):
        class BrokenPoll(Child):
            def poll(self): raise RuntimeError('poll failed')
        with tempfile.TemporaryDirectory() as tmp:
            planner=Planner();error=ValueError('original')
            with self.assertRaises(ValueError) as caught:
                with ControllerFailureCleanup(planner,Path(tmp)) as scope:
                    scope.track(BrokenPoll());raise error
            self.assertIs(caught.exception,error);self.assertTrue(planner.closed)
if __name__=='__main__': unittest.main()
