import json, sys, threading, time, types
from pathlib import Path
from hashlib import sha256

EVENTS=[]
DOWN=set()
class Root:
    id=1
    def query_pointer(self): return types.SimpleNamespace(mask=0,root_x=0,root_y=0)
class FakeDisplay:
    def __init__(self, _name): self.root=Root(); self.closed=False
    def get_input_focus(self): return types.SimpleNamespace(focus=41)
    def keysym_to_keycode(self, _symbol): return 38
    def screen(self): return types.SimpleNamespace(root=self.root)
    def query_keymap(self):
        bits=bytearray(32)
        for code in DOWN: bits[code//8] |= 1 << (code%8)
        return bytes(bits)
    def sync(self): pass
    def close(self): self.closed=True
xconst=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonRelease=5,Button1Mask=256,AnyPropertyType=0)
xlib=types.ModuleType('Xlib'); xlib.X=xconst
xk=types.ModuleType('Xlib.XK'); xk.string_to_keysym=lambda _key: 1; xlib.XK=xk
xd=types.ModuleType('Xlib.display'); xd.Display=FakeDisplay; xlib.display=xd
xe=types.ModuleType('Xlib.error'); xe.BadWindow=type('BadWindow',(Exception,),{}); xe.BadDrawable=type('BadDrawable',(Exception,),{}); xlib.error=xe
xext=types.ModuleType('Xlib.ext'); xtest=types.ModuleType('Xlib.ext.xtest')
def fake_input(_d,event,code):
    EVENTS.append([event,code])
    if event==xconst.KeyPress: DOWN.add(code)
    elif event==xconst.KeyRelease: DOWN.discard(code)
xtest.fake_input=fake_input; xext.xtest=xtest; xlib.ext=xext
sys.modules.update({'Xlib':xlib,'Xlib.X':types.ModuleType('Xlib.X'),'Xlib.XK':xk,'Xlib.display':xd,'Xlib.error':xe,'Xlib.ext':xext,'Xlib.ext.xtest':xtest})
executor=types.ModuleType('executor_v3'); executor.Cancelled=type('Cancelled',(Exception,),{}); executor.DecisionRequired=type('DecisionRequired',(Exception,),{}); sys.modules['executor_v3']=executor
class DummyOwner:
    def close(self): pass
class BaseBackend:
    def __init__(self,session,out,emit,signal_readers):
        self.session,self.out,self.emit,self.signal_readers=session,out,emit,signal_readers
        self.owner=DummyOwner(); self.held=set(); self.sequence=0; self.lease=None
    def execute(self,step,cancel,identifier,index):
        self.raw(step['key'],True)
        cancel.cancel=RaceCancel()
        self.raw(step['key'],False)
    def close(self): self.owner.close()
parent=types.ModuleType('doom_typed_release_backend_v1'); parent.Backend=BaseBackend; parent.suite=object(); sys.modules['doom_typed_release_backend_v1']=parent
class RaceCancel:
    def __init__(self): self.event=threading.Event(); self.caller=threading.get_ident(); self.first=True
    def is_set(self):
        if threading.get_ident()==self.caller and self.first:
            self.first=False; self.event.set(); return False
        return self.event.is_set()
class Lease:
    def __init__(self): self.intent_token='composition-intent'; self.deadline=time.perf_counter_ns()+5_000_000_000; self.cancel=threading.Event(); self.expected_focus=41; self.focus_invalid=False
    def check(self):
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError('expired')
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'FREEZE.json').read_text())
for rel, expected in freeze['sha256'].items():
    digest=sha256((ROOT/rel).read_bytes()).hexdigest()
    if digest != expected:
        raise RuntimeError('STOP_SOURCE_DRIFT:'+rel)
sys.path.insert(0,str(ROOT/'sources'))
import doom_typed_release_backend_v3 as runtime
emitted=[]
backend=runtime.Backend(types.SimpleNamespace(name=':fake'),None,emitted.append,{'health':object(),'ammo':object()})
lease=Lease(); backend.lease=lease
inner=backend.owner._inner; original=inner.call
def after_cleanup(operation,call_lease=None,key=None):
    if operation=='up':
        limit=time.monotonic()+2
        while not any(r.get('event')=='owner_release' and r.get('reason')=='cancelled' for r in inner.records):
            if time.monotonic()>=limit: raise TimeoutError('owner cleanup did not precede queued up')
            threading.Event().wait(.001)
    return original(operation,call_lease,key)
inner.call=after_cleanup
backend.execute({'op':'hold','key':'space','duration_ms':1},lease,'composition-probe',0)
owner_rows=backend.owner.records
backend.close()
result={'allocation_id':freeze['allocation_id'],'backend_class':backend.__class__.__module__+'.Backend','wrapper_class':backend.owner.__class__.__module__+'.InputOwner','events':emitted,'xtest_events':EVENTS,'owner_events':owner_rows,'down_after':sorted(DOWN)}
print(json.dumps(result,sort_keys=True))
