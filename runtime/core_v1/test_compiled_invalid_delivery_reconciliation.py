"""Malformed delivery attestation after execute preserves unknown effect and prefix."""
import unittest
from runtime.core_v1.test_compiled_gui import Driver

class InvalidDeliveryTests(unittest.TestCase):
 def test_bad_flag_after_first_or_second_execution_is_unresolved(self):
  for position in (1,2):
   for value in (0,1,None,'false'):
    with self.subTest(position=position,value=value):
     d=Driver();execute=d.execute
     def bad(payload):
      result=execute(payload)
      if len(d.calls['execute'])==position:result['input_dispatched']=value
      return result
     d.execute=bad;r=d.run();self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'));self.assertEqual(r['completed_transitions'],position-1);self.assertEqual(len(d.calls['execute']),position);self.assertEqual(len(d.calls['verify_effect']),position-1)
     u=r['unresolved_execution'];self.assertEqual(u['action'],('enter','save')[position-1]);self.assertEqual(u['reason'],'invalid_delivery_attestation');self.assertIsNone(u['input_dispatched']);self.assertFalse(u['release_verified']);self.assertEqual(u['action_id'],str(position));self.assertEqual(u['effect_ref'],'effect')
 def test_false_with_nonrefusal_is_unknown_not_preinput(self):
  for status in ('completed','delivery_uncertain'):
   with self.subTest(status=status):
    d=Driver(terminal=status);base=d.execute
    d.execute=lambda p:dict(base(p),input_dispatched=False)
    r=d.run();self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'));self.assertIsNone(r['unresolved_execution']['input_dispatched']);self.assertEqual(len(d.calls['execute']),1)
if __name__=='__main__':unittest.main()
