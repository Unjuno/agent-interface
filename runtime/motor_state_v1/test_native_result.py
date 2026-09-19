import unittest
from .adapter import SCHEMA
from .native_result import NativeResultError, motor_state_from_native_result

def raw():
    return {"result_id":"r1","target":{"surface_id":"surface-1","frame":"window-client"},"focus_confirmed":True,"ack_id":"ack-1","observation":{"observation_id":"obs-1","observed_pointer":{"x":1,"y":2}},"execution":{"transport_passed":True},"release":{"final_release_verified":True}}

class NativeResultTests(unittest.TestCase):
    def test_complete_result_maps_to_valid_state(self):
        row=motor_state_from_native_result(raw()); self.assertEqual(row["schema"],SCHEMA); self.assertEqual(row["uncertainty"],"NONE")
    def test_missing_ack_is_uncertain(self):
        v=raw(); v.pop("ack_id"); row=motor_state_from_native_result(v); self.assertNotEqual(row["uncertainty"],"NONE"); self.assertEqual(row["input_ack"]["status"],"UNKNOWN")
    def test_empty_pointer_is_uncertain(self):
        v=raw(); v["observation"]["observed_pointer"]={}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_null_pointer_is_uncertain(self):
        v=raw(); v["observation"]["observed_pointer"]={"x":None,"y":2}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_string_pointer_is_uncertain(self):
        v=raw(); v["observation"]["observed_pointer"]={"x":"1","y":2}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_bool_pointer_is_uncertain(self):
        v=raw(); v["observation"]["observed_pointer"]={"x":True,"y":2}; self.assertNotEqual(motor_state_from_native_result(v)["uncertainty"],"NONE")
    def test_missing_observation_is_uncertain(self):
        v=raw(); v["observation"]=None; self.assertEqual(motor_state_from_native_result(v)["uncertainty"],"OS_UNCONFIRMED")
    def test_release_error_precedes_verified_flag(self):
        v=raw(); v["release"]={"error":"release_failed","final_release_verified":True}; self.assertEqual(motor_state_from_native_result(v)["release"]["status"],"FAILED")
    def test_bad_revision_is_rejected(self):
        v=raw(); v["binding_revision"]="1"
        with self.assertRaises(NativeResultError): motor_state_from_native_result(v)
    def test_authority_promotion_is_rejected(self):
        v=raw(); v["extends_lease"]=True
        with self.assertRaises(NativeResultError): motor_state_from_native_result(v)
if __name__=="__main__": unittest.main()