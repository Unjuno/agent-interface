"""Opt-in timed owner release across the existing private socket."""
import socket
import threading
import time
import unittest

from test_input_owner_rpc_v2 import backend_fixture, bound
import input_owner_rpc_v2 as rpc

class TimedRpcTests(unittest.TestCase):
    def test_handshake_rejects_mismatched_opt_in(self):
        for server_enabled,client_enabled in ((True,False),(False,True)):
            with self.subTest(server=server_enabled),backend_fixture() as (backend,events,generation,fake):
                a,b=socket.socketpair();results=[]
                thread=threading.Thread(target=lambda:results.append(rpc.serve_owner(b,backend.owner,display=":fake",service_id="timed",timed_up=server_enabled)))
                thread.start()
                with self.assertRaisesRegex(ValueError,"readiness"):
                    rpc.OwnerRpcClient(a,display=":fake",service_id="timed",timeout=2,timed_up=client_enabled)
                thread.join(3);self.assertFalse(thread.is_alive())
    def test_timed_result_must_match_ticket_identity_and_owner_history(self):
        row={"event":"owner_explicit_keyup","operation":"up","key":"a", "owner_id":"owner", "intent_token":"intent", "server_keyup_verified":True, "server_key_down_after_keyup":False, "server_sync_completed":True, "cancel_requested_after_sync":False, "release_mode":"owner_deadline", "timed_ticket":"t", "timed_deadline_ns":100, "timed_armed_ns":90, "owner_keyrelease_started_ns":100, "owner_keymap_sampled_ns":101}
        value={"ticket":"t", "keys":["a"], "deadline_ns":100, "armed_ns":90, "status":"released", "receipts":[row], "intent_token":"intent"}
        rpc._validate_timed_result(value,[row],ticket="t",intent_token="intent")
        for changed, records in ((dict(value,ticket="bad"),[row]),(value,[]),(dict(value,receipts=[dict(row,server_keyup_verified=False)]),[row]),(dict(value,deadline_ns=102),[row]),(dict(value,armed_ns=91),[row]),(dict(value,receipts=[dict(row,cancel_requested_after_sync=True)]),[dict(row,cancel_requested_after_sync=True)])):
            with self.assertRaises(ValueError):rpc._validate_timed_result(changed,records,ticket="t",intent_token="intent")
    def test_explicit_release_allows_immediate_interrupted_result(self):
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot("source",0);lease=bound(backend)
            fake.keysym_to_keycode=lambda value:{ord("a"):38}.get(value,0)
            a,b=socket.socketpair();outcome=[]
            thread=threading.Thread(target=lambda:outcome.append(rpc.serve_owner(b,backend.owner,display=":fake",service_id="timed",timed_up=True)))
            thread.start();client=rpc.OwnerRpcClient(a,display=":fake",service_id="timed",timeout=2,timed_up=True)
            try:
                admission=client.call("down",lease,"a")
                client.call("arm_timed_up",lease,{"ticket":"abort","keys":["a"],"deadline_ns":admission["input_ack_ns"]+3_000_000_000})
                self.assertTrue(client.call("release",lease)["verified"])
                result=client.call("take_timed_up",lease,"abort")
                self.assertEqual(result["status"],"interrupted")
            finally:
                client.close();thread.join(3)
            self.assertFalse(thread.is_alive())
    def test_opt_in_releases_during_worker_stall(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot("source",0); lease=bound(backend)
            fake.keysym_to_keycode=lambda value:{ord("a"):38}.get(value,0)
            a,b=socket.socketpair(); outcome=[]
            thread=threading.Thread(target=lambda:outcome.append(rpc.serve_owner(b,backend.owner,display=":fake",service_id="timed",timed_up=True)))
            thread.start(); client=rpc.OwnerRpcClient(a,display=":fake",service_id="timed",timeout=2,timed_up=True)
            try:
                admission=client.call("down",lease,"a")
                deadline=admission["input_ack_ns"]+400_000_000
                client.call("arm_timed_up",lease,{"ticket":"first","keys":["a"],"deadline_ns":deadline})
                before=client._next_id
                with self.assertRaises(ValueError): client.call("take_timed_up",lease,"first")
                self.assertEqual(client._next_id,before)
                time.sleep(.55)  # worker is not servicing the owner during this interval
                self.assertEqual(fake.down,set())
                result=client.call("take_timed_up",lease,"first")
                self.assertEqual(result["status"],"released")
                self.assertTrue(result["receipts"][0]["server_keyup_verified"])
                self.assertGreaterEqual(result["receipts"][0]["owner_keyrelease_started_ns"],deadline)
                self.assertEqual(client.call("release_state",lease)["owned_keycodes"],[])
                self.assertTrue(client.close()["verified"])
            finally:
                client.close();thread.join(3)
            self.assertFalse(thread.is_alive())

if __name__=="__main__": unittest.main()
