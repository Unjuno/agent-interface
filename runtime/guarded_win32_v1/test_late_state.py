import pathlib,time,unittest,json,tempfile
from unittest.mock import Mock,patch
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.guarded_win32_v1.fresh import FreshWin32Reference
from runtime.guarded_win32_v1.bridge import MoveBridge

_fixture_output_dirs = []

def _cleanup_fixture_output_dirs():
 for output_dir in _fixture_output_dirs:
  output_dir.cleanup()
 _fixture_output_dirs.clear()

unittest.addModuleCleanup(_cleanup_fixture_output_dirs)

class Cases(unittest.TestCase):
 def fixture(self):
  b=object.__new__(Win32Backend);b.targets={'fixture':42};b.emissions=0;b.held_keys={};b.held_buttons=set();b.user32=Mock();b.user32.IsWindow.return_value=True;b.user32.GetForegroundWindow.return_value=42;b.process_identity=Mock(return_value={'pid':51,'creation_time_100ns':700});b.geometry=Mock(return_value={'x':0,'y':0,'width':8,'height':8})
  raw=bytes(v for y in range(8) for x in range(8) for v in (x*20,y*20,255,0));b._capture_hdc=Mock(return_value=raw);events=[]
  b.pointer_move=lambda t,f,x,y:events.append(['move',t,x,y])
  def release():events.append(['release']);return {'verified':True,'keys_down':[],'buttons_down':[]}
  b.release_all=release;image_dir=tempfile.TemporaryDirectory();_fixture_output_dirs.append(image_dir);o=FreshWin32Reference(b,'fixture',image_dir.name);o.observe([0,0,8,8]);o.mint('button',1,[2,2,4,4]);s=MoveBridge(o,lambda intent:{'lease_id':'inert-explicit-lease','expires_at_ns':time.monotonic_ns()+1000000000},lambda:False)
  return b,o,s,raw,events

 def test_target_process_generation_change_after_prepare_refuses_input(self):
  b,o,s,raw,e=self.fixture();b.process_identity=Mock(return_value={'pid':51,'creation_time_100ns':700})
  # Recreate the observation after installing the new process-identity adapter.
  o=FreshWin32Reference(b,'fixture',s.observer.out);o.observe([0,0,8,8]);o.mint('button',1,[2,2,4,4])
  s=MoveBridge(o,lambda intent:{'lease_id':'inert-explicit-lease','expires_at_ns':time.monotonic_ns()+1000000000},lambda:False)
  permit=s.prepare('button',[1,1])
  b.process_identity.return_value={'pid':52,'creation_time_100ns':900}
  result=s.execute(permit['authorization'])
  self.assertEqual(result['status'],'refused')
  self.assertEqual(e,[])
  self.assertTrue(o.review_required)

 def test_missing_target_process_generation_refuses_observation(self):
  b,o,s,raw,e=self.fixture();b.process_identity=Mock(side_effect=RuntimeError('process identity unavailable'))
  with self.assertRaisesRegex(RuntimeError,'process identity unavailable'):
   FreshWin32Reference(b,'fixture','images/'+self._testMethodName).observe([0,0,8,8])
  self.assertEqual(e,[])

 def test_prepare_observed_preserves_compiled_caller_sequence_without_recapture(self):
  b,o,s,raw,e=self.fixture();capture_count=b._capture_hdc.call_count
  permit=s.prepare_observed('button',[1,1],source_sequence=1)
  self.assertEqual(permit['sequence'],1)
  self.assertEqual(b._capture_hdc.call_count,capture_count)
  result=s.execute(permit['authorization'])
  self.assertEqual(result['status'],'completed')
  self.assertEqual(e,[['move','fixture',3,3],['release']])

 def test_prepare_observed_refuses_changed_generation_before_authorization(self):
  b,o,s,raw,e=self.fixture()
  b.process_identity.return_value={'pid':52,'creation_time_100ns':900}
  with self.assertRaisesRegex(ValueError,'association changed'):
   s.prepare_observed('button',[1,1],source_sequence=1)
  self.assertFalse(s.permits)
  self.assertEqual(e,[])
 def refused_once(self,s,p,events):
  r=s.execute(p['authorization']);self.assertEqual(r['status'],'refused');self.assertEqual(events,[]);self.assertEqual(s.execute(p['authorization'])['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN');return r
 def test_held_key_after_prepare_requires_recovery(self):
  b,o,s,raw,e=self.fixture();p=s.prepare('button',[1,1]);b.held_keys={'A':65};self.refused_once(s,p,e);self.assertTrue(s.session.recovery_required)
 def test_held_button_during_guard_capture_requires_recovery(self):
  b,o,s,raw,e=self.fixture();p=s.prepare('button',[1,1])
  def capture(*args,**kwargs):b.held_buttons.add('left');return raw
  b._capture_hdc.side_effect=capture;self.refused_once(s,p,e);self.assertTrue(s.session.recovery_required)
 def test_observation_changes_during_guard_capture(self):
  b,o,s,raw,e=self.fixture();p=s.prepare('button',[1,1])
  def capture(*args,**kwargs):o.sequence+=1;return raw
  b._capture_hdc.side_effect=capture;self.refused_once(s,p,e)
 def test_exact_expiry_consumes_without_capture(self):
  b,o,s,raw,e=self.fixture();p=s.prepare('button',[1,1]);count=b._capture_hdc.call_count
  with patch('runtime.guarded_win32_v1.bridge.time.monotonic_ns',return_value=p['valid_until_ns']):self.refused_once(s,p,e)
  self.assertEqual(b._capture_hdc.call_count,count)
 def test_expired_caller_lease_cannot_prepare(self):
  b,o,s,raw,e=self.fixture();s.authorize=lambda intent:{'lease_id':'expired-lease','expires_at_ns':time.monotonic_ns()-1}
  with self.assertRaisesRegex(ValueError,'authority expired'):s.prepare('button',[1,1])
  self.assertFalse(s.permits);self.assertEqual(e,[])
 def test_failed_new_preparation_invalidates_previous_permit(self):
  for mode in ['declined','expired']:
   b,o,s,raw,e=self.fixture();old=s.prepare('button',[1,1])
   if mode=='declined':s.authorize=lambda intent:None
   else:s.authorize=lambda intent:{'lease_id':'expired-lease','expires_at_ns':time.monotonic_ns()-1}
   expected='caller authority unavailable' if mode=='declined' else 'authority expired'
   with self.assertRaisesRegex(ValueError,expected):s.prepare('button',[1,1])
   self.assertFalse(s.permits)
   self.assertEqual(s.execute(old['authorization'])['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN')
   self.assertEqual(e,[])

if __name__=='__main__':unittest.main()
