"""Convert owner-timed receipts to a truthful task release transition."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"live_control"))
from doom_owner_thread_release_batch_backend_v1 import build_timed_transition

def evidence():
    admission={"event":"input_admission","id":"approach-1","step":0,"key":"Up","keycode":111,"owner_id":"owner","intent_token":"token","admitted_ns":110,"input_ack_ns":120,"valid_until_ns":1000,"timed_ticket":"ticket","timed_deadline_ns":220,"timed_armed_ns":125}
    attempt={"attempt":1,"keyrelease_started_ns":220,"sync_returned_ns":221,"keymap_sampled_ns":222,"server_key_down_before":True,"server_key_down_after":False}
    receipt={"event":"owner_explicit_keyup","operation":"up","key":"Up","keycode":111,"owner_id":"owner","intent_token":"token","valid_until_ns":1000,"owner_keyrelease_started_ns":220,"owner_sync_returned_ns":221,"owner_keymap_sampled_ns":222,"server_keyup_verified":True,"server_keyup_attempt_count":1,"server_keyup_attempts":[attempt],"server_key_down_after_keyup":False,"key_state_source":"x11_query_keymap","server_sync_completed":True,"physical_verification_authoritative":False,"cancel_requested_after_sync":False,"release_batch_initial_up_count":1,"release_batch_key_order":["Up"],"release_mode":"owner_deadline","timed_ticket":"ticket","timed_deadline_ns":220,"timed_armed_ns":125}
    result={"status":"released","ticket":"ticket","keys":["Up"],"deadline_ns":220,"armed_ns":125,"intent_token":"token","receipts":[receipt]}
    return admission,result,[receipt]

class TimedTransitionTests(unittest.TestCase):
    def test_builds_bound_transition_from_complete_owner_record(self):
        admission,result,records=evidence()
        row=build_timed_transition(admission,result,records,record_count=0,dispatch_ns=100,returned_ns=250)
        self.assertEqual(row["event"],"input_release_transition")
        self.assertEqual(row["release_mode"],"owner_deadline")
        self.assertEqual(row["owner_thread_keyup_receipt"],records[0])
        self.assertTrue(row["owner_transition_verified"])
        self.assertEqual(row["admission_receipt"],dict(admission,operation="down"))
    def test_refuses_changed_missing_late_or_unverified_evidence(self):
        for case in ("ticket","deadline","armed","owner","record","early","late","cancel","status","duplicate"):
            admission,result,records=evidence();receipt=result["receipts"][0]
            if case=="ticket":result["ticket"]="other"
            if case=="deadline":receipt["timed_deadline_ns"]-=1
            if case=="armed":receipt["timed_armed_ns"]+=1
            if case=="owner":receipt["owner_id"]="other"
            if case=="record":records=[]
            if case=="early":receipt["owner_keyrelease_started_ns"]=219;receipt["server_keyup_attempts"][0]["keyrelease_started_ns"]=219
            if case=="late":admission["valid_until_ns"]=249
            if case=="cancel":receipt["cancel_requested_after_sync"]=True
            if case=="status":result["status"]="cancelled"
            if case=="duplicate":records.append(copy.deepcopy(receipt))
            with self.subTest(case=case),self.assertRaises(ValueError):
                build_timed_transition(admission,result,records,record_count=0,dispatch_ns=100,returned_ns=250)

if __name__=="__main__":unittest.main()
