import unittest
from runtime.motor_state_v1 import motor_state_from_native_result,MotorStateAdapterError
class T(unittest.TestCase):
 def raw(self): return {"result_id":"r","target":{"surface_id":"s","frame":"window_client"},"focus_confirmed":True,"observation":{"observation_id":"o","observed_pointer":{"x":1}},"execution":{"transport_passed":True},"release":{"final_release_verified":True}}
 def test_map(self):
  x=motor_state_from_native_result(self.raw()); self.assertEqual(x["uncertainty"],"NONE"); self.assertEqual(x["release"]["status"],"VERIFIED_EMPTY")
 def test_missing_is_uncertain(self):
  r=self.raw();r["observation"]=None;self.assertEqual(motor_state_from_native_result(r)["uncertainty"],"OS_UNCONFIRMED")
 def test_authority_reject(self):
  r=self.raw();r["extends_lease"]=True
  with self.assertRaises(MotorStateAdapterError): motor_state_from_native_result(r)
if __name__=="__main__":unittest.main()
