import unittest
from research.live_control.calc_compiled_target_v1 import make_calc_interface_factory
from research.live_control import test_calc_compiled_method_v1 as fixture

class CalcTargetTests(unittest.TestCase):
 def test_final_revalidated_target_drives_all_core_admissions(self):
  factory=make_calc_interface_factory(interface_id='i',session_scope='s',surface='calc')
  count,result=fixture.CalcMethodTests().run_case(outer='succeeded',factory=factory,promote=True)
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED')
  self.assertEqual(count['admissions'],['new-sheet','new-save','new-confirm'])
  self.assertEqual(result['selected_target']['id'],'new')
 def test_malformed_duplicate_and_unbound_target_are_rejected(self):
  factory=make_calc_interface_factory(interface_id='i',session_scope='s',surface='calc')
  for target in [None,{}, {'sheet':'a','save':'a','confirm':'c'}, {'sheet':'a','save':'b','confirm':[]}]:
   with self.subTest(target=target):
    with self.assertRaises(ValueError):factory({'target':target})