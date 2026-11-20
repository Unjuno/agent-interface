from __future__ import annotations
import copy
import unittest
from .adapter import validate
from .native_result import from_dispatch_result
def context():
    return {"state_id":"s1","owner_id":"o1","owner_revision":2,"observation_id":"obs1","surface_id":"surface1","coordinate_frame":"window_client","commanded_pointer":{"x":10,"y":20}}
class NativeResultBridgeTests(unittest.TestCase):
    def test_completed_release_is_valid_but_still_uncertain_about_os_observation(self):
        result=from_dispatch_result({"result_id":"r1","status":"completed","admission":"accepted","execution":{"releases":[{"verified":True}]}},context=context())
        self.assertEqual(result["accepted"],True); self.assertEqual(result["reason"],"ok"); self.assertEqual(result["state"]["uncertainty"],"OS_UNCONFIRMED"); self.assertEqual(result["state"]["release"]["status"],"VERIFIED_EMPTY"); self.assertEqual(result["state"]["input_ack"]["status"],"ACKED")
    def test_missing_context_fails_closed_without_inventing_ids(self):
        self.assertEqual(from_dispatch_result({"status":"completed"},context={}),{"accepted":False,"reason":"missing_context","uncertainty":"OS_UNCONFIRMED"})
    def test_failed_or_unverified_release_remains_visible(self):
        result=from_dispatch_result({"result_id":"r2","status":"release_unverified","admission":"accepted","execution":{"releases":[{"verified":False}]}},context=context())
        self.assertEqual(result["accepted"],True); self.assertEqual(result["state"]["release"]["status"],"FAILED"); self.assertEqual(result["state"]["events"][0]["type"],"RELEASE_TRANSITION")
    def test_does_not_mutate_context_or_grant_effect(self):
        original=context(); frozen=copy.deepcopy(original); result=from_dispatch_result({"result_id":"r3","status":"refused"},context=original)
        self.assertEqual(original,frozen); self.assertNotIn("task_effect",result["state"]); self.assertNotIn("authority",result["state"])
    def test_validator_rejects_any_attempted_promotion(self):
        result=from_dispatch_result({"result_id":"r4","status":"completed"},context=context()); result["state"]["authority"]={"lease":"extend"}
        self.assertEqual(validate(result["state"]),(False,"unknown_or_authority_field"))
if __name__=="__main__": unittest.main()
