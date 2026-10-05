import importlib.util, os, sys, threading, time, types, unittest
from pathlib import Path
X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonRelease=5,Button1Mask=256,AnyPropertyType=0,IsViewable=2)
XK=types.SimpleNamespace(string_to_keysym=lambda s:s)
err=types.SimpleNamespace(BadWindow=type('BadWindow',(Exception,),{}),BadDrawable=type('BadDrawable',(Exception,),{}))
class Root:
 def query_pointer(self): return types.SimpleNamespace(mask=0)
class Display:
 def __init__(self): self.physical=set(); self.query_i=0; self.query_fail_on=set(); self.injections=[]; self.root=Root(); self.stuck={75}
 def get_input_focus(self): return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
 def keysym_to_keycode(self,s): return {'F8':74,'F9':75,'b':98}.get(s,0)
 def query_keymap(self):
  self.query_i+=1
  if self.query_i in self.query_fail_on: raise RuntimeError('injected aggregate keymap failure')
  a=bytearray(32)
  for c in self.physical:a[c//8]|=1<<(c%8)
  return a
 def sync(self): pass
 def screen(self): return types.SimpleNamespace(root=self.root)
 def close(self): pass
D=Display(); xlib=types.ModuleType('Xlib'); xlib.X=X; xlib.XK=XK; xlib.error=err
dm=types.ModuleType('Xlib.display'); dm.Display=lambda _name:D; xlib.display=dm
ext=types.ModuleType('Xlib.ext'); xt=types.ModuleType('Xlib.ext.xtest')
def fake_input(d,t,c=None,**kw):
 d.injections.append((t,c))
 if t==X.KeyPress:d.physical.add(c)
 elif t==X.KeyRelease:
  if c in d.stuck:d.stuck.remove(c)
  else:d.physical.discard(c)
xt.fake_input=fake_input; ext.xtest=xt
sys.modules.update({'Xlib':xlib,'Xlib.display':dm,'Xlib.ext':ext,'Xlib.ext.xtest':xt})
ex=types.ModuleType('executor_v3'); ex.Cancelled=type('Cancelled',(Exception,),{}); ex.DecisionRequired=type('DecisionRequired',(Exception,),{}); sys.modules['executor_v3']=ex
p=Path(os.environ['OWNER_SOURCE_PATH']); sp=importlib.util.spec_from_file_location('owner_under_test',p); M=importlib.util.module_from_spec(sp); sys.modules[sp.name]=M; sp.loader.exec_module(M)
class Lease:
 def __init__(self): self.expected_focus=42; self.focus_invalid=False; self.intent_token='intent'; self.deadline=time.perf_counter_ns()+30_000_000_000; self.cancel=threading.Event()
 def check(self):
  if time.perf_counter_ns()>=self.deadline:raise RuntimeError('expired')
class T(unittest.TestCase):
 def setUp(self): D.physical.clear(); D.query_i=0; D.query_fail_on.clear(); D.injections.clear(); D.stuck={75}; self.o=M.InputOwner(':fake'); self.l=Lease()
 def tearDown(self):
  try:self.o.close()
  except Exception:pass
 def test_non_neutral_successful_aggregate_must_fail_closed(self):
  self.o.call('down',self.l,'F8'); self.o.call('down',self.l,'F9')
  with self.assertRaisesRegex(RuntimeError,'owner release not verified'): self.o.call('release',self.l)
  rec=next(x for x in self.o.records if x.get('event')=='owner_release'); self.assertFalse(rec['verified']); self.assertEqual(rec['keys_down'],[75]); self.assertEqual(D.physical,{75})
  n=len(D.injections)
  with self.assertRaisesRegex(RuntimeError,'input owner failed closed'):self.o.call('down',self.l,'b')
  self.assertEqual(len(D.injections),n); self.assertNotIn(98,D.physical)
 def test_verified_neutral_release_allows_same_lease_followup(self):
  self.o.call('down',self.l,'F8'); r=self.o.call('release',self.l); self.assertTrue(r['verified']); self.o.call('down',self.l,'b'); self.assertIn(98,D.physical)
 def test_aggregate_query_exception_stays_fail_closed(self):
  self.o.call('down',self.l,'F8'); D.query_fail_on.add(5)
  with self.assertRaisesRegex(RuntimeError,'injected aggregate keymap failure'):self.o.call('release',self.l)
  n=len(D.injections)
  with self.assertRaisesRegex(RuntimeError,'input owner failed closed'):self.o.call('down',self.l,'b')
  self.assertEqual(len(D.injections),n); self.assertNotIn(98,D.physical)
if __name__=='__main__':unittest.main(verbosity=2)
