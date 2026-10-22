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

if __name__=="__main__":unittest.main()
