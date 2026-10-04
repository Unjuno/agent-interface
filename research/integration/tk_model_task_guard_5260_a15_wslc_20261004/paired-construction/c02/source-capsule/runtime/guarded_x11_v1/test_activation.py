"""Explicit activation must not resume editing or restore stale aliases."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from runtime.guarded_x11_v1.bridge import NativeHandleBridge

class ActivationTests(unittest.TestCase):
 def setUp(self):
  self.bridge=object.__new__(NativeHandleBridge)
  self.bridge.target='app';self.bridge.backend=SimpleNamespace(targets={'app':SimpleNamespace(id=123)})
  self.bridge.session=SimpleNamespace(recovery_required=False)
  self.bridge.sequence=4;self.bridge.binding_revision=2;self.bridge.scope='native-x11:test'
  self.bridge.active=None;self.bridge.review_required=False;self.bridge._save=Mock()
  p=patch('runtime.guarded_x11_v1.bridge.dispatch_in_session')
  self.dispatch=p.start();self.addCleanup(p.stop)
  self.dispatch.return_value={'status':'returned','result':{'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}}
 def activate(self,**changes):
  args=dict(window_id=123,source_sequence=4,current_binding_revision=2,expires_at_ns=5000,timeout_ms=300)
  args.update(changes)
  return self.bridge.activate_window(**args)
 def test_only_activation_and_release_use_existing_admission(self):
  result=self.activate()
  program=self.dispatch.call_args.args[1]
  self.assertEqual(program['ops'],[{'op':'activate','target':'app','timeout_ms':300},{'op':'release_all'}])
  self.assertEqual(program['source'],{'observation_seq':4,'binding_revision':2})
  self.assertEqual(program['authority']['expires_at_ns'],5000)
  self.assertEqual(result['status'],'completed')
  self.assertTrue(self.bridge.review_required)
  self.assertEqual(self.bridge.binding_revision,2)
  self.bridge._save.assert_called()
 def test_foreign_window_stale_source_and_revision_never_dispatch(self):
  for changes in [{'window_id':456},{'window_id':True},{'source_sequence':3},{'source_sequence':True},{'current_binding_revision':1},{'current_binding_revision':True},{'expires_at_ns':True},{'timeout_ms':True},{'timeout_ms':2001}]:
   with self.subTest(changes=changes):
    result=self.activate(**changes)
    self.assertEqual(result['status'],'refused');self.assertFalse(result['input_dispatched'])
    self.assertFalse(self.bridge.review_required);self.dispatch.assert_not_called()
 def test_busy_or_uncertain_input_blocks_activation(self):
  for active,recovery in [(('field',[0,0]),False),(None,True)]:
   self.bridge.active=active;self.bridge.session.recovery_required=recovery
   result=self.activate();self.assertEqual(result['status'],'refused')
   self.dispatch.assert_not_called()
 def test_core_refusal_keeps_original_binding_and_review_state(self):
  self.dispatch.return_value={'status':'returned','result':{'status':'refused','error':'LEASE_EXPIRED','input_dispatched':False}}
  result=self.activate();self.assertEqual(result['error'],'LEASE_EXPIRED')
  self.assertFalse(self.bridge.review_required)
  self.bridge.review_required=True
  self.activate()
  self.assertTrue(self.bridge.review_required)
 def test_partial_or_unknown_activation_requires_review_without_replay(self):
  for reply in [{'status':'returned','result':{'status':'execution_failed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}}, {'status':'runtime_failed','error':'lost receipt'}]:
   self.dispatch.reset_mock();self.dispatch.return_value=reply;self.bridge.review_required=False
   result=self.activate();self.assertTrue(self.bridge.review_required)
   self.dispatch.assert_called_once();self.assertNotEqual(result['status'],'completed')

if __name__=='__main__':unittest.main()
