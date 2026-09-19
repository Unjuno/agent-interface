import copy, unittest
from adapter import MotorStateAdapterError, motor_state_from_native_result

def raw():
    return {"result_id":"r1","owner_id":"o1","binding_revision":2,
      "target":{"surface_id":"s1","frame":"window_client"},"focus_confirmed":True,
      "observation":{"observation_id":"obs1","observed_pointer":{"x":1,"y":2}},
      "execution":{"transport_passed":True},"release":{"final_release_verified":True},
      "ack_id":"a1","held_keys":[],"held_buttons":[]}

class AdapterTests(unittest.TestCase):
    def test_confirmed_mapping(self):
        got=motor_state_from_native_result(raw())
        self.assertEqual(got["uncertainty"],"NONE")
        self.assertEqual(got["input_ack"]["status"],"ACKED")
        self.assertEqual(got["release"]["status"],"VERIFIED_EMPTY")
    def test_missing_observation_is_uncertain(self):
        x=raw(); x["observation"]=None
        got=motor_state_from_native_result(x)
        self.assertEqual(got["uncertainty"],"OS_UNCONFIRMED")
        self.assertIsNone(got["observed_pointer"])
    def test_focus_and_surface_unknown(self):
        x=raw(); x["focus_confirmed"]=False; x["target"]={}
        got=motor_state_from_native_result(x)
        self.assertEqual(got["uncertainty"],"SURFACE_UNKNOWN")
    def test_failed_release_is_retained(self):
        x=raw(); x["release"]={"error":"cleanup_failed"}; x["execution"]["transport_passed"]=False
        got=motor_state_from_native_result(x)
        self.assertEqual(got["release"]["status"],"FAILED")
        self.assertEqual(got["events"][0]["type"],"RELEASE_TRANSITION")
    def test_authority_promotion_rejected_and_input_unchanged(self):
        x=raw(); before=copy.deepcopy(x); x["extends_lease"]=True
        with self.assertRaises(MotorStateAdapterError): motor_state_from_native_result(x)
        self.assertEqual(x,before | {"extends_lease":True})
    def test_application_effect_is_not_invented(self):
        x=raw(); x["task_success"]=True
        got=motor_state_from_native_result(x)
        self.assertNotIn("task_success",got)

if __name__=="__main__": unittest.main()
