import ast, importlib.util, json, sys, types, threading, time
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"sources"/"research"
DOOM=SRC/"doom"
LIVE=SRC/"live_control"
sys.path[:0]=[str(DOOM),str(LIVE)]
OUT=ROOT/"run"/"runtime"
OUT.mkdir(parents=True,exist_ok=True)
TRACE=[]; SERVER_KEYS=set(); ROWS=[]; ROUTE={}; CASES=[]; CURRENT_CASE=None; SUPPRESS_KEYCODE=None; PRE_SAMPLE=None; POST_SAMPLE=None

def record(kind,**fields): TRACE.append({"n":len(TRACE),"case":CURRENT_CASE,"kind":kind,**fields})

class FakeX:
    KeyPress=2; KeyRelease=3; ButtonPress=4; ButtonRelease=5
    Button1Mask=256; AnyPropertyType=0; IsViewable=2; MotionNotify=6
class Focus: id=99
class FocusReply: focus=Focus()
class Point: mask=0; root_x=0; root_y=0
class Root:
    id=1
    def query_pointer(self): record("owner_query_pointer"); return Point()
class Screen: root=Root()
class FakeDisplay:
    def __init__(self,name): self.keys=SERVER_KEYS; self.name=name; record("display_open",name=name)
    def get_input_focus(self): record("owner_query_focus"); return FocusReply()
    def screen(self): return Screen()
    def keysym_to_keycode(self,symbol): return {"space":65,"F8":74}.get(symbol,0)
    def sync(self): record("x_sync",held=sorted(self.keys))
    def query_keymap(self):
        record("query_keymap",display=self.name,held=sorted(self.keys))
        bits=bytearray(32)
        for code in self.keys: bits[code//8]|=1<<(code%8)
        return bits
    def close(self): record("display_close",name=self.name)
def fake_input(display,event_type,detail,**kwargs):
    if event_type==FakeX.KeyPress:
        display.keys.add(detail);record("xtest_key_down",keycode=detail)
    elif event_type==FakeX.KeyRelease:
        record("xtest_key_up_attempt",keycode=detail)
        if SUPPRESS_KEYCODE == detail:
            record("xtest_key_up_suppressed",keycode=detail)
        else:
            display.keys.discard(detail);record("xtest_key_up_delivered",keycode=detail)
    else:record("xtest_other",event_type=event_type,detail=detail)
xlib=types.ModuleType("Xlib");xlib.X=FakeX;xlib.XK=SimpleNamespace(string_to_keysym=lambda s:s)
xlib.display=SimpleNamespace(Display=FakeDisplay)
xlib.error=SimpleNamespace(BadWindow=type("BadWindow",(Exception,),{}),BadDrawable=type("BadDrawable",(Exception,),{}))
ext=types.ModuleType("Xlib.ext");xtest=types.ModuleType("Xlib.ext.xtest");xtest.fake_input=fake_input;ext.xtest=xtest
sys.modules.update({"Xlib":xlib,"Xlib.ext":ext,"Xlib.ext.xtest":xtest})

executor3=types.ModuleType("executor_v3")
executor3.Cancelled=type("Cancelled",(Exception,),{});executor3.DecisionRequired=type("DecisionRequired",(Exception,),{})
class ExecutorV12Stub:
    def __init__(self,*args,**kwargs): pass
executor12=types.ModuleType("executor_v12");executor12.Executor=ExecutorV12Stub
lease=types.ModuleType("lease");lease.Expired=type("Expired",(Exception,),{})
sys.modules.update({"executor_v3":executor3,"executor_v12":executor12,"lease":lease})
# Load the exact current V13 class body; its lower ExecutorV12 runtime boundary is stubbed.
spec=importlib.util.spec_from_file_location("executor_v13",LIVE/"executor_v13.py")
executor13=importlib.util.module_from_spec(spec);sys.modules["executor_v13"]=executor13;spec.loader.exec_module(executor13)

typed=types.ModuleType("doom_typed_release_backend_v2")
class PreviousBackend:
    suite=()
    def __init__(self,session,out,emit,signal_readers):
        self.session=session;self.out=out;self.emit=emit;self.signal_readers=signal_readers
        self.owner=SimpleNamespace(close=lambda:None);self.lease=session.lease;self.held=set();self._input_event_context=None
    def execute(self,step,cancel,identifier,index):
        self._input_event_context=(identifier,index)
        try:
            for key in step["down"]: self.raw(key,True)
            for key in step["up"]: self.raw(key,False)
            return {"executed":True}
        finally:self._input_event_context=None
typed.Backend=PreviousBackend;typed.suite=()
sys.modules["doom_typed_release_backend_v2"]=typed

scorer=types.ModuleType("map01_scorer_stdio_adapter_v1")
class FakeSink:
    def __init__(self,out): self.out=out;record("v15_scorer_sink_created")
    def direct(self,*args,**kwargs): record("scorer_direct")
    def finalize(self,*args,**kwargs): record("v15_scorer_sink_finalized")
class FakePolling:
    def __init__(self,stdin,sample_game,sink,sample_hz=35.0):self._stats={};record("v15_scorer_polling_created",sample_hz=sample_hz)
    def stats(self):return self._stats
scorer.MainThreadScorerStdin=FakePolling;scorer.ScorerFileSink=FakeSink
clock=types.ModuleType("independent_progress_clock_v2");clock.ProgressSample=type("ProgressSample",(),{})
sys.modules.update({"map01_scorer_stdio_adapter_v1":scorer,"independent_progress_clock_v2":clock})

# Execute the exact V39 session_command function extracted from the pinned source lines.
selector_text=(SRC/"doom"/"controller_session_command.py").read_text(encoding="utf-8")
selector_module=ast.parse(selector_text)
selector_func=next(n for n in selector_module.body if isinstance(n,ast.FunctionDef) and n.name=="session_command")
selector_ns={"sys":sys,"Path":Path,"HERE":DOOM}
exec(compile(ast.Module(body=[selector_func],type_ignores=[]),"<pinned-v39-session-command>","exec"),selector_ns)
args=SimpleNamespace(measurement_session=True,seed=20261005,load_fixture_manifest=Path("fixture.json"))
command=selector_ns["session_command"](args,OUT)
selected_session=Path(command[1])
ROUTE["selector_command"]=command
ROUTE["selected_session"]=selected_session.name
ROUTE["selected_is_v15"]=selected_session.name=="session_map01_v15.py"
if not ROUTE["selected_is_v15"]: raise AssertionError("V39 selector did not choose V15")

class Lease:
    def __init__(self):
        self.expected_focus=99;self.deadline=time.perf_counter_ns()+10_000_000_000
        self.cancel=threading.Event();self.focus_invalid=False;self.intent_token="a07-token"
    def check(self):
        if time.perf_counter_ns()>=self.deadline:raise RuntimeError("lease expired")
class Session: name="FAKE"
Session.lease=Lease()

base=types.ModuleType("session_map01_v12")
class FakeGame: pass
base.vd=SimpleNamespace(DoomGame=FakeGame,GameVariable=SimpleNamespace())
base.sys=sys

def base_main():
    global CURRENT_CASE, SUPPRESS_KEYCODE, PRE_SAMPLE, POST_SAMPLE, ROWS
    route_backend=base.Backend;route_executor=base.Executor
    ROUTE["installed_backend"]=f"{route_backend.__module__}.{route_backend.__name__}"
    ROUTE["installed_executor"]=f"{route_executor.__module__}.{route_executor.__name__}"
    ROUTE["backend_is_release_batch_v1"]=route_backend.__module__=="doom_owner_thread_release_batch_backend_v1"
    ROUTE["executor_is_v13"]=route_executor is executor13.Executor
    def snapshot(stage):
        sampler=FakeDisplay(stage+"_batch_sampler")
        bits=sampler.query_keymap()
        down=[code for code in (65,74) if bits[code//8]&(1<<(code%8))]
        record("keymap_sample_result",stage=stage,keycodes_down=down)
        sampler.close()
        return {"status":"SAMPLED","keycodes_down":down}
    for case_id,suppress in (("normal",None),("lost_space_keyrelease",65)):
        CURRENT_CASE=case_id; SUPPRESS_KEYCODE=suppress; PRE_SAMPLE=None; POST_SAMPLE=None; ROWS=[]; SERVER_KEYS.clear(); TRACE.clear()
        backend=route_backend(Session(),None,lambda row:None,[])
        original_call=backend.owner.call
        def measured_call(operation,lease_arg=None,key=None):
            global PRE_SAMPLE, POST_SAMPLE
            if operation=="up" and PRE_SAMPLE is None:
                PRE_SAMPLE=snapshot("pre")
            result=original_call(operation,lease_arg,key)
            if operation=="input_state":
                POST_SAMPLE=snapshot("post")
            return result
        backend.owner.call=measured_call
        def emit(row):
            if isinstance(row,dict) and row.get("event")=="input_release_transition":
                code={"space":65,"F8":74}.get(row.get("key"))
                before=(PRE_SAMPLE or {}).get("keycodes_down")
                after=(POST_SAMPLE or {}).get("keycodes_down")
                row["pre_batch_keymap_status"]=(PRE_SAMPLE or {}).get("status","UNKNOWN")
                row["pre_batch_keycodes_down"]=before
                row["post_batch_keymap_status"]=(POST_SAMPLE or {}).get("status","UNKNOWN")
                row["post_batch_keycodes_down"]=after
                row["post_batch_key_down"]=(code in after) if code is not None and isinstance(after,list) else None
                row["sample_classification"]=("ABSENT_AT_POST_SAMPLE" if code in before and code not in after else "STILL_DOWN_AT_POST_SAMPLE" if code in before and code in after else "NOT_DOWN_AT_PRE_SAMPLE") if isinstance(before,list) and isinstance(after,list) else "UNKNOWN"
            ROWS.append(dict(row));record("telemetry_emit",event=row.get("event"),key=row.get("key"))
        backend.emit=emit
        execute_error=None
        try:
            execution=backend.execute({"down":["F8","space"],"up":["space","F8"]},threading.Event(),"a02-program-"+case_id,0)
        except BaseException as exc:
            execution=None;execute_error={"type":type(exc).__name__,"message":str(exc)}
        records=list(getattr(backend.owner,"records",[]))
        server_before_close=sorted(SERVER_KEYS)
        close_error=None
        try: backend.owner.close()
        except BaseException as exc: close_error={"type":type(exc).__name__,"message":str(exc)};record("owner_close_error",**close_error)
        CASES.append({"case":case_id,"suppressed_keycode":suppress,"execution":execution,"execute_error":execute_error,"pre_sample":PRE_SAMPLE,"post_sample":POST_SAMPLE,"rows":ROWS,"owner_records":records,"server_keys_before_close":server_before_close,"final_server_keys":sorted(SERVER_KEYS),"close_error":close_error,"trace":TRACE.copy()})
    CURRENT_CASE=None
base.main=base_main
base.main=base_main
sys.modules["session_map01_v12"]=base

sys.argv=["session_map01_v15.py","--out",str(OUT),"--timeout-seconds","10"]
v15_spec=importlib.util.spec_from_file_location("session_map01_v15",selected_session)
v15=importlib.util.module_from_spec(v15_spec);sys.modules["session_map01_v15"]=v15;v15_spec.loader.exec_module(v15)
ROUTE["v15_module_sha256_claim"]="source frozen by repository base commit"
v15.main()
raw={"schema":"v39-v15-selected-path-prepost-a02-raw-v1","route":ROUTE,"cases":CASES,
     "claims":{"real_x11":False,"real_input":False,"application":False,"physical_keyboard":False,"full_controller_loop":False}}
print(json.dumps(raw,sort_keys=True,separators=(",",":")))
