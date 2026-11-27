"""Regression test for joining backend-emitted key admissions to batch releases."""
import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("doom_owner_thread_release_batch_backend_v1.py")

class Lease:
    intent_token = "lease-token"

class Owner:
    owner_id = "owner-1"
    def __init__(self): self.records=[]
    def call(self,operation,lease=None,value=None):
        if operation=="down":
            return {"event":"input_admission","key":value,"owner_id":self.owner_id,
                    "intent_token":lease.intent_token,"valid_until_ns":1000,
                    "admitted_ns":10,"input_ack_ns":20}
        if operation=="up_batch":
            receipt={"event":"owner_explicit_keyup","operation":"up","key":value[0],
                     "owner_id":self.owner_id,"intent_token":lease.intent_token,
                     "valid_until_ns":1000,"server_sync_completed":True,
                     "physical_verification_authoritative":False}
            self.records.append(receipt)
            return [{"event":"input_release_transition","operation":"up","key":value[0],
                     "owner_id":self.owner_id,"intent_token":lease.intent_token,
                     "valid_until_ns":1000,"release_call_started_ns":30,
                     "release_call_returned_ns":40,"ordinary_release_candidate":True,
                     "owner_thread_keyup_receipt":receipt,
                     "owner_thread_keyup_verified":True}]
        if operation=="input_state":
            return {"owner_id":self.owner_id,"sample_started_ns":50,
                    "sample_finished_ns":60,"owned_keycodes":[]}
        raise AssertionError(operation)

def load_backend():
    base=types.ModuleType("doom_typed_release_backend_v2")
    class Base:
        def release_all(self): return {"verified":True}
    base.Backend=Base;base.suite=object()
    owner_mod=types.ModuleType("input_transition_owner_v4");owner_mod.InputOwner=object
    with patch.dict(sys.modules,{"doom_typed_release_backend_v2":base,"input_transition_owner_v4":owner_mod}):
        spec=importlib.util.spec_from_file_location("_tested_release_batch_backend",MODULE_PATH)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
        spec.loader.exec_module(module)
    return module.Backend

class AdmissionLinkTest(unittest.TestCase):
    def make_backend(self):
        Backend=load_backend();backend=Backend.__new__(Backend)
        backend.owner=Owner();backend.lease=Lease();backend.held=set()
        backend._input_event_context=("program",0);backend._release_batch=threading.local()
        backend._last_release_batch_delivery=None;backend._admission_receipts={};emitted=[]
        backend.emit=lambda row:emitted.append(dict(row))
        return backend,emitted

    def test_release_batch_carries_the_exact_owner_bound_admission(self):
        backend,emitted=self.make_backend()
        backend.raw("w",True)
        context={"rows":[],"identifier":"probe","step":0,"pending_ups":[]}
        backend._release_batch.context=context
        backend.raw("w",False)
        release=next(row for row in emitted if row.get("event")=="input_release_transition")
        expected={"event":"input_admission","operation":"down","key":"w",
                  "owner_id":"owner-1","intent_token":"lease-token",
                  "valid_until_ns":1000,"admitted_ns":10,"input_ack_ns":20,
                  "id":"program","step":0}
        self.assertEqual(release.get("admission_receipt"),expected)
        self.assertIs(release["admission_receipt_valid"],True)

    def test_mismatched_admission_owner_fails_closed(self):
        backend,emitted=self.make_backend()
        backend.raw("w",True)
        backend._admission_receipts["w"][0]["owner_id"]="different-owner"
        context={"rows":[],"identifier":"probe","step":0,"pending_ups":[]}
        backend._release_batch.context=context
        backend.raw("w",False)
        release=next(row for row in emitted if row.get("event")=="input_release_transition")
        self.assertIsNone(release["admission_receipt"])
        self.assertIs(release["admission_receipt_valid"],False)

    def test_ack_after_release_start_fails_closed(self):
        backend,emitted=self.make_backend()
        backend.raw("w",True)
        backend._admission_receipts["w"][0]["input_ack_ns"]=31
        context={"rows":[],"identifier":"probe","step":0,"pending_ups":[]}
        backend._release_batch.context=context
        backend.raw("w",False)
        release=next(row for row in emitted if row.get("event")=="input_release_transition")
        self.assertIsNone(release["admission_receipt"])
        self.assertIs(release["admission_receipt_valid"],False)

    def test_terminal_release_discards_unmatched_admission_cache(self):
        backend, _ = self.make_backend()
        backend._admission_receipts["stale"] = [{"event":"input_admission"}]
        result=backend.release_all()
        self.assertIs(result["verified"],True)
        self.assertEqual(backend._admission_receipts,{})


    def test_cleanup_timestamp_is_checked_against_release_bracket(self):
        for timestamp, expected in ((29, True), (30, False), (35, False),
                                    (40, False), (41, True), (True, False)):
            with self.subTest(timestamp=timestamp):
                backend, emitted = self.make_backend()
                original_call = backend.owner.call
                def call(operation, lease=None, value=None):
                    result = original_call(operation, lease, value)
                    if operation == "up_batch":
                        backend.owner.records.append({
                            "event": "owner_release", "verified": True,
                            "verified_ns": timestamp, "keys_down": [],
                            "buttons_down": [], "reason": "cancelled",
                        })
                    return result
                backend.owner.call = call
                backend.raw("w", True)
                backend._release_batch.context = {
                    "rows": [], "identifier": "probe", "step": 0, "pending_ups": []}
                backend.raw("w", False)
                release = next(row for row in emitted
                               if row.get("event") == "input_release_transition")
                self.assertIs(release["owner_transition_verified"], expected)



    def test_split_step_preserves_each_release_and_rejects_cross_step_projection(self):
        backend, emitted = self.make_backend()
        parent = type(backend).__mro__[1]
        def execute(instance, step, cancel, identifier, index):
            instance._input_event_context = (identifier, index)
            for key, down in step:
                instance.raw(key, down)
        with patch.object(parent, "execute", execute, create=True):
            backend.execute([("w", True), ("a", True), ("w", False)], None, "program", 0)
            self.assertFalse(any(row.get("event") == "input_release_transition"
                                 for row in emitted))
            backend.execute([("a", False)], None, "program", 1)
        releases = [row for row in emitted if row.get("event") == "input_release_transition"]
        self.assertEqual([(row["key"], row["step"]) for row in releases],
                         [("w", 0), ("a", 1)])
        self.assertTrue(all(row["admission_receipt_valid"] for row in releases))
        from project_v39_release_measurement_v1 import project
        self.assertEqual(project(emitted), {"measurement_ready": False, "rows": []})


if __name__=="__main__":unittest.main()
