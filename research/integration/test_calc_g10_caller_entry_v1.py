"""Actual G10 caller entry with inert bridge and retained scoring fixture."""
import hashlib,json,unittest
from pathlib import Path
from research.live_control.calc_g10_caller_v1 import run_g10_in_caller
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
from research.integration.test_calc_g10_fresh_admission_v1 import MintingBridge,interface,bindings,verify
from research.integration.test_calc_g10_caller_score_v1 import predicate,oracle,ROOT

class G10CallerEntryTests(unittest.TestCase):
 def run_case(self,unknown=False,wrong=False,sink_fail=False):
  raw=(ROOT/'runs'/'compiled_ocrlive10'/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  checks=json.loads(raw)['pixel_checks'];blob=(ROOT/'runs'/'compiled_ocrlive10'/'second.fods').read_bytes()
  self.assertEqual(hashlib.sha256(blob).hexdigest(),'9c0efd47b8f145229dd77f3b6380b2f604707c6f4e776045c98b8a19b3a2a2df')
  bridge=MintingBridge();state={'verify':0,'sink':0,'bound':[]};cancel=lambda:False
  def perceive(_,image):
   phase=image.getpixel((0,0))[0];row=checks[phase]
   return {'ready':True,'row_visible':predicate.visible_row_predicate(None if unknown and phase==1 else row['decoded_values'],row['expected_values'])}
  def proposal(native,image):return {'alias':'a1_second','source_sequence':native['sequence'],
   'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  worker=BoundedProposal(proposal,timeout_ms=300,cancelled=cancel)
  def outer(_):
   state['verify']+=1;passed=oracle.score_saved(blob,44 if wrong else 43,47)['pass_effect']
   return {'status':'succeeded' if passed else 'failed','evidence_ref':'saved-fods'}
  def sink(receipt):
   state['sink']+=1;receipt.clear()
   if sink_fail:raise OSError('inert sink failure')
  def build(payload):state['bound'].append(payload['target']['id']);return interface()
  spec={'target':'calc','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
   'cached_target':{'id':'old'},'repair_on':[],'local_repair_on':[],'session_id':'inert'}
  caller={'reuse_revalidate':lambda _: {'status':'revalidated'},
   'final_revalidate':lambda _: {'status':'revalidated','target':{'id':'new'}},
   'verify_effect':outer,'journal':lambda _:None}
  result=run_g10_in_caller(spec,caller,build,bridge,bindings(),perceive=perceive,verify_effect=verify,
   proposal_worker=worker,cancelled=cancel,on_receipt=sink)
  return bridge,state,result
 def test_independent_score_and_final_target(self):
  for wrong,outcome in [(False,'TASK_SUCCEEDED'),(True,'TASK_NOT_VERIFIED')]:
   with self.subTest(wrong=wrong):
    bridge,state,result=self.run_case(wrong=wrong)
    self.assertEqual(result['outcome'],outcome);self.assertEqual(state['bound'],['new'])
    self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],2)
    self.assertEqual((len(bridge.inputs),state['sink'],state['verify']),(2,1,1))
 def test_unknown_effect_keeps_prefix_and_skips_outer_verification(self):
  bridge,state,result=self.run_case(unknown=True)
  self.assertEqual(result['outcome'],'EXECUTION_INCOMPLETE');self.assertEqual(result['delivery'],'confirmed_partial')
  self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],1)
  self.assertEqual((len(bridge.inputs),state['sink'],state['verify']),(1,1,0))
 def test_sink_failure_retains_completed_receipt_without_replay(self):
  bridge,state,result=self.run_case(sink_fail=True)
  self.assertEqual(result['outcome'],'CALLER_FAILED');self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],2)
  self.assertEqual((len(bridge.inputs),state['sink'],state['verify']),(2,1,0))