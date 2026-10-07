from pathlib import Path
import hashlib,json,os,subprocess,sys,time,threading,types
PKG=Path(__file__).resolve().parent
SOURCE=None
DOOM=LIVE=None
X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonPress=4,ButtonRelease=5,MotionNotify=6,Button1Mask=256,AnyPropertyType=0,IsViewable=2)
server_down=set(); requests=[]; fail_after_press=False; injected_count=0
class Focus: id=41
class Pointer: mask=0; root_x=10; root_y=10
class Root:
 def query_pointer(self): return Pointer()
 def translate_coords(self,_window,x,y): return types.SimpleNamespace(x=x,y=y)
class Screen: root=Root()
class FakeDisplay:
 def __init__(self,_name): self.down=server_down; self.closed=False
 def get_input_focus(self): return types.SimpleNamespace(focus=Focus())
 def keysym_to_keycode(self,_sym): return 38
 def query_keymap(self):
  b=bytearray(32)
  for code in self.down: b[code//8]|=1<<(code%8)
  return bytes(b)
 def screen(self): return Screen()
 def sync(self): pass
 def close(self): self.closed=True
 def create_resource_object(self,_kind,_ident): return types.SimpleNamespace(get_attributes=lambda:types.SimpleNamespace(map_state=X.IsViewable),get_geometry=lambda:types.SimpleNamespace(x=0,y=0,width=100,height=100),query_tree=lambda:types.SimpleNamespace(parent=types.SimpleNamespace(id=1)))
def fake_input(display,event,code,**_kwargs):
 global fail_after_press,injected_count
 requests.append({'event':event,'code':code})
 if event==X.KeyPress:
  display.down.add(code)
  if fail_after_press and injected_count==0:
   injected_count+=1
   raise OSError('injected response loss after fake-server delivery')
 elif event==X.KeyRelease: display.down.discard(code)

def install_xlib():
 xlib=types.ModuleType('Xlib'); xlib.X=X
 xlib.XK=types.SimpleNamespace(string_to_keysym=lambda _key:1)
 xlib.error=types.SimpleNamespace(BadWindow=type('BadWindow',(Exception,),{}),BadDrawable=type('BadDrawable',(Exception,),{}))
 display=types.ModuleType('Xlib.display'); display.Display=FakeDisplay
 ext=types.ModuleType('Xlib.ext'); xtest=types.ModuleType('Xlib.ext.xtest'); xtest.fake_input=fake_input; ext.xtest=xtest
 xlib.display,xlib.ext=display,ext
 sys.modules.update({'Xlib':xlib,'Xlib.X':types.ModuleType('Xlib.X'),'Xlib.XK':types.ModuleType('Xlib.XK'),'Xlib.error':types.ModuleType('Xlib.error'),'Xlib.display':display,'Xlib.ext':ext,'Xlib.ext.xtest':xtest})
def install_production_owner(owner_cls):
 from input_transition_owner_v4 import InputOwner
 return InputOwner('FAKE',_owner_cls=owner_cls)
class Lease:
 def __init__(self): self.deadline=time.perf_counter_ns()+10_000_000_000; self.cancel=threading.Event(); self.intent_token='alias-cleanup-a01'; self.expected_focus=41; self.focus_invalid=False
 def check(self): pass
 def interruption_snapshot(self): return None
 def record_interruption(self,_row): pass
 def is_set(self): return self.cancel.is_set()
 def wait(self,s): return self.cancel.wait(s)
 def set(self): self.cancel.set()
 def wait_interruption(self,_s): return None
class DummyOwner:
 def close(self): pass
class ControllerBackend:
 def __init__(self,session,_out,emit,_signal_readers): self.owner=DummyOwner(); self.lease=Lease(); self.held=set(); self.sequence=0; self.emit=emit; self.session=session; self._input_event_context=None; self.touched=set()
 def execute(self,step,_cancel,identifier,index):
  observed=self.session.context().get('focus'); actual=self.session.d.get_input_focus().focus.id
  if observed!=actual: raise ValueError('fake observed-focus admission failed')
  self.lease.expected_focus=observed; self._input_event_context=(identifier,index)
  try:
   for key,down in step['actions']: self.raw(key,down)
  finally: self._input_event_context=None
  return {'executed':len(step['actions'])}
 def validate(self,_steps): return None
 def release_all(self): return self.owner.call('release',self.lease)
class Session:
 name='FAKE'
 def __init__(self): self.d=FakeDisplay('FAKE_SESSION'); self.context=lambda:{'focus':41,'surface':42,'geometry':[0,0,100,100]}
def install_backend_imports():
 base=types.ModuleType('doom_typed_release_backend_v1'); base.Backend=ControllerBackend; base.suite=object(); sys.modules['doom_typed_release_backend_v1']=base
 import input_owner_v12
 input_owner_v12.X=X; input_owner_v12.XK=sys.modules['Xlib'].XK; input_owner_v12.display=types.SimpleNamespace(Display=FakeDisplay); input_owner_v12.error=types.SimpleNamespace(BadWindow=type('BadWindow',(Exception,),{}),BadDrawable=type('BadDrawable',(Exception,),{})); input_owner_v12.xtest=types.SimpleNamespace(fake_input=fake_input)
 base.InputOwner=lambda name:install_production_owner(input_owner_v12.InputOwner)
def worker(arm):
 global SOURCE,DOOM,LIVE,server_down,requests,fail_after_press,injected_count
 server_down=set(); requests=[]; fail_after_press=(arm=='delivered_error'); injected_count=0
 SOURCE=PKG/'sources'/'main'; DOOM=SOURCE/'research'/'doom'; LIVE=SOURCE/'research'/'live_control'; sys.path[:0]=[str(DOOM),str(LIVE)]
 install_xlib(); install_backend_imports()
 from doom_owner_thread_release_batch_backend_v1 import Backend
 from executor_v13 import Executor
 emitted=[]; backend=Backend(Session(),None,emitted.append,{})
 backend.owner=install_production_owner(__import__('input_owner_v12').InputOwner)
 engine=Executor(backend,emitted.append)
 actions=[('F8',True),('F8',False)] if arm=='normal' else [('F8',True)]
 identifier='normal-keypress-a01' if arm=='normal' else 'delivered-error-cleanup-a01'
 engine.submit(identifier,[{'op':'key_batch','actions':actions}],expected_sequence=backend.sequence,valid_until_ns=time.perf_counter_ns()+10_000_000_000)
 end=time.monotonic()+3; terminal=None
 while time.monotonic()<end:
  terminal=next((r for r in emitted if r.get('event')=='terminal'),None)
  if terminal: break
  time.sleep(.005)
 if terminal is None: raise RuntimeError('ExecutorV13 terminal timeout')
 engine.close()
 owner=backend.owner; records=list(owner._inner.records)
 owner.close()
 return {'arm':arm,'terminal':terminal,'events':emitted,'owner_records':records,'requests':requests,'final_server_keycodes_down':sorted(server_down),'injected_count':injected_count}
def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':
  print(json.dumps(worker(sys.argv[2]),sort_keys=True)); return 0
 cases=[]
 for arm in ('normal','delivered_error'):
  proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',arm],capture_output=True,text=True,timeout=10)
  try: row=json.loads(proc.stdout)
  except Exception: row={'arm':arm,'parse_error':repr(proc.stdout),'stderr':proc.stderr}
  row['worker_exit_code']=proc.returncode; row['worker_stderr']=proc.stderr
  cases.append(row)
 raw={'schema':'issue59-input-ack-loss-cleanup-a02-raw-v1','run_id':json.loads((PKG/'FREEZE.json').read_text())['run_id'],'main_commit':json.loads((PKG/'FREEZE.json').read_text())['main_commit'],'cases':cases,'scope':{'real_x11':False,'gui':False,'physical_input':False,'doom':False,'model':False,'application_effect':False}}
 out=PKG/'results'/'raw.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(raw,indent=2,sort_keys=True)+chr(10),encoding='utf-8')
 print(json.dumps({'raw':str(out),'arms':len(cases),'worker_exits':[r['worker_exit_code'] for r in cases]},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
