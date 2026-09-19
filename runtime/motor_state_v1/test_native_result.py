import unittest
from .adapter import SCHEMA
from .native_result import NativeResultError, motor_state_from_native_result


def raw():
    return {"result_id":"r1","target":{"surface_id":"surface-1","frame":"window-client"},"focus_confirmed":True,"ack_id":"ack-1","observation":{"observation_id":"obs-1","observed_pointer":{"x":1,"y":2}},"execution":{"transport_passed":True},"release":{"final_release_verified":True}}


class NativeResultTests(unittest.TestCase):
    def test_complete_result_maps_to_valid_state(self):
        row=motor_state_from_native_result(raw()); self.assertEqual(row["schema"],SCHEMA); self.assertEqual(row["uncertainty"],"NONE"); self.assertEqual(row["input_ack"],{"id":"ack-1","status":"ACKED"}); self.assertEqual(row["release"]["status"],"VERIFIED_EMPTY")
    def test_missing_observation_is_uncertain_and_valid(self):
        v=raw(); v["observation"]=None; self.assertEqual(motor_state_from_native_result(v)["uncertainty"],"OS_UNCONFIRMED")
    def test_transport_failure_cannot_emit_none(self):
        v=raw(); v["execution"]={"transport_passed":False}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_missing_pointer_cannot_emit_none(self):
        v=raw(); v["observation"]={"observation_id":"obs-1"}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_empty_pointer_cannot_emit_none(self):
        v=raw(); v["observation"]["observed_pointer"]={}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_missing_ack_cannot_emit_acked_or_none(self):
        v=raw(); del v["ack_id"]; row=motor_state_from_native_result(v); self.assertEqual(row["input_ack"]["status"],"UNKNOWN"); self.assertNotEqual(row["uncertainty"],"NONE")
    def test_release_error_precedes_verified_flag(self):
        v=raw(); v["release"]={"error":"release_failed","final_release_verified":True}; self.assertEqual(motor_state_from_native_result(v)["release"]["status"],"FAILED")
    def test_bad_revision_is_rejected(self):
        v=raw(); v["binding_revision"]="1"; self.assertRaises(NativeResultError,motor_state_from_native_result,v)
    def test_missing_surface_is_rejected(self):
        v=raw(); v["target"]={"frame":"window-client"}; self.assertRaises(NativeResultError,motor_state_from_native_result,v)
    def test_authority_promotion_is_rejected(self):
        v=raw(); v["extends_lease"]=True; self.assertRaises(NativeResultError,motor_state_from_native_result,v)
    def test_raw_input_is_not_mutated(self):
        v=raw(); before=repr(v); motor_state_from_native_result(v); self.assertEqual(repr(v),before)


if __name__=="__main__": unittest.main()
