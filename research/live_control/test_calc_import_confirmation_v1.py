from contextlib import contextmanager
from types import SimpleNamespace
import copy,unittest
from PIL import Image
from research.live_control.reviewed_preview_gate_v1 import ReviewedPreviewGate
from research.live_control.test_reviewed_modal_guard_v1 import Bridge
from research.live_control.calc_import_confirmation_v1 import ImportConfirmation

def tsv(s):return ('level\tconf\ttext\n5\t95\t'+s+'\n').encode()
class ModalBridge(Bridge):
 def __init__(self,img):
  super().__init__();self.active=None;self.img=img;self.mints=[];self.clicks=[];self.change=False;self.error=False
 def mint_reference(self,alias,seq,point,region_size):
  self.mints.append((alias,seq,point,region_size));return {'offset':[2,2]}
 @contextmanager
 def input_guard(self,alias,offset,*,tail,verify,interaction):
  self.check=verify
  try:yield
  finally:self.check=None
 def click(self,alias,offset,*,tail,expires_at_ns):
  if self.error:raise OSError('delivery unknown')
  image=self.img.copy()
  if self.change:image.putpixel((3,3),(0,0,0))
  n=self.capture(image)
  if not self.check('before_press',n,image):return {'status':'refused','input_dispatched':False,'recovery_required':False}
  self.clicks.append(alias);return {'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
class ImportConfirmationTests(unittest.TestCase):
 def setUp(self):
  self.img=Image.new('RGB',(16,16),'white');self.b=ModalBridge(self.img);self.owner=SimpleNamespace(bridge=self.b,state='open',session_id='new',dispatch_attempted=False);self.count=0
  def runner(cmd,**kw):
   self.count+=1;return SimpleNamespace(returncode=0,stdout=tsv(('641','283')[(self.count-1)%2]),stderr=b'')
  self.runner=runner;self.prior={'format':'compiled-gui-runtime-receipt-v1','session_scope':'prior','outcome':'SAFE_YIELD','reason':'effect_unavailable','completed_transitions':1,'pending_effect':{'action':'enter','expected_effect':{'cells_match':True},'effect_ref':'e1'},'transitions':[{'action':'enter','effect_ref':'e1','release_verified':True}]};self.close={'status':'closed','session_id':'old','authority_granted':False,'restart_allowed':False,'release_attempted':True,'release':{'verified':True,'keys_down':[],'buttons_down':[]}}
 def candidate(self,expected=('641','283')):
  gate=ReviewedPreviewGate(self.b,reference=self.img,static_regions=((0,0,1,1),),preview_regions=((2,2,8,8),(10,10,14,14)),title='Text Import',expected=expected,deadline_ns=2000,max_age_ns=100,clock=lambda:1010,runner=self.runner)
  n=self.b.capture(self.img);return ImportConfirmation(self.owner,gate,prior_receipt=self.prior,prior_close=self.close,prior_scope='prior',prior_session_id='old',alias='import_ok',point=[5,5],region_size=(4,4)),n
 def test_match_confirms_once_and_keeps_effect_unverified(self):
  attempt,n=self.candidate();r=attempt.run(n,self.img);self.assertEqual(r['status'],'input_completed');self.assertEqual(self.b.clicks,['import_ok']);self.assertTrue(self.owner.dispatch_attempted);self.assertEqual(r['import_effect'],'unverified');self.assertFalse(r['entry_replayed'])
  with self.assertRaises(ValueError):attempt.run(n,self.img)
 def test_wrong_preview_does_not_mint_or_click(self):
  attempt,n=self.candidate(expected=('642','283'));r=attempt.run(n,self.img);self.assertEqual(r['status'],'rejected');self.assertEqual(self.b.mints,[]);self.assertEqual(self.b.clicks,[]);self.assertFalse(self.owner.dispatch_attempted)
 def test_changed_preview_after_mint_is_refused_before_click(self):
  attempt,n=self.candidate();self.b.change=True;r=attempt.run(n,self.img);self.assertEqual(r['status'],'refused');self.assertEqual(self.b.clicks,[]);self.assertFalse(r['entry_replayed'])
 def test_delivery_exception_is_uncertain_and_not_retried(self):
  attempt,n=self.candidate();self.b.error=True;r=attempt.run(n,self.img);self.assertEqual(r['status'],'uncertain');self.assertTrue(self.owner.dispatch_attempted)
  with self.assertRaises(ValueError):attempt.run(n,self.img)
 def test_prior_release_or_effect_mismatch_blocks_before_gate(self):
  for mode in ('release','effect','scope','session'):
   with self.subTest(mode=mode):
    self.setUp()
    if mode=='release':self.close['release']['verified']=False
    if mode=='effect':self.prior['pending_effect']['effect_ref']='other'
    if mode=='scope':self.prior['session_scope']='other'
    if mode=='session':self.close['session_id']='other'
    with self.assertRaises(ValueError):self.candidate()
    self.assertEqual(self.count,0);self.assertEqual(self.b.mints,[])
 def test_owner_bridge_changed_before_run_never_mints(self):
  attempt,n=self.candidate();self.owner.bridge=ModalBridge(self.img);r=attempt.run(n,self.img);self.assertEqual(r['status'],'unavailable');self.assertEqual(self.b.mints,[])
 def test_owner_changed_during_mint_never_clicks(self):
  attempt,n=self.candidate();mint=self.b.mint_reference
  def change(*args,**kwargs):
   ref=mint(*args,**kwargs);self.owner.session_id='changed';return ref
  self.b.mint_reference=change;r=attempt.run(n,self.img);self.assertEqual(r['status'],'unavailable');self.assertTrue(r['mint_may_be_consumed']);self.assertEqual(self.b.clicks,[])
 def test_completed_with_recovery_required_is_uncertain(self):
  attempt,n=self.candidate();click=self.b.click
  def recover(*args,**kwargs):
   result=click(*args,**kwargs);result['recovery_required']=True;return result
  self.b.click=recover;r=attempt.run(n,self.img);self.assertEqual(r['status'],'uncertain')
 def test_refusal_with_pending_recovery_is_uncertain(self):
  attempt,n=self.candidate()
  self.b.click=lambda *args,**kwargs: {'status':'refused','input_dispatched':False,'recovery_required':True}
  result=attempt.run(n,self.img);self.assertEqual(result['status'],'uncertain');self.assertTrue(self.owner.dispatch_attempted)
 def test_refusal_without_recovery_evidence_is_uncertain(self):
  attempt,n=self.candidate()
  self.b.click=lambda *args,**kwargs: {'status':'refused','input_dispatched':False}
  result=attempt.run(n,self.img);self.assertEqual(result['status'],'uncertain')
 def test_refusal_with_session_recovery_is_uncertain(self):
  attempt,n=self.candidate()
  def refused(*args,**kwargs):
   self.b.session.recovery_required=True
   return {'status':'refused','input_dispatched':False,'recovery_required':False}
  self.b.click=refused;result=attempt.run(n,self.img);self.assertEqual(result['status'],'uncertain')
 def test_completed_with_session_recovery_is_uncertain(self):
  attempt,n=self.candidate();click=self.b.click
  def completed(*args,**kwargs):
   result=click(*args,**kwargs);self.b.session.recovery_required=True;return result
  self.b.click=completed;result=attempt.run(n,self.img);self.assertEqual(result['status'],'uncertain')
 def test_outside_modal_target_blocks_before_gate(self):
  gate=ReviewedPreviewGate(self.b,reference=self.img,static_regions=((0,0,1,1),),preview_regions=((2,2,8,8),(10,10,14,14)),title='Text Import',expected=('641','283'),deadline_ns=2000,max_age_ns=100,clock=lambda:1010,runner=self.runner)
  a=ImportConfirmation(self.owner,gate,prior_receipt=self.prior,prior_close=self.close,prior_scope='prior',prior_session_id='old',alias='import_ok',point=[99,99],region_size=(4,4));n=self.b.capture(self.img);r=a.run(n,self.img);self.assertEqual(r['status'],'rejected');self.assertEqual(self.count,0);self.assertEqual(self.b.mints,[])
if __name__=='__main__':unittest.main()
