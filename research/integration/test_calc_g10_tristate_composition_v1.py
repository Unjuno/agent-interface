"""G10's retained tri-state rule through the current fake-bridge composition."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
from research.live_control.calc_g10_fresh_admission_v1 import run_with_bounded_fresh_proposal
from research.integration.test_calc_g10_fresh_admission_v1 import MintingBridge,interface,bindings,verify

ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'
source=ROOT/'effect_predicate.py'
if hashlib.sha256(source.read_bytes()).hexdigest()!='44473bbb30194486ccdceb998a6714f28c59db0fac4ed51cee88202275d54eba':
 raise ValueError('retained G10 predicate source differs')
spec=importlib.util.spec_from_file_location('retained_g10_effect_predicate',source)
predicate=importlib.util.module_from_spec(spec);spec.loader.exec_module(predicate)
class G10TriStateCompositionTests(unittest.TestCase):
 def run_case(self,first_decoded):
  data=(ROOT/'runs'/'compiled_ocrlive10'/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(data).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  checks=json.loads(data)['pixel_checks'];bridge=MintingBridge();requested=[];cancel=lambda:False
  def perceive(_,image):
   phase=image.getpixel((0,0))[0]
   row=checks[phase]
   decoded=first_decoded if phase==1 else row['decoded_values']
   return {'ready':True,'row_visible':predicate.visible_row_predicate(decoded,row['expected_values'])}
  def proposal(native,image):
   requested.append(native['sequence'])
   return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  worker=BoundedProposal(proposal,timeout_ms=300,cancelled=cancel)
  result=run_with_bounded_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_worker=worker,cancelled=cancel)
  return bridge,requested,result
 def test_recorded_decodes_allow_two_inert_transitions(self):
  bridge,requested,result=self.run_case(['29','31','899'])
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED');self.assertEqual(len(bridge.inputs),2);self.assertEqual(len(requested),1)
 def test_unavailable_or_mismatched_first_decode_stops_before_second(self):
  for decoded,reason in [(None,'effect_unavailable'),(['29','31','898'],'effect_failed')]:
   with self.subTest(decoded=decoded):
    bridge,requested,result=self.run_case(decoded)
    self.assertEqual(result['reason'],reason);self.assertEqual(result['completed_transitions'],1)
    self.assertEqual(len(bridge.inputs),1);self.assertEqual(requested,[]);self.assertEqual(bridge.mints,[])