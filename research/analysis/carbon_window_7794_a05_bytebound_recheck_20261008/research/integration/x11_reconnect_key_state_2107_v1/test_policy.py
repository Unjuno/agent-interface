import json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).with_name('policy.py')
def call(p):
 r=subprocess.run([sys.executable,'-B',str(P)],input=json.dumps(p),text=True,capture_output=True); return r.returncode, json.loads(r.stdout) if r.stdout.strip() else None
class T(unittest.TestCase):
 def base(self,pol='CARRY_OLD_STATE'):
  return {'policy':pol,'keycode':50,'current_epoch':'e2','old_shift_down':False,'bootstrap':{'epoch':'e2','shift_down':False},'events':[]}
 def test_carry_up(self): self.assertEqual(call(self.base())[1]['decision'],'CONTINUE')
 def test_carry_press(self):
  p=self.base();p['events']=[{'seq':1,'epoch':'e2','kind':'KeyPress','detail':50}];self.assertEqual(call(p)[1]['decision'],'WAIT')
 def test_carry_release(self):
  p=self.base();p['old_shift_down']=True;p['events']=[{'seq':1,'epoch':'e2','kind':'KeyRelease','detail':50}];self.assertEqual(call(p)[1]['decision'],'CONTINUE')
 def test_reboot_down(self):
  p=self.base('REBOOTSTRAP_ON_RECONNECT');p['bootstrap']['shift_down']=True;self.assertEqual(call(p)[1]['decision'],'WAIT')
 def test_no_boot(self):
  p=self.base('REBOOTSTRAP_ON_RECONNECT');p['bootstrap']=None;self.assertEqual(call(p)[1]['decision'],'UNKNOWN')
 def test_wrong_epoch(self):
  p=self.base('REBOOTSTRAP_ON_RECONNECT');p['bootstrap']['epoch']='old';self.assertEqual(call(p)[1]['decision'],'UNKNOWN')
 def test_after_release(self):
  p=self.base('REBOOTSTRAP_ON_RECONNECT');p['bootstrap']['shift_down']=True;p['events']=[{'seq':1,'epoch':'e2','kind':'KeyRelease','detail':50}];self.assertEqual(call(p)[1]['decision'],'CONTINUE')
 def test_foreign_event_reject(self):
  p=self.base();p['events']=[{'seq':1,'epoch':'x','kind':'KeyPress','detail':50}];self.assertNotEqual(call(p)[0],0)
 def test_duplicate_seq_reject(self):
  p=self.base();p['events']=[{'seq':1,'epoch':'e2','kind':'KeyPress','detail':50},{'seq':1,'epoch':'e2','kind':'KeyRelease','detail':50}];self.assertNotEqual(call(p)[0],0)
 def test_bool_keycode_reject(self):
  p=self.base();p['keycode']=True;self.assertNotEqual(call(p)[0],0)
if __name__=='__main__':unittest.main()
