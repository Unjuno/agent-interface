import json, sys, types, threading, time
from pathlib import Path

TRACE=[]; TRACE_LOCK=threading.Lock()
def record(kind, **fields):
    with TRACE_LOCK: TRACE.append({"n":len(TRACE), "kind":kind, **fields})

class FakeX:
    KeyPress=2; KeyRelease=3; ButtonPress=4; ButtonRelease=5
    Button1Mask=256; AnyPropertyType=0; IsViewable=2; MotionNotify=6
class Focus: id=99
class FocusReply: focus=Focus()
class Point: mask=0; root_x=0; root_y=0
class Root:
    id=1
    def query_pointer(self): record("query_pointer"); return Point()
class Screen: root=Root()
class FakeDisplay:
    last=None
    def __init__(self,name): self.keys=set(); FakeDisplay.last=self; record("display_open",name=name)
    def get_input_focus(self): record("query_focus"); return FocusReply()
    def screen(self): return Screen()
    def keysym_to_keycode(self,symbol): return {"a":30,"b":31}.get(symbol,0)
    def sync(self): record("sync",held=sorted(self.keys))
    def query_keymap(self):
        record("query_keymap",held=sorted(self.keys))
        bits=bytearray(32)
        for code in self.keys: bits[code//8] |= 1 << (code%8)
        return bits
    def close(self): record("display_close")
def fake_input(display,event_type,detail,**kwargs):
    if event_type==FakeX.KeyPress:
        display.keys.add(detail); record("xtest_key_down",keycode=detail)
    elif event_type==FakeX.KeyRelease:
        display.keys.discard(detail); record("xtest_key_up",keycode=detail)
    else: record("xtest_other",event_type=event_type,detail=detail)

xlib=types.ModuleType("Xlib"); xlib.X=FakeX
xlib.XK=types.SimpleNamespace(string_to_keysym=lambda s:s)
xlib.display=types.SimpleNamespace(Display=FakeDisplay)
xlib.error=types.SimpleNamespace(BadWindow=type("BadWindow",(Exception,),{}),BadDrawable=type("BadDrawable",(Exception,),{}))
ext=types.ModuleType("Xlib.ext"); xtest=types.ModuleType("Xlib.ext.xtest"); xtest.fake_input=fake_input
sys.modules.update({"Xlib":xlib,"Xlib.ext":ext,"Xlib.ext.xtest":xtest})
executor=types.ModuleType("executor_v3")
executor.Cancelled=type("Cancelled",(Exception,),{}); executor.DecisionRequired=type("DecisionRequired",(Exception,),{})
sys.modules["executor_v3"]=executor

class PreviousBackend:
    suite=()
    def __init__(self,session,out,emit,signal_readers):
        self.session=session; self.out=out; self.emit=emit; self.signal_readers=signal_readers
        self.owner=types.SimpleNamespace(close=lambda:None)
        self.lease=session.lease; self.held=set(); self._input_event_context=None
    def execute(self,step,cancel,identifier,index):
        for key in step["down"]: self.raw(key,True)
        for key in step["up"]: self.raw(key,False)
        return {"executed":True}
previous=types.ModuleType("doom_typed_release_backend_v2")
previous.Backend=PreviousBackend; previous.suite=()
sys.modules["doom_typed_release_backend_v2"]=previous

src=Path(__file__).resolve().parent/"sources"; sys.path.insert(0,str(src))
from doom_owner_thread_release_batch_backend_v1 import Backend
class Lease:
    def __init__(self):
        self.expected_focus=99; self.deadline=time.perf_counter_ns()+10_000_000_000
        self.cancel=threading.Event(); self.focus_invalid=False; self.intent_token="a01-token"
    def check(self):
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError("expired")
class Session:
    name="FAKE"
    def __init__(self): self.lease=Lease()

rows=[]
backend=Backend(Session(),None,rows.append,[])
original_call=backend.owner.call
def traced_call(operation,lease=None,key=None):
    record("call_begin",operation=operation,key=key)
    result=original_call(operation,lease,key)
    record("call_return",operation=operation,key=key)
    return result
backend.owner.call=traced_call
try:
    result=backend.execute({"down":["a","b"],"up":["b","a"]},threading.Event(),"a01-program",0)
    owner_records=list(backend.owner.records)
    release_rows=rows[:]
    final_keys=sorted(FakeDisplay.last.keys)
    backend.owner.close()
except BaseException:
    try: backend.owner.close()
    finally: raise
state=release_rows[0].get("owned_keycodes_after_batch") if release_rows else None
raw={"schema":"v39-v15-up-order-a01-raw-v1","trace":TRACE,"backend_result":result,
 "release_rows":release_rows,"owner_records":owner_records,
 "post_release_owned_keycodes":state,"final_fake_keys":final_keys,
 "claims":{"real_x11":False,"real_input":False,"application":False}}
print(json.dumps(raw,sort_keys=True,separators=(",",":")))

