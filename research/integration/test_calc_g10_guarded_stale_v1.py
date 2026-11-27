"""G10 graph against current guarded adapter with a fake stale-reference bridge."""
import hashlib,json,unittest
from pathlib import Path
from runtime.guarded_x11_v1.compiled import run
from runtime.guarded_x11_v1.test_compiled import Bridge

ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'/'runs'/'compiled_ocrlive10'
class ExpiringReferenceBridge(Bridge):
 def resolve(self,*args,**kwargs):
  if self.phase >= 1:return {'eligible':False,'status':'STALE','valid_until_ns':0}
  return super().resolve(*args,**kwargs)

class G10GuardedTests(unittest.TestCase):
 def test_original_single_alias_stops_when_selection_invalidates_it(self):
  raw_bytes=(ROOT/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  interface=json.loads(raw_bytes)['interface'];interface['session_scope']='private';interface['surface']='x11-window-20'
  self.assertEqual(interface['actions']['first']['target_symbol'],'anchor')
  self.assertEqual(interface['actions']['second']['target_symbol'],'anchor')
  self.assertEqual(interface['symbols']['anchor']['target_reference'],'a1_primary')
  bridge=ExpiringReferenceBridge()
  bindings={name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('first','second')}
  def perceive(_,image):return {'ready':True,'row_visible':'unknown' if image.getpixel((0,0))[0]==0 else True}
  def verify(p,n,i):return {'status':'succeeded','evidence_ref':p['observation']['evidence_ref']}
  result=run(bridge,interface,bindings,perceive=perceive,verify_effect=verify)
  self.assertEqual(result['outcome'],'SAFE_YIELD');self.assertEqual(result['reason'],'stale_symbol')
  self.assertEqual(result['completed_transitions'],1);self.assertEqual(len(bridge.inputs),1)
 def test_two_explicit_fresh_aliases_allow_inert_two_transition_graph(self):
  class DistinctBridge(Bridge):
   def resolve(self,alias,*args,**kwargs):
    expected='a1_primary' if self.phase==0 else 'a1_second'
    if alias!=expected:return {'eligible':False,'status':'STALE','valid_until_ns':0}
    return super().resolve(alias,*args,**kwargs)
  raw_bytes=(ROOT/'raw.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  interface=json.loads(raw_bytes)['interface'];interface['session_scope']='private';interface['surface']='x11-window-20'
  second=dict(interface['symbols']['anchor']);second['target_reference']='a1_second'
  interface['symbols']['second_anchor']=second;interface['actions']['second']['target_symbol']='second_anchor'
  bridge=DistinctBridge();bindings={name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('first','second')}
  def perceive(_,image):return {'ready':True,'row_visible':'unknown' if image.getpixel((0,0))[0]==0 else True}
  def verify(p,n,i):return {'status':'succeeded','evidence_ref':p['observation']['evidence_ref']}
  result=run(bridge,interface,bindings,perceive=perceive,verify_effect=verify)
  self.assertEqual(result['outcome'],'TASK_SUCCEEDED');self.assertEqual(result['completed_transitions'],2)
  self.assertEqual([i[0] for i in bridge.inputs],['a1_primary','a1_second'])