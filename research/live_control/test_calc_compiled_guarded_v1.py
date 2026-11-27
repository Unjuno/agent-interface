"""Calc-shaped graph with the actual guarded compiled adapter and fake bridge."""
import unittest
from research.live_control.calc_compiled_method_v1 import compile_calc_method
from runtime.guarded_x11_v1.compiled import run
from runtime.guarded_x11_v1.test_compiled import Bridge

class CalcGuardedIntegrationTests(unittest.TestCase):
 def test_real_adapter_accepts_positive_absence_dependencies(self):
  bridge=Bridge()
  interface=compile_calc_method(interface_id='calc',session_scope='private',surface='x11-window-20',
    sheet_handle='sheet',save_handle='save',confirm_handle='confirm')
  bindings={name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('enter','save','confirm')}
  def perceive(_,image):
   phase=image.getpixel((0,0))[0]
   return {'cells_match':phase>=1,'sheet_target_present':True,'save_target_present':True,
    'dialog_present':phase==2,'dialog_absent':phase!=2,'confirm_target_present':True,'saved_indication':phase>=3}
  def verify(payload,native,image):return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}
  result=run(bridge,interface,bindings,perceive=perceive,verify_effect=verify)
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED')
  self.assertEqual(result['completed_transitions'],3);self.assertEqual(len(bridge.inputs),3)
 def test_dialog_appearing_at_input_guard_blocks_click(self):
  class ChangedBridge(Bridge):
   def click(self,*args,**kwargs):
    self.phase=2;self.observe()
    return super().click(*args,**kwargs)
  bridge=ChangedBridge()
  interface=compile_calc_method(interface_id='calc',session_scope='private',surface='x11-window-20',
    sheet_handle='sheet',save_handle='save',confirm_handle='confirm')
  bindings={name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('enter','save','confirm')}
  def perceive(_,image):
   phase=image.getpixel((0,0))[0]
   return {'cells_match':phase>=1,'sheet_target_present':True,'save_target_present':True,
    'dialog_present':phase==2,'dialog_absent':phase!=2,'confirm_target_present':True,'saved_indication':phase>=3}
  result=run(bridge,interface,bindings,perceive=perceive,
    verify_effect=lambda p,n,i:{'status':'succeeded','evidence_ref':p['observation']['evidence_ref']})
  self.assertEqual(bridge.inputs,[]);self.assertEqual(result['completed_transitions'],0)
  self.assertNotEqual(result['outcome'],'TASK_SUCCEEDED')