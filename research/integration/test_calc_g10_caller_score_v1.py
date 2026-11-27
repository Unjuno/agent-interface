"""G10-shaped guarded execution with outer caller and retained independent score.

Only fake input/observations and historical saved bytes are used.
"""
import hashlib,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
from research.live_control import integrated_efficiency_compiled_execution_v2 as composition
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
from research.live_control.calc_g10_fresh_admission_v1 import run_with_bounded_fresh_proposal
from research.integration.test_calc_g10_fresh_admission_v1 import MintingBridge,interface,bindings,verify

ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'
def load_pinned(path,digest,name):
 if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('pinned source differs')
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
predicate=load_pinned(ROOT/'effect_predicate.py','44473bbb30194486ccdceb998a6714f28c59db0fac4ed51cee88202275d54eba','g10_pred')
oracle=load_pinned(ROOT/'saved_oracle.py','92def4221091e3d788ce24340d7a3f0f6e2e4dbe9b732164dc97605975f6de0d','g10_oracle')

class G10CallerCompositionTests(unittest.TestCase):
 def run_case(self,expected=(43,47),unknown=False):
  data=(ROOT/'runs'/'compiled_ocrlive10'/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(data).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  checks=json.loads(data)['pixel_checks'];blob=(ROOT/'runs'/'compiled_ocrlive10'/'second.fods').read_bytes()
  digest=hashlib.sha256(blob).hexdigest();self.assertEqual(digest,'9c0efd47b8f145229dd77f3b6380b2f604707c6f4e776045c98b8a19b3a2a2df')
  bridge=MintingBridge();calls={'verify':0,'proposal':0};cancel=lambda:False
  def perceive(_,image):
   phase=image.getpixel((0,0))[0];row=checks[phase]
   decoded=None if unknown and phase==1 else row['decoded_values']
   return {'ready':True,'row_visible':predicate.visible_row_predicate(decoded,row['expected_values'])}
  def proposal(native,image):
   calls['proposal']+=1;return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  worker=BoundedProposal(proposal,timeout_ms=300,cancelled=cancel)
  def guarded(graph,_):
   return run_with_bounded_fresh_proposal(bridge,graph,bindings(),perceive=perceive,verify_effect=verify,proposal_worker=worker,cancelled=cancel)
  def outer(_):
   calls['verify']+=1;score=oracle.score_saved(blob,*expected)
   return {'status':'succeeded' if score['pass_effect'] else 'failed',
           'evidence_ref':'saved-fods','evidence_digest':digest}
  spec={'target':'calc-inert','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
   'cached_target':{'id':'calc-inert'},'repair_on':[],'local_repair_on':[],'session_id':'inert'}
  caller={'reuse_revalidate':lambda _: {'status':'revalidated'},'final_revalidate':lambda _: {'status':'revalidated'},
   'verify_effect':outer,'journal':lambda _:None}
  with patch.object(composition,'run_compiled',side_effect=guarded):
   result=composition.run_compiled_interface_in_caller(spec,caller,lambda _:interface(),{})
  return bridge,calls,result
 def test_independent_saved_score_controls_outer_success(self):
  for expected,outcome in [((43,47),'TASK_SUCCEEDED'),((44,47),'TASK_NOT_VERIFIED')]:
   with self.subTest(expected=expected):
    bridge,calls,result=self.run_case(expected=expected)
    self.assertEqual(result['outcome'],outcome);self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],2)
    self.assertEqual((len(bridge.inputs),calls['proposal'],calls['verify']),(2,1,1))
 def test_unknown_first_effect_retains_prefix_and_skips_outer_score(self):
  bridge,calls,result=self.run_case(unknown=True)
  self.assertEqual(result['outcome'],'EXECUTION_INCOMPLETE');self.assertEqual(result['execution_progress']['reason'],'effect_unavailable')
  self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],1)
  self.assertEqual((len(bridge.inputs),calls['proposal'],calls['verify']),(1,0,0))