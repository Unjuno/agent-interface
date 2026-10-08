import tempfile,unittest,json
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
class Child:
    def __init__(self, fail=False): self.stdin=Pipe(fail);self.exited=False
    def poll(self): return 0 if self.exited else None
    def wait(self,timeout): self.exited=True;return 0
    def terminate(self): self.exited=True
    def kill(self): self.exited=True
class Tests(unittest.TestCase):
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
