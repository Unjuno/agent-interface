import threading, unittest
from research.live_control.calc_g10_fresh_admission_v1 import run_with_bounded_fresh_proposal
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
from research.integration.test_calc_g10_fresh_admission_v1 import MintingBridge,interface,bindings,perceive,verify

class BoundedEntryTests(unittest.TestCase):
 def test_unbounded_or_mismatched_cancellation_rejected_before_input(self):
  for wrong in ('bare','different_cancel','reused'):
   with self.subTest(wrong=wrong):
    bridge=MintingBridge();cancel=lambda:False
    provider=BoundedProposal(lambda *_:None,timeout_ms=30,cancelled=cancel)
    if wrong=='bare':provider=lambda *_:None
    elif wrong=='different_cancel':provider=BoundedProposal(lambda *_:None,timeout_ms=30,cancelled=lambda:False)
    elif wrong=='reused':provider({},__import__('PIL.Image',fromlist=['Image']).new('RGB',(4,4)))
    with self.assertRaises(ValueError):run_with_bounded_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_worker=provider,cancelled=cancel)
    self.assertEqual(bridge.inputs,[]);self.assertEqual(bridge.mints,[])
 def test_timeout_stops_after_first_action_without_retry(self):
  bridge=MintingBridge();release=threading.Event();entered=threading.Event();cancel=lambda:False
  def slow(native,image):entered.set();release.wait(2);return None
  provider=BoundedProposal(slow,timeout_ms=30,cancelled=cancel)
  try:
   result=run_with_bounded_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_worker=provider,cancelled=cancel)
   self.assertTrue(entered.is_set());self.assertEqual(result['completed_transitions'],1)
   self.assertEqual(len(bridge.inputs),1);self.assertEqual(bridge.mints,[]);self.assertTrue(provider.snapshot()['retired'])
  finally:
   release.set()
   if provider.thread is not None:provider.thread.join(1)
 def test_completed_proposal_reaches_second_guarded_action(self):
  bridge=MintingBridge();cancel=lambda:False
  def proposal(native,image):return {'alias':'a1_second','source_sequence':native['sequence'],
   'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  provider=BoundedProposal(proposal,timeout_ms=300,cancelled=cancel)
  result=run_with_bounded_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_worker=provider,cancelled=cancel)
  self.assertEqual(result['completed_transitions'],2);self.assertEqual(len(bridge.inputs),2)
  self.assertTrue(provider.snapshot()['retired'])