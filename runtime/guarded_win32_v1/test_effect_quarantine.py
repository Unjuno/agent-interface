import unittest,time
import runtime.guarded_win32_v1.test_late_state as fixture_module

class EffectQuarantineCases(unittest.TestCase):
 def check_change(self,mode):
  b,o,s,raw,e=fixture_module.Cases('test_exact_expiry_consumes_without_capture').fixture();p=s.prepare('button',[1,1]);base=b.pointer_move
  def move(*args):
   base(*args)
   if mode=='after_move':b.user32.GetForegroundWindow.return_value=43
  b.pointer_move=move
  def callback(*args):
   if mode in ('focus','raises'):b.user32.GetForegroundWindow.return_value=43
   if mode=='geometry':b.geometry.return_value={'x':1,'y':0,'width':8,'height':8}
   if mode=='raises':raise RuntimeError('inert predicate failure after focus change')
   return True
  r=s.execute(p['authorization'],verify_effect=callback,effect_deadline_ns=time.monotonic_ns()+1000000000)
  self.assertEqual(r['status'],'completed');self.assertIsNone(r['task_success']);self.assertEqual(e,[['move','fixture',3,3],['release']]);self.assertTrue(o.review_required)
  b.user32.GetForegroundWindow.return_value=42;b.geometry.return_value={'x':0,'y':0,'width':8,'height':8}
  with self.assertRaisesRegex(ValueError,'review required'):s.prepare('button',[1,1])
  self.assertEqual(s.execute(p['authorization'])['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN');self.assertFalse(s.lock.locked())
 def test_focus_change_inside_verifier(self):self.check_change('focus')
 def test_geometry_change_inside_verifier(self):self.check_change('geometry')
 def test_focus_change_after_move_before_capture(self):self.check_change('after_move')
 def test_predicate_exception_after_focus_change(self):self.check_change('raises')

if __name__=='__main__':unittest.main()
