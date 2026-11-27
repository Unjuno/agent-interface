"""Timed release is owned by the input thread, not the observation worker."""
import threading
import time
import unittest
from unittest.mock import patch

import input_owner_v12 as module
from test_input_owner_v12_cleanup_after_explicit_up import FakeDisplay, Lease

class OwnerTimedUpTests(unittest.TestCase):
    def setUp(self):
        self.display = FakeDisplay(); self.display.drop_next_key_release = False
        self.keyup = threading.Event()
        def event(_display, kind, code):
            if kind == module.X.KeyPress: self.display.down.add(code)
            elif kind == module.X.KeyRelease:
                if self.display.fail_key_release_attempts:
                    self.display.fail_key_release_attempts-=1
                    raise RuntimeError("synthetic release failure")
                self.display.down.discard(code); self.keyup.set()
        self.patches = [patch.object(module.display, "Display", return_value=self.display),
                        patch.object(module.XK, "string_to_keysym", side_effect=lambda key:ord(key)),
                        patch.object(module.xtest, "fake_input", side_effect=event)]
        for p in self.patches: p.start()
        self.owner = module.InputOwner(":fake"); self.lease = Lease(); self.lease.intent_token="test"
    def tearDown(self):
        self.owner.close()
        for p in reversed(self.patches): p.stop()
    def arm(self, delay_ms=40):
        self.owner.call("down",self.lease,"W")
        end=time.perf_counter_ns()+delay_ms*1_000_000
        self.owner.call("arm_timed_up",self.lease,{"ticket":"one", "keys":["W"], "deadline_ns":end})
        return end
    def test_down_and_arm_is_atomic_on_owner_thread(self):
        admission=self.owner.call("down_timed",self.lease,{"key":"W","ticket":"atomic","duration_ms":50})
        self.assertEqual(admission["event"],"input_admission")
        deadline=admission["timed_deadline_ns"]
        self.assertEqual(deadline,admission["input_ack_ns"]+50_000_000)
        armed=admission["timed_armed_ns"]
        self.assertLessEqual(admission["input_ack_ns"],armed)
        self.assertLess(armed,deadline)
        self.assertTrue(self.keyup.wait(1))
        result=self.owner.call("take_timed_up",self.lease,"atomic")
        self.assertEqual(result["status"],"released")
        self.assertEqual(result["receipts"][0]["timed_armed_ns"],armed)
        self.assertGreaterEqual(result["receipts"][0]["owner_keyrelease_started_ns"],deadline)
    def test_collection_dequeued_before_deadline_but_handled_after_it(self):
        admission=self.owner.call('down_timed',self.lease,{'key':'W','ticket':'boundary','duration_ms':180})
        deadline=admission['timed_deadline_ns']
        original=self.owner.requests.get
        def crossing_deadline(*args,**kwargs):
            request=original(*args,**kwargs)
            if request[0]=='take_timed_up':
                remaining=(deadline-time.perf_counter_ns())/1e9
                if remaining>0:time.sleep(remaining+.005)
            return request
        with patch.object(self.owner.requests,'get',side_effect=crossing_deadline):
            time.sleep(.01)  # Let an earlier unpatched queue wait finish.
            result=self.owner.call('take_timed_up',self.lease,'boundary')
        self.assertEqual(result['status'],'released')
        self.assertTrue(result['receipts'][0]['server_keyup_verified'])
        self.assertEqual(self.display.down,set())
    def test_atomic_press_late_ack_is_released_and_not_success(self):
        self.lease.deadline=time.perf_counter_ns()+80_000_000
        original=self.display.sync;calls=[]
        def slow_first_sync():
            if not calls:time.sleep(.12)
            calls.append(True);original()
        self.display.sync=slow_first_sync
        with self.assertRaises(module.DecisionRequired):
            self.owner.call("down_timed",self.lease,{"key":"W","ticket":"late","duration_ms":20})
        self.assertEqual(self.display.down,set())
        self.assertTrue(self.lease.cancel.is_set())
        self.assertTrue(any(row.get("event")=="owner_release" and row.get("verified") is True for row in self.owner.records))
    def test_atomic_press_rejects_invalid_parameters_without_input(self):
        for value in ({"key":"W","ticket":"x","duration_ms":True},
                      {"key":"W","ticket":"x","duration_ms":0},
                      {"key":"W","ticket":"","duration_ms":10}):
            with self.subTest(value=value),self.assertRaises(ValueError):self.owner.call("down_timed",self.lease,value)
        self.assertEqual(self.display.down,set())
    def test_release_occurs_without_observation_worker_or_cancel(self):
        end=self.arm()
        self.assertTrue(self.keyup.wait(1))
        result=self.owner.call("take_timed_up",self.lease,"one")
        self.assertEqual(result["status"],"released")
        self.assertTrue(result["receipts"][0]["server_keyup_verified"])
        self.assertEqual(result["receipts"][0]["timed_ticket"],"one")
        self.assertEqual(result["receipts"][0]["timed_deadline_ns"],end)
        self.assertGreaterEqual(result["receipts"][0]["owner_keyrelease_started_ns"],end)
        self.assertFalse(self.lease.cancel.is_set())
        self.assertEqual(self.display.down,set())
    def test_old_ticket_cannot_release_a_later_hold(self):
        self.arm();self.assertTrue(self.keyup.wait(1))
        with self.assertRaises(ValueError):self.owner.call("take_timed_up",self.lease,"wrong")
        with self.assertRaises(ValueError):self.owner.call("down",self.lease,"A")
        self.owner.call("take_timed_up",self.lease,"one")
        self.owner.call("down",self.lease,"A")
        with self.assertRaises(ValueError):self.owner.call("take_timed_up",self.lease,"one")
        self.assertIn(66,self.display.down)
    def test_early_take_reuse_and_wrong_owner_are_rejected(self):
        self.arm(100)
        with self.assertRaises(ValueError):self.owner.call("take_timed_up",self.lease,"one")
        other=Lease();other.intent_token="other"
        with self.assertRaises(ValueError):self.owner.call("take_timed_up",other,"one")
        self.assertTrue(self.keyup.wait(1));self.owner.call("take_timed_up",self.lease,"one")
        self.owner.call("down",self.lease,"W")
        with self.assertRaises(ValueError):
            self.owner.call("arm_timed_up",self.lease,{"ticket":"one","keys":["W"],"deadline_ns":time.perf_counter_ns()+50_000_000})
    def test_arm_rejects_mismatched_keys_and_expired_deadline(self):
        self.owner.call("down",self.lease,"W")
        for payload in (
            {"ticket":"x", "keys":["A"], "deadline_ns":time.perf_counter_ns()+200_000_000},
            {"ticket":"x", "keys":["W","W"], "deadline_ns":time.perf_counter_ns()+200_000_000},
            {"ticket":"x", "keys":["W"], "deadline_ns":time.perf_counter_ns()-1},
            {"ticket":"x", "keys":["W"], "deadline_ns":self.lease.deadline},
        ):
            with self.subTest(payload=payload),self.assertRaises(ValueError):self.owner.call("arm_timed_up",self.lease,payload)
        self.assertIn(65,self.display.down)
    def test_program_expiry_overrides_completed_timed_release(self):
        self.arm();self.assertTrue(self.keyup.wait(1));self.lease.deadline=time.perf_counter_ns()-1
        self.assertEqual(self.owner.call("take_timed_up",self.lease,"one")["status"],"expired")
    def test_unverified_keyup_does_not_become_success(self):
        self.owner.call("down",self.lease,"W")
        self.display.fail_key_release_attempts=10
        self.owner.call("arm_timed_up",self.lease,{"ticket":"one","keys":["W"],"deadline_ns":time.perf_counter_ns()+40_000_000})
        time.sleep(.1)
        result=self.owner.call("take_timed_up",self.lease,"one")
        self.assertEqual(result["status"],"unverified")
        with self.assertRaises(RuntimeError):self.owner.call("down",self.lease,"A")
        self.display.fail_key_release_attempts=0
        self.owner.call("release",self.lease)
    def test_cancel_after_keyup_before_collection_is_not_success(self):
        self.arm();self.assertTrue(self.keyup.wait(1))
        self.lease.cancel.set()
        self.assertEqual(self.owner.call("take_timed_up",self.lease,"one")["status"],"cancelled")
    def test_cancel_cannot_be_misreported_as_timed_success(self):
        self.arm(200);self.lease.cancel.set();self.assertTrue(self.keyup.wait(1))
        result=self.owner.call("take_timed_up",self.lease,"one")
        self.assertEqual(result["status"],"cancelled")
        self.assertEqual(self.display.down,set())

if __name__=="__main__":unittest.main()
