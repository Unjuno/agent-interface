"""Timed release through the real cancellation-aware owner adapter; Fake X only."""
from contextlib import contextmanager
import tempfile
import time
import unittest
from pathlib import Path
from input_owner_process_v3 import launch_owner_service
from input_owner_service_adapter import OwnedOwnerAdapter
from test_input_owner_process_v3 import fake_owner, make_lease, native

@contextmanager
def fake_unverified_up(*,display,out,service_id):
    with fake_owner(display=display,out=out,service_id=service_id) as owner:
        original=native.xtest.fake_input.side_effect
        def fail_until_allowed(connection,kind,code):
            if kind==native.X.KeyRelease and not (out/"allow-release").exists():return
            return original(connection,kind,code)
        native.xtest.fake_input.side_effect=fail_until_allowed
        yield owner

class TimedAdapterTests(unittest.TestCase):
    def test_unverified_timed_release_retains_obligation_after_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=launch_owner_service(display=":fake",out=Path(tmp)/"service",_owner_factory=fake_unverified_up,cancellation=True,timed_up=True)
            adapter=None
            try:
                adapter=OwnedOwnerAdapter(service,display=":fake")
                lease=make_lease();adapter.bind_lease(lease)
                admission=adapter.call("down",lease,"a")
                adapter.call("arm_timed_up",lease,{"ticket":"bad", "keys":["a"], "deadline_ns":admission["input_ack_ns"]+200_000_000})
                time.sleep(.35)
                result=adapter.call("take_timed_up",lease,"bad")
                self.assertEqual(result["status"],"unverified")
                self.assertEqual(adapter.obligation_snapshot()["kind"],"timed_release_unverified")
                (service.out/"allow-release").touch()
                self.assertFalse(adapter.close()["verified"])
            finally:
                (service.out/"allow-release").touch()
                if adapter is not None:adapter.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_atomic_timed_press_survives_stalled_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=launch_owner_service(display=":fake",out=Path(tmp)/"service",_owner_factory=fake_owner,cancellation=True,timed_up=True)
            adapter=None
            try:
                adapter=OwnedOwnerAdapter(service,display=":fake")
                lease=make_lease();adapter.bind_lease(lease)
                admission=adapter.call("down_timed",lease,{"key":"a","ticket":"atomic","duration_ms":200})
                self.assertEqual(admission["timed_deadline_ns"],admission["input_ack_ns"]+200_000_000)
                time.sleep(.3)
                result=adapter.call("take_timed_up",lease,"atomic")
                self.assertEqual(result["status"],"released")
                self.assertTrue(result["receipts"][0]["server_keyup_verified"])
                self.assertIsNone(adapter.obligation_snapshot())
                close=adapter.close()
                self.assertTrue(close["verified"],close)
            finally:
                if adapter is not None:adapter.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_adapter_cancellation_preempts_timed_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=launch_owner_service(display=":fake",out=Path(tmp)/"service",_owner_factory=fake_owner,cancellation=True,timed_up=True)
            adapter=None
            try:
                adapter=OwnedOwnerAdapter(service,display=":fake")
                lease=make_lease();adapter.bind_lease(lease)
                admission=adapter.call("down",lease,"a")
                adapter.call("arm_timed_up",lease,{"ticket":"cancel", "keys":["a"], "deadline_ns":admission["input_ack_ns"]+3_000_000_000})
                lease.set();outcome=adapter.control.wait(lease.intent_token,3)
                self.assertIs(outcome.get("release_verified"),True)
                self.assertEqual(adapter.call("take_timed_up",lease,"cancel")["status"],"cancelled")
                self.assertIsNone(adapter.obligation_snapshot())
                close=adapter.close()
                self.assertTrue(close["verified"],close)
            finally:
                if adapter is not None:adapter.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_adapter_releases_while_caller_is_waiting_and_retains_no_obligation(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=launch_owner_service(display=":fake",out=Path(tmp)/"service",_owner_factory=fake_owner,cancellation=True,timed_up=True)
            adapter=None
            try:
                adapter=OwnedOwnerAdapter(service,display=":fake")
                lease=make_lease();adapter.bind_lease(lease)
                admission=adapter.call("down",lease,"a");deadline=admission["input_ack_ns"]+400_000_000
                adapter.call("arm_timed_up",lease,{"ticket":"op", "keys":["a"], "deadline_ns":deadline})
                with self.assertRaises(ValueError): adapter.call("take_timed_up",lease,"op")
                self.assertIsNone(adapter.obligation_snapshot())
                time.sleep(.55)
                result=adapter.call("take_timed_up",lease,"op")
                self.assertEqual(result["status"],"released")
                self.assertTrue(result["receipts"][0]["server_keyup_verified"])
                self.assertIsNone(adapter.obligation_snapshot())
                close=adapter.close()
                self.assertTrue(close["verified"],close)
            finally:
                if adapter is not None:adapter.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())

if __name__=="__main__": unittest.main()
