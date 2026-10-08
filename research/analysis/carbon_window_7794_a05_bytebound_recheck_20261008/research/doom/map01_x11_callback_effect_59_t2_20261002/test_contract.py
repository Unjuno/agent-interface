"""Preformal mutation tests for the client callback effect audit."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("callback_effect_audit",ROOT/"audit.py")
AUDIT=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(AUDIT)
FIXTURE=json.loads((ROOT/"fixture.json").read_text())
FREEZE={"image_digest":AUDIT.IMAGE}

def make_record():
    code,aid,bid=25,100,200
    events=[{"event_id":0,"phase":"positive_held","type":2,"detail":code,"window_id":aid,"received_ns":10},
        {"event_id":1,"phase":"positive_held","type":2,"detail":code,"window_id":aid,"received_ns":20},
        {"event_id":2,"phase":"transfer_a_held","type":2,"detail":code,"window_id":aid,"received_ns":30},
        {"event_id":3,"phase":"transfer_b_held","type":2,"detail":code,"window_id":bid,"received_ns":70}]
    effects=[]
    for eid,w,phase,ts,n in [(0,aid,"positive_held",10,0),(1,aid,"positive_held",20,1),(2,aid,"transfer_a_held",30,2),(3,bid,"transfer_b_held",70,0)]:
        bits=bytearray(32); bits[code//8]|=1<<(code%8)
        effects.append({"effect_id":len(effects),"event_id":eid,"phase":phase,"event_received_ns":ts,"effect_ns":ts+1,"window_id":w,"keycode":code,"effect_name":"movement_tick_counter","before":n,"after":n+1,"focus_window_id":w,"key_down":True,"bitmap_hex":bits.hex()})
    samples=[]
    for label,phase,focus,down,ts in [("positive_pre","positive",aid,False,1),("positive_held","positive",aid,True,2),("positive_post","positive",aid,False,3),("transfer_pre","transfer",aid,False,4),("transfer_a_held","transfer",aid,True,5),("transfer_b_held","transfer",bid,True,6),("transfer_b_end","transfer",bid,True,7),("transfer_post","transfer",bid,False,8)]:
        bits=bytearray(32)
        if down:bits[code//8]|=1<<(code%8)
        samples.append({"label":label,"phase":phase,"focus_window_id":focus,"expected_focus_window_id":focus,"keycode":code,"key_down":down,"bitmap_hex":bits.hex(),"observed_ns":ts})
    actions=[("positive","focus",aid,None),("positive","press",None,2),("positive","release",None,3),("transfer","focus",aid,None),("transfer","press",None,2),("transfer","focus",bid,None),("transfer","release",None,3)]
    actions=[{"phase":p,"operation":op,"window_id":w,"event_type":typ,"started_ns":10+i*10,"sync_returned_ns":11+i*10,"keycode":code} for i,(p,op,w,typ) in enumerate(actions)]
    return {"schema":"issue59-x11-callback-effect-raw-v1","allocation_id":FIXTURE["allocation_id"],"main_sha":FIXTURE["main_sha"],"image_digest":AUDIT.IMAGE,"candidate_invocations":1,"retries":0,"xvfb_tcp_enabled":False,"xvfb_exit_code":0,"xvfb_socket_removed":True,"xvfb_lock_removed":True,"xvfb_stderr":"","keycode":code,"window_a_id":aid,"window_b_id":bid,"repeat_control":{"global_auto_repeat":1},"samples":samples,"actions":actions,"events":events,"callback_effects":effects,"effects_final":{str(aid):3,str(bid):1},"a_received_initial_transfer_press":True,"transfer_b_start_ns":60,"transfer_b_end_ns":80,"transfer_release_action_ns":81}

class AuditContractTests(unittest.TestCase):
    def test_one_to_one_callback_state_yields_pass(self):
        self.assertEqual(AUDIT.result(make_record(),FIXTURE,FREEZE,False)[0],"PASS_X11_CALLBACK_EFFECT_MATCHES_DELIVERED_KEYPRESS")
    def test_missing_b_effect_is_fail(self):
        r=make_record(); r["events"].pop(); r["callback_effects"].pop(); r["effects_final"]["200"]=0
        self.assertEqual(AUDIT.result(r,FIXTURE,FREEZE,False)[0],"FAIL_NO_CALLBACK_EFFECT_IN_NEW_FOCUS")
    def test_counter_jump_rejected(self):
        r=make_record(); r["callback_effects"][3]["after"]=99
        self.assertTrue(any("counter" in e for e in AUDIT.validate(r,FIXTURE,FREEZE,False)))
    def test_effect_without_event_link_rejected(self):
        r=make_record(); r["callback_effects"][3]["event_id"]=999
        self.assertTrue(AUDIT.validate(r,FIXTURE,FREEZE,False))
    def test_wrong_focus_bitmap_rejected(self):
        r=make_record(); r["callback_effects"][3]["key_down"]=False
        self.assertTrue(any("focused/down" in e for e in AUDIT.validate(r,FIXTURE,FREEZE,False)))

if __name__=="__main__":unittest.main(verbosity=2)
