"""Inert preflight and cleanup failure composition."""
import unittest
from runtime.backends.win32_v1.backend import Win32Backend, Win32BackendError
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM

class PreflightCleanupFailureTests(unittest.TestCase):
    def test_cleanup_exception_returns_failure_and_retains_recovery(self):
        b=Win32Backend.__new__(Win32Backend)
        b.emissions=0; b.held_keys={}; b.held_buttons=set(); b.pending_unicode_ups=set()
        def refuse(_program): raise Win32BackendError("target rejected")
        def cleanup(): raise RuntimeError("cleanup query unavailable")
        b.preflight=refuse; b.release_all=cleanup
        session=Win32RuntimeSession(b)
        program={"schema":SCHEMA_PROGRAM,"program_id":"preflight-cleanup",
          "source":{"observation_seq":1,"binding_revision":1},
          "authority":{"lease_id":"lease","expires_at_ns":100},
          "terminal":{"release_all_required":True},
          "ops":[{"op":"focus","target":"fixture"},{"op":"release_all"}]}
        result=session.dispatch(program,current_observation_seq=1,current_binding_revision=1,now_ns=1)
        self.assertEqual(result["status"],"execution_failed")
        self.assertEqual(result["error"],"BACKEND_CLEANUP")
        self.assertTrue(result["recovery_required"])
        self.assertFalse(result["input_dispatched"])
        self.assertIn("target rejected",result["preflight_error"])
        self.assertEqual(result["cleanup_error"]["type"],"RuntimeError")
        self.assertEqual(b.emissions,0)
        again=session.dispatch(program,current_observation_seq=1,current_binding_revision=1,now_ns=1)
        self.assertEqual(again["error"],"INPUT_RECOVERY_REQUIRED")
        self.assertFalse(again["input_dispatched"])
        b.release_all=lambda: {"verified":True,"keys_down":[],"buttons_down":[]}
        recovered=session.recover_input()
        self.assertEqual(recovered["status"],"input_recovered")
        self.assertFalse(recovered["replay_allowed"])

if __name__=="__main__": unittest.main()
