"""Offline Calc-shaped receipt through the actual compiled caller/core."""
import json, time, unittest
from pathlib import Path
from research.live_control.calc_compiled_stage_terminal_v1 import to_core_terminal, make_stage_executor
from research.live_control.integrated_efficiency_compiled_adapter_v2 import compile_form_method, EXPECTED_METHOD_CONTRACT
from research.live_control.integrated_efficiency_compiled_execution_v2 import run_compiled_interface_in_caller

class CalcHandoffTests(unittest.TestCase):
 def run_case(self, refuse=False, sink_fail=False):
  path=Path(__file__).parent/'results'/'calc-table-live-01'/'save'/'receipt.json'
  source=json.loads(path.read_bytes());state={'observations':0,'inputs':0,'outer_verify':0,'projection':[]}
  interface=compile_form_method(interface_id='calc-inert',session_scope='scope',surface='calc',field_handle='cell',submit_handle='save',method_contract=EXPECTED_METHOD_CONTRACT)
  def observe(_):
   state['observations']+=1
   return {'sequence':state['observations'],'captured_ns':time.perf_counter_ns(),'surface':'calc',
    'predicates':{'field_pixels_changed':False,'field_value_matches_task':False,'field_target_present':True,'submit_target_present':True,'submission_pixels_changed':False},
    'evidence_ref':'inert','evidence_digest':'inert'}
  def admit(payload):return {'eligible':not refuse,'status':'stale' if refuse else 'revalidated','authorization':None if refuse else 'inert',
    'expected_sequence':payload['observation']['sequence'],'valid_until_ns':time.perf_counter_ns()+1_000_000_000}
  def run_stage(_):
   state['inputs']+=1;return source
  def retain(value):
   if sink_fail: raise OSError('inert sink failure')
   state['projection'].append(value['projection'])
  execute=make_stage_executor(run_stage,retain)
  def verify(_):state['outer_verify']+=1;return {'status':'succeeded','evidence_ref':'independent'}
  spec={'target':'calc-inert','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
   'cached_target':{'id':'calc-inert'},'repair_on':[],'local_repair_on':[],'session_id':'inert'}
  caller={'reuse_revalidate':lambda _: {'status':'revalidated'},'final_revalidate':lambda _: {'status':'revalidated'},
   'verify_effect':verify,'journal':lambda _:None}
  adapters={'observe':observe,'admit':admit,'execute':execute,'verify_effect':lambda _: {'status':'succeeded','evidence_ref':'unused'},'cancelled':lambda:False}
  result=run_compiled_interface_in_caller(spec,caller,lambda _:interface,adapters)
  if sink_fail:
   self.assertEqual(state['inputs'],1);self.assertEqual(state['outer_verify'],0)
   self.assertEqual(result['outcome'],'CALLER_FAILED');self.assertIsNone(result['compiled_execution_receipt'])
   self.assertEqual(result['delivery'],'delivery_uncertain')
   held=execute.snapshot();self.assertEqual(held['receipt'],source)
   self.assertEqual(held['projection']['delivery'],'unknown')
   return
  if refuse:
   self.assertEqual(state['inputs'],0);self.assertEqual(state['outer_verify'],0)
   self.assertEqual(result['delivery'],'not_attempted');self.assertEqual(result['compiled_execution_receipt']['reason'],'stale_symbol')
   return
  self.assertEqual(state['inputs'],1);self.assertEqual(state['outer_verify'],0)
  self.assertEqual(state['projection'][0]['delivery'],'unknown');self.assertFalse(state['projection'][0]['replay_permitted'])
  self.assertEqual(result['outcome'],'EXECUTION_INCOMPLETE');self.assertEqual(result['delivery'],'delivery_uncertain')
  self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],0)
 def test_interrupted_possible_input_stops_before_second_action(self): self.run_case()

 def test_stale_target_never_invokes_stage(self): self.run_case(refuse=True)

 def test_sink_failure_does_not_retry_input(self): self.run_case(sink_fail=True)

 def test_standalone_bridge_never_promotes_completion_or_grants_authority(self):
  receipt={'format':'decision-receipt-v4','reported_state':'terminal','program_write_may_have_been_attempted':True,
   'terminals':[{'record':{'event':'terminal','status':'completed','steps_completed':1,
    'release':{'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[]}}}]}
  terminal,projection=to_core_terminal(receipt)
  self.assertEqual(projection['disposition'],'completed_unverified')
  self.assertEqual(terminal['status'],'delivery_uncertain')
  self.assertNotIn('input_dispatched',terminal);self.assertIsNone(terminal['effect_ref'])
