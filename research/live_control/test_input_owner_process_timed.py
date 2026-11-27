"""Spawned owner opts in to timed key release, using only Fake X."""
import tempfile
import time
import unittest
from pathlib import Path
from input_owner_rpc_v2 import OwnerRpcClient
from input_owner_cancel_v4 import CancellationClient
from input_owner_process_v3 import launch_owner_service
from test_input_owner_process_v3 import fake_owner, make_lease

class TimedOwnerProcessTests(unittest.TestCase):
    def test_independent_cancellation_preempts_timed_release(self):
        with tempfile.TemporaryDirectory() as temp:
            handle=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=fake_owner,timed_up=True,cancellation=True)
            client=control=None
            try:
                client=OwnerRpcClient(handle.take_socket(),display=":fake",service_id=handle.service_id,timeout=2,timed_up=True)
                control=CancellationClient(handle.take_cancellation_socket(),startup=handle.startup,timeout=2)
                lease=make_lease();control.watch(lease);admission=client.call("down",lease,"a")
                client.call("arm_timed_up",lease,{"ticket":"cancel", "keys":["a"], "deadline_ns":admission["input_ack_ns"]+3_000_000_000})
                lease.set();outcome=control.wait(lease.intent_token,3)
                self.assertIs(outcome.get("release_verified"),True)
                self.assertEqual(client.call("take_timed_up",lease,"cancel")["status"],"cancelled")
            finally:
                if client is not None:client.close()
                if control is not None:control.close()
                handle.close_channel();handle.process.join(5)
                self.assertFalse(handle.process.is_alive())
    def test_spawned_owner_timed_release_and_clean_retirement(self):
        with tempfile.TemporaryDirectory() as temp:
            handle=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=fake_owner,timed_up=True)
            client=None
            try:
                self.assertIs(handle.startup.get("timed_up_enabled"),True)
                client=OwnerRpcClient(handle.take_socket(),display=":fake",service_id=handle.service_id,timeout=2,timed_up=True)
                lease=make_lease();admission=client.call("down",lease,"a")
                deadline=admission["input_ack_ns"]+200_000_000
                client.call("arm_timed_up",lease,{"ticket":"t","keys":["a"],"deadline_ns":deadline})
                time.sleep(.3)
                result=client.call("take_timed_up",lease,"t")
                self.assertEqual(result["status"],"released")
                self.assertTrue(result["receipts"][0]["server_keyup_verified"])
                self.assertTrue(client.close()["verified"])
                self.assertTrue(handle.wait(5)["verified"])
            finally:
                if client is not None:client.close()
                handle.close_channel();handle.process.join(5)
                self.assertFalse(handle.process.is_alive())

if __name__=="__main__":unittest.main()
