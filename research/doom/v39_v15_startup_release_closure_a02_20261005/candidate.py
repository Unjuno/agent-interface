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
ext.xtest=xtest
sys.modules.update({"Xlib":xlib,"Xlib.ext":ext,"Xlib.ext.xtest":xtest})
class PreviousBackend:
    suite=()
    def __init__(self,session,out,emit,signal_readers):
        self.session=session; self.out=out; self.emit=emit; self.signal_readers=signal_readers
        self.owner=types.SimpleNamespace(close=lambda:None)
        self.lease=session.lease; self.held=set(); self._input_event_context=None
    def execute(self,step,cancel,identifier,index):
        self._input_event_context=(identifier,index)
        try:
            for key in step["down"]: self.raw(key,True)
            for key in step["up"]: self.raw(key,False)
            return {"executed":True}
        finally:
            self._input_event_context=None
previous=types.ModuleType("doom_typed_release_backend_v2")
previous.Backend=PreviousBackend; previous.suite=()
sys.modules["doom_typed_release_backend_v2"]=previous

repo=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(repo/"research/live_control"),str(repo/"research/doom")]

class ProgressSample:
    def __init__(self,*values): self.values=values
scorer=types.ModuleType("map01_scorer_stdio_adapter_v1")
class Polling:
    def __init__(self,*args,**kwargs): self.args=args
    def stats(self): return {"synthetic":True}
class Sink:
    def __init__(self,out): self.out=out
    def direct(self,*args): record("scorer_direct")
    def finalize(self,*args): record("scorer_finalize")
scorer.MainThreadScorerStdin=Polling; scorer.ScorerFileSink=Sink
clock=types.ModuleType("independent_progress_clock_v2"); clock.ProgressSample=ProgressSample
sys.modules["map01_scorer_stdio_adapter_v1"]=scorer
sys.modules["independent_progress_clock_v2"]=clock

class FakeGame:
    def init(self): record("game_init")
    def close(self): record("game_close")
    def get_episode_time(self): return 1
    def is_episode_finished(self): return False
    def is_player_dead(self): return False
    def get_game_variable(self,name): return 0
    def get_ticrate(self): return 35
    def is_episode_timeout_reached(self): return False

base_module=types.ModuleType("session_map01_v12")
base_module.vd=types.SimpleNamespace(
    DoomGame=FakeGame,
    GameVariable=types.SimpleNamespace(KILLCOUNT="KILLCOUNT",DEATHCOUNT="DEATHCOUNT"))
base_module.sys=sys
class Lease:
    def __init__(self):
        self.expected_focus=99; self.deadline=time.perf_counter_ns()+10_000_000_000
        self.cancel=threading.Event(); self.focus_invalid=False; self.intent_token="a01-token"
    def check(self):
        if time.perf_counter_ns()>=self.deadline: raise RuntimeError("expired")
class Session:
    name="FAKE"
    def __init__(self): self.lease=Lease()

captured={}; rows=[]
def base_main():
    backend_type=base_module.Backend
    executor_type=base_module.Executor
    captured["selected_backend"]=backend_type.__module__+"."+backend_type.__name__
    captured["selected_executor"]=executor_type.__module__+"."+executor_type.__name__
    captured["v12_main_test_shim"]=True
    game=base_module.vd.DoomGame(); game.init()
    backend=backend_type(Session(),None,rows.append,[])
    original_call=backend.owner.call
    def traced_call(operation,lease=None,key=None):
        record("call_begin",operation=operation,key=key)
        result=original_call(operation,lease,key)
        record("call_return",operation=operation,key=key)
        return result
    backend.owner.call=traced_call
    try:
        backend.execute({"down":["a","b"],"up":["b","a"]},
                        threading.Event(),"v15-a01-program",0)
        captured["owner_records"]=list(backend.owner.records)
        captured["release_rows"]=[dict(row) for row in rows]
        captured["owner_id"]=backend.owner.owner_id
        captured["final_fake_keys_before_owner_close"]=sorted(FakeDisplay.last.keys)
    finally:
        backend.owner.close()
        game.close()
    captured["final_fake_keys"]=sorted(FakeDisplay.last.keys)
base_module.main=base_main
sys.modules["session_map01_v12"]=base_module

import tempfile
from collections import OrderedDict
with tempfile.TemporaryDirectory(prefix="v15-startup-a01-") as output:
    out=Path(output); (out/"sources.json").write_text("{}",encoding="utf-8")
    old_argv=sys.argv
    sys.argv=["session_map01_v15","--out",str(out),"--timeout-seconds","600"]
    try:
        import session_map01_v15 as v15
        v15.main()
    finally:
        sys.argv=old_argv
    captured["session_source_hashes"]=json.loads((out/"sources.json").read_text(encoding="utf-8"))

batch_rows=[r for r in captured["release_rows"] if r.get("event")=="input_release_transition"]
release_projection=[{k:r.get(k) for k in (
 "event","key","owner_id","intent_token","owner_thread_keyup_receipt",
 "owner_thread_keyup_verified","release_batch_complete","release_batch_position",
 "release_batch_size","owner_transition_verified","owned_keycodes_after_batch",
 "owner_sample_after_started_ns","owner_sample_after_finished_ns",
 "owner_sample_ordered_after_batch","release_call_started_ns","release_call_returned_ns"
 )} for r in batch_rows]
raw={"schema":"v39-v15-startup-release-closure-a01-raw-v1","trace":TRACE,
 "selection":{"backend":captured.get("selected_backend"),"executor":captured.get("selected_executor"),
              "v12_main_test_shim":captured.get("v12_main_test_shim")},
 "release_rows":release_projection,"owner_records":captured["owner_records"],
 "session_source_hashes":captured["session_source_hashes"],
 "post_release_owned_keycodes":release_projection[-1].get("owned_keycodes_after_batch") if release_projection else None,
 "final_fake_keys_before_owner_close":captured["final_fake_keys_before_owner_close"],
 "final_fake_keys":captured["final_fake_keys"],
 "claims":{"real_x11":False,"real_input":False,"application":False,"game":False,"model":False}}
print(json.dumps(raw,sort_keys=True,separators=(",",":")))
