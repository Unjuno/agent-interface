import copy,time,unittest
from types import SimpleNamespace
from PIL import Image
from save_guard import SemanticSaveGuard
from runtime.backends.x11_v1.backend import X11BackendError

class SaveGuardTests(unittest.TestCase):
 def setUp(self):
  self.now=time.monotonic_ns();self.binding={'surface':20,'focus':21,'geometry':[0,0,1280,800]}
  self.image=Image.new('RGB',(1280,800),'white');self.image.putpixel((92,185),(0,0,0));self.image.putpixel((92,205),(0,0,0))
  self.b=SimpleNamespace(scope='calc',binding_revision=1,sequence=1,active=None,review_required=False,session=SimpleNamespace(recovery_required=False),history={},_binding=lambda:copy.deepcopy(self.binding),_focus_within_target=lambda:True)
  self.native=self.observation();self.b.history[1]=(copy.deepcopy(self.native),self.image.copy());self.emissions=[];self.captures=[]
  def check(stage):
   self.captures.append(stage);self.b.sequence+=1;native=self.observation();self.b.history[self.b.sequence]=(native,self.image.copy());return {'eligible':True,'point':[8,8]}
  self.b.check=check;self.b.backend=SimpleNamespace(key_state=lambda key,down:self.emissions.append((key,down)))
  self.guard=SemanticSaveGuard(self.b,alias='sheet',offset=[8,8],regions=[[88,182,125,200],[88,202,125,220]],deadline_ns=self.now+5_000_000_000,clock=lambda:self.now)
  self.record={'cue':'filled','sequence':1,'artifact_sha256':'png'}
 def observation(self):
  return {'sequence':self.b.sequence,'binding_revision':1,'capture_ns':self.now,'pointer_binding':copy.deepcopy(self.binding),'native':{'artifact':{'sha256':'png'}}}
 def arm(self):self.guard.arm(self.native,self.image.copy(),cue_record=self.record)
 def test_correct_pixels_preserve_original_guard_and_press(self):
  self.arm();self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():self.b.backend.key_state('CTRL',True);self.b.backend.key_state('S',True)
  self.assertEqual(self.captures,['before_save_key_press:CTRL','before_save_key_press:S']);self.assertEqual(self.emissions,[('CTRL',True),('S',True)])
 def test_cells_changed_after_ocr_blocks_first_press(self):
  self.arm();self.image.putpixel((92,205),(255,0,0));self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   with self.assertRaisesRegex(X11BackendError,'pixels changed'):self.b.backend.key_state('CTRL',True)
  self.assertEqual(self.emissions,[])
 def test_cells_changed_after_modifier_blocks_s_and_allows_release(self):
  self.arm();self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   self.b.backend.key_state('CTRL',True);self.image.putpixel((92,205),(255,0,0))
   with self.assertRaises(X11BackendError):self.b.backend.key_state('S',True)
   self.b.backend.key_state('CTRL',False)
  self.assertEqual(self.emissions,[('CTRL',True),('CTRL',False)])
 def test_unarmed_save_is_refused(self):
  self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   with self.assertRaisesRegex(X11BackendError,'unarmed'):self.b.backend.key_state('CTRL',True)
  self.assertEqual(self.emissions,[])
 def test_other_program_not_affected(self):
  self.b.active=('entry',[8,8])
  with self.guard.installed_guard():self.b.backend.key_state('7',True)
  self.assertEqual(self.captures,[]);self.assertEqual(self.emissions,[('7',True)])
 def test_original_alias_refusal_not_overridden(self):
  self.arm();self.b.active=('sheet',[8,8]);self.b.check=lambda s:(_ for _ in ()).throw(X11BackendError('alias refused'))
  with self.guard.installed_guard():
   with self.assertRaisesRegex(X11BackendError,'alias refused'):self.b.backend.key_state('CTRL',True)
  self.assertEqual(self.emissions,[])
 def test_scope_change_refused(self):
  self.arm();self.b.scope='different';self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   with self.assertRaises(X11BackendError):self.b.backend.key_state('CTRL',True)
  self.assertEqual(self.emissions,[])
 def test_expired_deadline_release_still_possible(self):
  self.arm();self.now+=5_000_000_000;self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   with self.assertRaises(X11BackendError):self.b.backend.key_state('CTRL',True)
   self.b.backend.key_state('CTRL',False)
  self.assertEqual(self.emissions,[('CTRL',False)])
 def test_hooks_restored_after_exception(self):
  old_check=self.b.check;old_key=self.b.backend.key_state
  with self.assertRaises(RuntimeError):
   with self.guard.installed_guard():raise RuntimeError('caller failure')
  self.assertIs(self.b.check,old_check);self.assertIs(self.b.backend.key_state,old_key);self.assertFalse(self.guard.installed)
 def test_no_dependency_renewal(self):
  self.arm()
  with self.assertRaisesRegex(ValueError,'renewed'):self.arm()
 def test_wrong_ocr_cannot_arm(self):
  self.record['cue']='wrong'
  with self.assertRaises(ValueError):self.arm()
 def test_modified_rgb_cannot_arm(self):
  self.image.putpixel((2,2),(0,0,0))
  with self.assertRaises(ValueError):self.arm()
 def test_replaced_source_cannot_arm(self):
  self.b.sequence=2
  with self.assertRaises(ValueError):self.arm()
 def test_only_frozen_save_program_installs_guard(self):
  self.arm();tail=[{'op':'key_chord','keys':['CTRL','s']}];calls=[]
  def keyboard(alias,offset,*,tail,expires_at_ns=None):
   calls.append(self.guard.installed);self.b.active=(alias,offset)
   try:self.b.backend.key_state('CTRL',True)
   finally:self.b.active=None
  self.b.keyboard=keyboard;old_keyboard=self.b.keyboard
  with self.guard.install_for_save(tail):
   self.b.keyboard('sheet',[8,8],tail=[{'op':'text','text':'731'}]);self.b.keyboard('sheet',[8,8],tail=tail)
  self.assertEqual(calls,[False,True]);self.assertIs(self.b.keyboard,old_keyboard)
 def native_check(self):
  from runtime.guarded_x11_v1.bridge import NativeHandleBridge
  from types import MethodType
  self.b.deadline=self.now+5_000_000_000;self.b.checks=[]
  self.b.store=SimpleNamespace(resolve_point=lambda *a,**kw:{'eligible':True,'status':'VALID','point':[8,8]})
  def observe():
   self.captures.append('native_observe');self.b.sequence+=1;native=self.observation();self.b.history[self.b.sequence]=(native,self.image.copy());return native
  self.b.observe=observe;self.b.check=MethodType(NativeHandleBridge.check,self.b)
 def test_existing_native_check_capture_is_used_for_cell_guard(self):
  self.arm();self.native_check();self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():self.b.backend.key_state('CTRL',True)
  self.assertEqual(self.captures,['native_observe']);self.assertEqual(len(self.b.checks),1)
  self.assertEqual(self.b.checks[0]['stage'],'before_save_key_press:CTRL');self.assertEqual(self.emissions,[('CTRL',True)])
 def test_existing_native_focus_check_blocks_changed_cells(self):
  self.arm();self.native_check();self.image.putpixel((92,205),(255,0,0));self.b.active=('sheet',[8,8])
  with self.guard.installed_guard():
   with self.assertRaisesRegex(X11BackendError,'pixels changed'):self.b.check('before_focus')
  self.assertEqual(self.captures,['native_observe']);self.assertEqual(self.emissions,[])
 def test_modified_save_cannot_bypass_guard(self):
  tail=[{'op':'key_chord','keys':['CTRL','s']}];calls=[]
  self.b.keyboard=lambda *a,**k:calls.append(k)
  with self.guard.install_for_save(tail):
   for alias,offset,ops in [('other',[8,8],tail),('sheet',[9,9],tail),('sheet',[8,8],tail+[{'op':'wait_update','timeout_ms':100}])]:
    with self.subTest(alias=alias,offset=offset,ops=ops):
     with self.assertRaisesRegex(ValueError,'frozen'):self.b.keyboard(alias,offset,tail=ops)
  self.assertEqual(calls,[])
if __name__=='__main__':unittest.main()
