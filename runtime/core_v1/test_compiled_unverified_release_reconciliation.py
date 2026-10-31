"""A returned execution with unverified release must preserve reconciliation identity."""
import unittest
from runtime.core_v1.test_compiled_gui import Driver

class UnverifiedReleaseTests(unittest.TestCase):
 def test_unverified_completed_entry_preserves_unresolved_identity(self):
  d=Driver(released=False);r=d.run();self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'));self.assertEqual(r['completed_transitions'],0);self.assertEqual(len(d.calls['execute']),1);self.assertEqual(d.calls['verify_effect'],[])
  self.assertEqual(r['unresolved_execution'],{'action':'enter','reason':'release_unverified','release_verified':False,'input_dispatched':None,'action_id':'1','effect_ref':'effect'})
 def test_second_action_retains_verified_prefix_and_unresolved_save(self):
  d=Driver();execute=d.execute
  def second(p):
   t=execute(p)
   if len(d.calls['execute'])==2:t['release']['keys_down']=['x']
   return t
  d.execute=second;r=d.run();self.assertEqual(r['completed_transitions'],1);self.assertEqual(r['transitions'][0]['action'],'enter');self.assertEqual(r['unresolved_execution']['action'],'save');self.assertEqual(r['unresolved_execution']['action_id'],'2');self.assertEqual(r['unresolved_execution']['reason'],'release_unverified')
 def test_explicit_preinput_refusal_retains_existing_no_input_path(self):
  d=Driver();execute=d.execute
  def refusal(p):
   t=execute(p);t.update(status='refused',input_dispatched=False);t['release']['verified']=False;return t
  d.execute=refusal;r=d.run();self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','execution_refused'));self.assertNotIn('unresolved_execution',r)
 def test_delivery_flag_is_preserved_without_inventing_neutrality(self):
  for delivered in (True,False):
   with self.subTest(delivered=delivered):
    d=Driver(released=False);execute=d.execute
    def execute_with_flag(p):
     t=execute(p);t['input_dispatched']=delivered
     if not delivered:t.update(status='refused');t['release']['keys_down']=['held']
     return t
    d.execute=execute_with_flag;r=d.run();self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertIs(r['unresolved_execution']['input_dispatched'],delivered);self.assertIs(r['unresolved_execution']['release_verified'],False)
 def test_opaque_reference_is_not_copied_into_unresolved_record(self):
  d=Driver(released=False);execute=d.execute
  def opaque(p):
   t=execute(p);t['effect_ref']=object();return t
  d.execute=opaque;r=d.run();self.assertIsNone(r['unresolved_execution']['effect_ref'])
if __name__=='__main__':unittest.main()
