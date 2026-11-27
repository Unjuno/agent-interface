"""Standard X11 must stop new input after its original lease expires."""
import os
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from Xlib import X
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.backends.x11_v1.test_mapping_boundary import MappingBoundaryTests

class StandardExpiryTests(unittest.TestCase):
    def test_expired_wait_releases_held_key_and_does_not_emit_suffix(self):
        backend,events,physical,emitted,emit=MappingBoundaryTests().backend()
        now=[99]
        backend._wait_update=lambda _ms: now.__setitem__(0,100)
        backend.manifest=lambda: {}
        program={"authority":{"lease_id":"lease","expires_at_ns":100},"ops":[
            {"op":"key_state","key":"w","down":True},
            {"op":"wait_update","timeout_ms":1},
            {"op":"text","text":"a"},
            {"op":"release_all"}]}
        admitted=SimpleNamespace(accepted=True,required_capabilities=[])
        with patch("runtime.backends.x11_v1.session.admit_program",return_value=admitted), \
             patch("runtime.backends.x11_v1.backend.time.monotonic_ns",side_effect=lambda:now[0]), \
             patch("runtime.backends.x11_v1.backend.xtest.fake_input",side_effect=emit):
            result=X11RuntimeSession(backend).dispatch(program,current_observation_seq=1,
                                                      current_binding_revision=1,now_ns=99)
        self.assertEqual(result["status"],"execution_failed")
        self.assertEqual(result["execution"]["completed_ops"],[0,1])
        self.assertEqual(result["execution"]["failed_op"],2)
        backend.text.assert_not_called()
        self.assertEqual(emitted,[(X.KeyPress,25),(X.KeyRelease,25)])
        self.assertEqual(physical,set())
        self.assertTrue(result["execution"]["releases"][-1]["verified"])

    def test_expiry_during_custody_publication_prevents_native_press(self):
        backend,events,physical,emitted,emit=MappingBoundaryTests().backend()
        now=[99]
        backend._publish_input_obligations=lambda:now.__setitem__(0,100)
        backend.manifest=lambda: {}
        program={"authority":{"lease_id":"lease","expires_at_ns":100},"ops":[
            {"op":"key_state","key":"w","down":True},{"op":"release_all"}]}
        admitted=SimpleNamespace(accepted=True,required_capabilities=[])
        with patch("runtime.backends.x11_v1.session.admit_program",return_value=admitted), \
             patch("runtime.backends.x11_v1.backend.time.monotonic_ns",side_effect=lambda:now[0]), \
             patch("runtime.backends.x11_v1.backend.xtest.fake_input",side_effect=emit):
            result=X11RuntimeSession(backend).dispatch(program,current_observation_seq=1,
                                                      current_binding_revision=1,now_ns=99)
        self.assertEqual(result["status"],"execution_failed")
        self.assertNotIn((X.KeyPress,25),emitted)
        self.assertEqual(physical,set())
        self.assertTrue(result["execution"]["releases"][-1]["verified"])

    def test_wait_stops_at_deadline_instead_of_full_wait(self):
        import threading
        from runtime.backends.x11_v1.backend import X11BackendError
        backend,events,physical,emitted,emit=MappingBoundaryTests().backend()
        backend._program_deadline_context=threading.local()
        backend._program_deadline_context.deadline=150_000_000
        now=[100_000_000]
        requested=[]
        def sleep(seconds):
            requested.append(seconds)
            now[0]+=round(seconds*1_000_000_000)
        with patch("runtime.backends.x11_v1.backend.time.monotonic_ns",side_effect=lambda:now[0]), \
             patch("runtime.backends.x11_v1.backend.time.sleep",side_effect=sleep):
            with self.assertRaises(X11BackendError):
                backend._wait_update(200)
        self.assertEqual(requested,[0.05])

@unittest.skipUnless(os.environ.get("DISPLAY"), "requires caller-owned private X11 display")
class LiveStandardExpiryTests(unittest.TestCase):
    def test_expired_wait_releases_real_x11_key(self):
        from Xlib import display
        from runtime.backends.x11_v1.backend import X11Backend
        from runtime.core_v1.contract import SCHEMA_PROGRAM
        connection=display.Display()
        window=connection.screen().root.create_window(10,10,200,100,0,
            connection.screen().root_depth, X.InputOutput, X.CopyFromParent)
        window.map()
        connection.sync()
        backend=X11Backend(os.environ["DISPLAY"],{"fixture":window.id})
        try:
            program={"schema":SCHEMA_PROGRAM,"program_id":"expiry-live",
                     "source":{"observation_seq":1,"binding_revision":1},
                     "authority":{"lease_id":"lease","expires_at_ns":time.monotonic_ns()+1_000_000_000},
                     "terminal":{"release_all_required":True},
                     "ops":[{"op":"focus","target":"fixture"},
                            {"op":"key_state","key":"a","down":True},
                            {"op":"wait_update","timeout_ms":1500},
                            {"op":"text","text":"mustnotrun"},
                            {"op":"release_all"}]}
            result=X11RuntimeSession(backend).dispatch(program,current_observation_seq=1,current_binding_revision=1)
            self.assertEqual(result["status"],"execution_failed",result)
            self.assertIn("LEASE_EXPIRED_DURING_EXECUTION",result["execution"]["error"])
            self.assertEqual(result["execution"]["completed_ops"],[0,1])
            self.assertEqual(result["execution"]["failed_op"],2)
            self.assertTrue(result["execution"]["releases"][-1]["verified"])
            self.assertEqual(result["execution"]["releases"][-1]["keys_down"],[])
            self.assertFalse(result["recovery_required"])
        finally:
            backend.close()
            window.destroy()
            connection.close()

if __name__=="__main__":
    unittest.main()
