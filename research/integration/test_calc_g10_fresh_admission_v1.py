import hashlib,json,time,unittest
from pathlib import Path
from runtime.guarded_x11_v1.test_compiled import Bridge
from research.live_control.calc_g10_fresh_admission_v1 import run_with_fresh_proposal
ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'/'runs'/'compiled_ocrlive10'
class MintingBridge(Bridge):
 def __init__(self):super().__init__();self.aliases={'a1_primary'};self.mints=[]
 def observe(self):
  if self.phase>=1:time.sleep(.02)
  return super().observe()
 def mint_reference(self,alias,sequence,point,*,region_size):
  self.mints.append((alias,sequence));self.aliases.add(alias)
  return {'offset':[region_size[0]//2,region_size[1]//2],'lifetime':{'authority_granted':False}}
 def resolve(self,alias,*args,**kwargs):
  if alias not in self.aliases:return {'eligible':False,'status':'MISSING','valid_until_ns':0}
  if alias=='a1_primary' and self.phase>=1:return {'eligible':False,'status':'STALE','valid_until_ns':0}
  return super().resolve(alias,*args,**kwargs)

def interface():
 data=(ROOT/'raw.json').read_bytes()
 if hashlib.sha256(data).hexdigest()!='890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf':raise ValueError('retained G10 bytes differ')
 graph=json.loads(data)['interface'];graph['session_scope']='private';graph['surface']='x11-window-20'
 second=dict(graph['symbols']['anchor']);second['target_reference']='a1_second'
 graph['symbols']['second_anchor']=second;graph['actions']['second']['target_symbol']='second_anchor'
 return graph

def perceive(_,image):return {'ready':True,'row_visible':'unknown' if image.getpixel((0,0))[0]==0 else True}
def verify(p,n,i):return {'status':'succeeded','evidence_ref':p['observation']['evidence_ref']}
def bindings():return {name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('first','second')}
class G10FreshAdmissionTests(unittest.TestCase):
 def test_fresh_proposal_is_minted_then_guarded_for_second_action(self):
  bridge=MintingBridge();seen=[]
  def provider(native,image):
   seen.append(native['sequence']);return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  result=run_with_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_provider=provider)
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED');self.assertEqual(result['completed_transitions'],2)
  self.assertEqual([x[0] for x in bridge.inputs],['a1_primary','a1_second']);self.assertEqual(len(seen),1);self.assertEqual(len(bridge.mints),1)
 def test_wrong_digest_refuses_second_action_without_retry(self):
  bridge=MintingBridge();seen=[]
  def provider(native,image):
   seen.append(1);return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':'0'*64,'point':[8,8],'region_size':[4,4]}
  result=run_with_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_provider=provider)
  self.assertEqual(result['outcome'],'SAFE_YIELD');self.assertEqual(result['completed_transitions'],1)
  self.assertEqual(len(bridge.inputs),1);self.assertEqual(bridge.mints,[]);self.assertEqual(len(seen),1)
 def test_changed_binding_during_proposal_prevents_mint_and_input(self):
  bridge=MintingBridge()
  def provider(native,image):
   bridge.binding_revision+=1
   return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  result=run_with_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_provider=provider)
  self.assertEqual(result['outcome'],'SAFE_YIELD');self.assertEqual(result['completed_transitions'],1)
  self.assertEqual(len(bridge.inputs),1);self.assertEqual(bridge.mints,[])
 def test_cancel_during_proposal_prevents_mint_and_input(self):
  bridge=MintingBridge();state={'cancelled':False}
  def provider(native,image):
   state['cancelled']=True
   return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  result=run_with_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,
     proposal_provider=provider,cancelled=lambda:state['cancelled'])
  self.assertEqual(result['outcome'],'SAFE_YIELD');self.assertEqual(result['completed_transitions'],1)
  self.assertEqual(len(bridge.inputs),1);self.assertEqual(bridge.mints,[])
 def test_original_single_alias_is_rejected_before_any_input(self):
  bridge=MintingBridge();graph=interface();graph['actions']['second']['target_symbol']='anchor'
  with self.assertRaises(ValueError):
   run_with_fresh_proposal(bridge,graph,bindings(),perceive=perceive,verify_effect=verify,proposal_provider=lambda *_:None)
  self.assertEqual(bridge.inputs,[]);self.assertEqual(bridge.mints,[])
 def test_bounded_proposal_timeout_stops_before_second_input(self):
  import threading
  from research.live_control.calc_bounded_proposal_v1 import BoundedProposal
  bridge=MintingBridge();entered=threading.Event();release=threading.Event()
  def slow(native,image):
   entered.set();release.wait(2)
   return {'alias':'a1_second','source_sequence':native['sequence'],
    'source_sha256':native['native']['artifact']['sha256'],'point':[8,8],'region_size':[4,4]}
  provider=BoundedProposal(slow,timeout_ms=30,cancelled=lambda:False)
  try:
   result=run_with_fresh_proposal(bridge,interface(),bindings(),perceive=perceive,verify_effect=verify,proposal_provider=provider)
   self.assertTrue(entered.is_set());self.assertEqual(result['outcome'],'SAFE_YIELD')
   self.assertEqual(result['completed_transitions'],1);self.assertEqual(len(bridge.inputs),1)
   self.assertEqual(bridge.mints,[]);self.assertTrue(provider.snapshot()['retired'])
  finally:
   release.set()
   if provider.thread is not None:provider.thread.join(1)