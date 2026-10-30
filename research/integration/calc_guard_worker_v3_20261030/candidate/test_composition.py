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
 def case(self,route,second='864',unknown=False,mutate_after_ctrl=False):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
  b=Bridge();b.scope='calc-scope';b.binding_revision=1;b.phase=0;b.checks=[];b.deadline=None
  binding={'focus':21,'surface':20,'geometry':[0,0,1280,800]}
  b._binding=lambda:copy.deepcopy(binding);b._window_title=lambda:'book.xlsx - LibreOffice Calc'
  b._focus_within_target=lambda:True;self.key_events=[]
  b.backend.key_state=lambda key,down:self.key_events.append((key,down))
  target={'path':root/'initial'};target['path'].mkdir()
  def configure(path,**kwargs):target['path']=Path(path);target['path'].mkdir(parents=True,exist_ok=True)
  b.backend.configure_capture_artifacts=configure
  def observe():
   b.sequence+=1;now=time.monotonic_ns();rgb=Image.new('RGB',(1280,800),'white')
   if b.phase:rgb.putpixel((92,185),(0,0,0));rgb.putpixel((92,205),(0,0,0))
   if getattr(b,'changed',False):rgb.putpixel((92,205),(255,0,0))
   buf=io.BytesIO();rgb.save(buf,format='PNG');data=buf.getvalue();path=target['path']/f'{b.sequence}.png';path.write_bytes(data)
   native={'sequence':b.sequence,'observation_id':str(b.sequence),'binding_revision':1,'capture_ns':now,'pointer_binding':copy.deepcopy(binding),
    'native':{'sha256':'fixture-raw-association','width':1280,'height':800,'frame':'screen_physical_px','region':[0,0,1280,800],'native_window_id':20,'capture_ended_ns':time.monotonic_ns(),
      'artifact':{'path':str(path),'mime_type':'image/png','sha256':hashlib.sha256(data).hexdigest(),'source_raw_sha256':'fixture-raw-association','bytes':len(data),'width':1280,'height':800}}}
   b.history[b.sequence]=(copy.deepcopy(native),rgb);return native
  b.observe=observe;b.check=MethodType(NativeHandleBridge.check,b)
  b.input_guard=MethodType(NativeHandleBridge.input_guard,b)
  b._check_additional_input=MethodType(NativeHandleBridge._check_additional_input,b)
  b._isolated_observation_active=lambda:False
  b._input_guard=None;b.additional_checks=[]
  inputs=[];keys=[]
  def result():return {'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
  def enter(alias,offset,**kw):inputs.append(('enter',kw));b.phase=1;return result()
  def save(alias,offset,**kw):
   inputs.append(('save',kw));b.active=(alias,offset);b.deadline=kw['expires_at_ns'];b.checks=[]
   try:
    b.check('before_admission');b.check('before_focus')
    for key in ['CTRL','s']:
     b.check('before_key_press:'+key);b.backend.key_state(key,True);keys.append(key)
     if key=='CTRL' and mutate_after_ctrl:b.changed=True
    return result()
   except Exception as error:
    return {'status':'failed','error':repr(error),'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
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
    self.assertTrue(owner.dispatch_attempted);self.assertEqual(len([e for e in b.additional_checks if e['eligible']]),4)
 def test_compiled_changed_cells_after_ctrl_stop_save_suffix(self):
  owner,b,c,inputs,keys,result=self.case('compiled',mutate_after_ctrl=True)
  self.assertEqual([a for a,k in inputs],['enter','save'])
  self.assertEqual(keys,['CTRL'])
  self.assertNotEqual(result['method_receipt']['outcome'],'TASK_SUCCEEDED')
  self.assertEqual(result['method_receipt']['completed_transitions'],1)
  self.assertTrue(any(not row['eligible'] for row in b.additional_checks))

 def test_ordinary_changed_cells_after_ctrl_refuses_and_attempts_release(self):
  owner,b,c,inputs,keys,result=self.case('ordinary',mutate_after_ctrl=True)
  self.assertEqual(result['method_receipt']['reason'],'execution_failed')
  self.assertEqual(result['method_receipt']['completed_transitions'],1)
  self.assertIsNone(result['task_success'])
  self.assertFalse(result['replay_allowed'])
  self.assertIn(('CTRL',True),self.key_events)
  self.assertNotIn(('s',True),self.key_events)
  self.assertIn(('CTRL',False),self.key_events)

 def test_guard_rejects_image_not_equal_to_current_native_history(self):
  owner,b,c,inputs,keys,result=self.case('compiled')
  native,rgb=b.history[b.sequence]
  forged=rgb.copy();forged.putpixel((50,50),(255,0,0))
  decision=c.guard_perceive(copy.deepcopy(native),forged)
  self.assertIsNot(decision['context_ok'],True)
  self.assertIsNot(decision['cells_filled'],True)

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
