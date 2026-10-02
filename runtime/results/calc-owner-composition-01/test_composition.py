import copy,hashlib,io,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace,MethodType
from unittest.mock import patch
from PIL import Image
from composition import CalcComposition
from runtime.guarded_x11_v1.test_compiled import Bridge
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner

TSV=b'level\tleft\ttop\twidth\theight\tconf\ttext\n5\t92\t185\t20\t10\t95\t731\n5\t92\t205\t20\t10\t95\t864\n'
class CompositionTests(unittest.TestCase):
 def case(self,route,second='864',unknown=False):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
  b=Bridge();b.scope='calc-scope';b.binding_revision=1;b.phase=0;b.checks=[];b.deadline=None
  binding={'focus':21,'surface':20,'geometry':[0,0,1280,800]}
  b._binding=lambda:copy.deepcopy(binding);b._window_title=lambda:'book.xlsx - LibreOffice Calc'
  b._focus_within_target=lambda:True;b.backend.key_state=lambda key,down:None
  target={'path':root/'initial'};target['path'].mkdir()
  def configure(path,**kwargs):target['path']=Path(path);target['path'].mkdir(parents=True,exist_ok=True)
  b.backend.configure_capture_artifacts=configure
  def observe():
   b.sequence+=1;now=time.monotonic_ns();rgb=Image.new('RGB',(1280,800),'white')
   if b.phase:rgb.putpixel((92,185),(0,0,0));rgb.putpixel((92,205),(0,0,0))
   buf=io.BytesIO();rgb.save(buf,format='PNG');data=buf.getvalue();path=target['path']/f'{b.sequence}.png';path.write_bytes(data)
   native={'sequence':b.sequence,'observation_id':str(b.sequence),'binding_revision':1,'capture_ns':now,'pointer_binding':copy.deepcopy(binding),
    'native':{'sha256':'fixture-raw-association','width':1280,'height':800,'frame':'screen_physical_px','region':[0,0,1280,800],'native_window_id':20,'capture_ended_ns':time.monotonic_ns(),
      'artifact':{'path':str(path),'mime_type':'image/png','sha256':hashlib.sha256(data).hexdigest(),'source_raw_sha256':'fixture-raw-association','bytes':len(data),'width':1280,'height':800}}}
   b.history[b.sequence]=(copy.deepcopy(native),rgb);return native
  b.observe=observe;b.check=MethodType(NativeHandleBridge.check,b)
  inputs=[];keys=[]
  def result():return {'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
  def enter(alias,offset,**kw):inputs.append(('enter',kw));b.phase=1;return result()
  def save(alias,offset,**kw):
   inputs.append(('save',kw));b.active=(alias,offset);b.deadline=kw['expires_at_ns'];b.checks=[]
   try:
    b.check('before_admission');b.check('before_focus')
    for key in ['CTRL','s']:b.backend.key_state(key,True);keys.append(key)
    return result()
   finally:
    b.backend.key_state('s',False);b.backend.key_state('CTRL',False);b.active=None;b.deadline=None
  b.click=enter;b.keyboard=save
  reviewed=b.observe();rgb=b.history[b.sequence][1]
  owner=GuardedSessionOwner({'app':20},root/'owner');owner.bridge=b;owner.session=b.session;owner.state='open'
  refs={'entry_alias':'entry','entry_offset':[8,8],'save_alias':'sheet','save_offset':[8,8],
        'cell_regions':[[20,180,125,200],[20,200,125,220]],'context_region':[0,0,10,10]}
  approved={'geometry_reviewed':True,'image_size':[1280,800],'scope':b.scope,'revision':1,'binding':binding,'titles':[b._window_title()]}
  def runner(*a,**kw):
   data=TSV if b.phase else b''
   if unknown and b.phase:data=b''
   if second!='864':data=data.replace(b'864',second.encode())
   return SimpleNamespace(returncode=0,stdout=data,stderr=b'')
  composition=CalcComposition(owner,root/'method',refs=refs,approved=approved,reviewed_native=reviewed,reviewed_rgb=rgb,second_value=second,ocr_runner=runner)
  old=b.keyboard
  # Actual public owner method and real graph; presentation alone is stubbed.
  with patch('runtime.cli_v1.review.present_result',return_value={'image_status':'image','image':None,'fixture_only':True}):result=composition.run(route)
  self.assertIs(b.keyboard,old);self.assertFalse(composition.guard.installed)
  return owner,b,composition,inputs,keys,result
 def test_both_routes_request_save_without_claiming_persistence(self):
  for route in ['compiled','ordinary']:
   with self.subTest(route=route):
    owner,b,c,inputs,keys,result=self.case(route)
    self.assertEqual([a for a,k in inputs],['enter','save']);self.assertEqual(keys,['CTRL','s'])
    self.assertEqual(result['method_receipt']['outcome'],'SAFE_YIELD');self.assertEqual(result['method_receipt']['reason'],'no_progress');self.assertIsNone(result['task_success'])
    self.assertTrue(owner.dispatch_attempted);self.assertEqual(len([e for e in c.guard.events if e['event']=='dependency_checked']),4)
 def test_both_routes_wrong_digits_stop_before_save(self):
  for route in ['compiled','ordinary']:
   with self.subTest(route=route):
    owner,b,c,inputs,keys,result=self.case(route,second='863')
    self.assertEqual([a for a,k in inputs],['enter']);self.assertEqual(keys,[]);self.assertEqual(result['method_receipt']['completed_transitions'],1);self.assertIsNone(result['task_success'])
 def test_both_routes_unknown_digits_stop_before_save(self):
  for route in ['compiled','ordinary']:
   with self.subTest(route=route):
    owner,b,c,inputs,keys,result=self.case(route,unknown=True)
    self.assertEqual([a for a,k in inputs],['enter']);self.assertEqual(keys,[]);self.assertEqual(result['method_receipt']['completed_transitions'],1)
if __name__=='__main__':unittest.main()
