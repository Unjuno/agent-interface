import os,subprocess,unittest,json,time
from Xlib import display
keeper=display.Display()
subprocess.run(['setxkbmap','-layout','jp'],check=True)
from runtime.backends.x11_v1.test_integration import X11IntegrationTests,make_program
class ChangedLayout(X11IntegrationTests):
 @classmethod
 def setUpClass(cls):
  super().setUpClass()
  print('before',cls.backend._text_plan(':'),flush=True)
  subprocess.run(['setxkbmap','-layout','us'],check=True)
  cls.backend.d.sync()
  time.sleep(0.1)
  print('after',cls.backend._text_plan(':'),flush=True)
 def test_changed_layout(self):
  row=self.session.dispatch(make_program('changed-layout',text='http://a_b'),current_observation_seq=7,current_binding_revision=3)
  print('status',row['status'],flush=True)
  actual=json.loads(self.effect.read_text())
  print('saved',actual,flush=True)
  self.assertEqual(actual,{'saved':True,'text':'http://a_b'})
class ReverseLayout(ChangedLayout):
 @classmethod
 def setUpClass(cls):
  subprocess.run(['setxkbmap','-layout','us'],check=True)
  X11IntegrationTests.setUpClass.__func__(cls)
  subprocess.run(['setxkbmap','-layout','jp'],check=True)
  cls.backend.d.sync()
  time.sleep(0.1)
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ChangedLayout('test_changed_layout'),ReverseLayout('test_changed_layout')]))
raise SystemExit(not r.wasSuccessful())
