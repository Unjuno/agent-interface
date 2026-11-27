import time, unittest
from types import SimpleNamespace
from PIL import Image
from runtime.guarded_x11_v1.handles import TargetHandleStore
from research.live_control.calc_fresh_reference_v1 import mint_from_proposal

class FixtureBridge:
 def __init__(self):
  self.scope='scope';self.sequence=2;self.binding_revision=0;self.review_required=False;self.session=SimpleNamespace(recovery_required=False);self.minted=[];self.store=TargetHandleStore('scope')
  self.image=Image.new('RGB',(100,100),'white')
  for i in range(20):self.image.putpixel((40+i,45+i%10),(i*10,30,200))
  self.observation={'sequence':2,'binding_revision':0,'capture_ns':time.monotonic_ns(),'pointer_binding':{'focus':123,'surface':123,'geometry':[0,0,100,100]},
   'native':{'artifact':{'sha256':'a'*64}}}
  self.history={2:(self.observation,self.image)}
 def mint_reference(self,alias,source_sequence,point,*,region_size):
  self.minted.append(alias);o,image=self.history[source_sequence];w,h=region_size
  self.store.mint(alias,'window_content',[point[0]-w//2,point[1]-h//2,w,h],o,image,time.monotonic_ns())
  return {'offset':[w//2,h//2],'lifetime':{'authority_granted':False}}

def proposal():return {'alias':'fresh_target','source_sequence':2,'source_sha256':'a'*64,'point':[50,50],'region_size':[24,14]}
class FreshReferenceTests(unittest.TestCase):
 def test_current_reviewed_proposal_mints_observational_reference(self):
  bridge=FixtureBridge();p=proposal();result=mint_from_proposal(bridge,p,scope='scope',after_ns=bridge.observation['capture_ns']-1)
  self.assertEqual(result['status'],'REFERENCE_MINTED');self.assertFalse(result['grants_input_authority'])
  o,image=bridge.history[2];self.assertTrue(bridge.store.resolve_point('fresh_target',result['offset'],o,image,time.monotonic_ns(),bridge.scope)['eligible'])
 def test_wrong_image_sequence_scope_or_boundary_never_mints(self):
  for change in ('digest','sequence','scope','boundary','point'):
   with self.subTest(change=change):
    bridge=FixtureBridge();p=proposal();scope='scope';boundary=bridge.observation['capture_ns']-1
    if change=='digest':p['source_sha256']='b'*64
    elif change=='sequence':p['source_sequence']=1
    elif change=='scope':scope='other'
    elif change=='boundary':boundary=bridge.observation['capture_ns']
    else:p['point']=[-1,50]
    result=mint_from_proposal(bridge,p,scope=scope,after_ns=boundary)
    self.assertEqual(result['status'],'UNAVAILABLE');self.assertEqual(bridge.minted,[])
 def test_association_change_during_mint_is_not_promoted_or_retried(self):
  bridge=FixtureBridge();original=bridge.mint_reference
  def raced(*args,**kwargs):
   value=original(*args,**kwargs);bridge.sequence+=1;return value
  bridge.mint_reference=raced
  result=mint_from_proposal(bridge,proposal(),scope='scope',after_ns=bridge.observation['capture_ns']-1)
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertTrue(result['alias_may_be_consumed'])
  self.assertEqual(bridge.minted,['fresh_target'])
 def test_old_or_future_capture_does_not_mint(self):
  for adjustment in (-2_000_000_000,2_000_000_000):
   with self.subTest(adjustment=adjustment):
    bridge=FixtureBridge();bridge.observation['capture_ns']+=adjustment
    result=mint_from_proposal(bridge,proposal(),scope='scope',after_ns=0)
    self.assertEqual(result['status'],'UNAVAILABLE');self.assertEqual(bridge.minted,[])
 def test_revision_change_during_mint_never_promotes_reference(self):
  bridge=FixtureBridge();original=bridge.mint_reference
  def raced(*args,**kwargs):
   result=original(*args,**kwargs);bridge.binding_revision+=1;return result
  bridge.mint_reference=raced
  result=mint_from_proposal(bridge,proposal(),scope='scope',after_ns=bridge.observation['capture_ns']-1)
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertTrue(result['alias_may_be_consumed'])
