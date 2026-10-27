"""Concurrent session recovery tests with no native input."""
import threading
import unittest
from runtime.backends.win32_v1.session import Win32RuntimeSession

class BlockingBackend:
    def __init__(self):
        self.entered=threading.Event(); self.finish=threading.Event(); self.calls=0
    def release_all(self):
        self.calls += 1
        if self.calls == 1:
            self.entered.set()
            if not self.finish.wait(3): raise RuntimeError("test barrier timeout")
        return {"verified":True,"keys_down":[],"buttons_down":[],"keys_unknown":[],"buttons_unknown":[]}

class RecoveryConcurrencyTests(unittest.TestCase):
    def test_concurrent_recovery_does_not_start_a_second_release(self):
        backend=BlockingBackend(); session=Win32RuntimeSession(backend);session.recovery_required=True
        results=[];worker=threading.Thread(target=lambda: results.append(session.recover_input()))
        worker.start()
        try:
            self.assertTrue(backend.entered.wait(1))
            duplicate=session.recover_input()
            self.assertEqual(duplicate["status"],"pending")
            self.assertEqual(duplicate["error"],"INPUT_RECOVERY_IN_PROGRESS")
            self.assertFalse(duplicate["release_attempted"])
            self.assertEqual(backend.calls,1)
            dispatch=session.dispatch({},current_observation_seq=0,current_binding_revision=0)
            self.assertEqual(dispatch["error"],"INPUT_RECOVERY_IN_PROGRESS")
            self.assertFalse(dispatch["input_dispatched"])
        finally:
            backend.finish.set();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0]["status"],"input_recovered")

    def test_failed_recovery_releases_reservation_for_later_retry(self):
        class RetryBackend:
            def __init__(self): self.calls=0
            def release_all(self):
                self.calls+=1
                if self.calls==1: raise RuntimeError("inert failure")
                return {"verified":True,"keys_down":[],"buttons_down":[],"keys_unknown":[],"buttons_unknown":[]}
        backend=RetryBackend(); session=Win32RuntimeSession(backend);session.recovery_required=True
        self.assertEqual(session.recover_input()["status"],"recovery_failed")
        self.assertTrue(session.recovery_required)
        self.assertEqual(session.recover_input()["status"],"input_recovered")
        self.assertEqual(backend.calls,2)

if __name__=="__main__":unittest.main()
