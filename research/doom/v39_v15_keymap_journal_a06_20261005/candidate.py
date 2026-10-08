import json, sys, types, threading, time
from pathlib import Path

TRACE=[]; TRACE_LOCK=threading.Lock(); SERVER_KEYS=set(); DROP_UP=None; FAIL_QUERY=False; POST_SAMPLE=None
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
    def __init__(self,name): self.keys=SERVER_KEYS; FakeDisplay.last=self; record("display_open",name=name)
    def get_input_focus(self): record("query_focus"); return FocusReply()
    def screen(self): return Screen()
    def keysym_to_keycode(self,symbol): return {"F8":74,"space":65}.get(symbol,0)
    def sync(self): record("sync",held=sorted(self.keys))
    def query_keymap(self):
        global FAIL_QUERY
        if FAIL_QUERY:
            record("query_keymap",error="sampler_unavailable")
            raise RuntimeError("sampler unavailable")
        record("query_keymap",held=sorted(self.keys))
        bits=bytearray(32)
        for code in self.keys: bits[code//8] |= 1 << (code%8)
        return bits
    def close(self): record("display_close")
def fake_input(display,event_type,detail,**kwargs):
    global DROP_UP
    if event_type==FakeX.KeyPress:
        display.keys.add(detail); record("xtest_key_down",keycode=detail)
    elif event_type==FakeX.KeyRelease:
        if detail==DROP_UP:
            DROP_UP=None
            record("xtest_key_up_suppressed_once",keycode=detail)
        else:
            display.keys.discard(detail); record("xtest_key_up",keycode=detail)
    else: record("xtest_other",event_type=event_type,detail=detail)

xlib=types.ModuleType("Xlib"); xlib.X=FakeX
xlib.XK=types.SimpleNamespace(string_to_keysym=lambda s:s)
xlib.display=types.SimpleNamespace(Display=FakeDisplay)
xlib.error=types.SimpleNamespace(BadWindow=type("BadWindow",(Exception,),{}),BadDrawable=type("BadDrawable",(Exception,),{}))
ext=types.ModuleType("Xlib.ext"); xtest=types.ModuleType("Xlib.ext.xtest"); xtest.fake_input=fake_input
ext.xtest=xtest
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

base=Path(__file__).resolve().parent; sys.path[:0]=[str(base/"sources/research/live_control"),str(base/"sources/research/doom")]
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

BASE=Path(__file__).resolve().parent
RUN=BASE/"run"
CASE_JOURNAL=RUN/"cases.jsonl"
FAILURE_JOURNAL=RUN/"failures.jsonl"

def append_jsonl(path, value):
    with path.open("a",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n")
        stream.flush()

def run_case(case_name, drop_key=None, fail_query=False):
    global TRACE, SERVER_KEYS, DROP_UP, FAIL_QUERY, POST_SAMPLE
    TRACE=[]; SERVER_KEYS=set(); DROP_UP=drop_key; FAIL_QUERY=fail_query; POST_SAMPLE=None; FakeDisplay.last=None
    rows=[]
    backend=Backend(Session(),None,lambda row: None,[])
    orig_call=backend.owner.call
    def observed_call(operation, lease=None, key=None):
        global POST_SAMPLE
        result=orig_call(operation,lease,key)
        if operation=="input_state":
            sampler=FakeDisplay("post_batch_keymap_sampler")
            try:
                bits=sampler.query_keymap()
                down=[code for code in (65,74) if bits[code//8] & (1 << (code%8))]
                POST_SAMPLE={"status":"SAMPLED","keycodes_down":down}
                record("post_batch_keymap_sample",status="SAMPLED",keycodes_down=down)
            except BaseException as exc:
                POST_SAMPLE={"status":"UNKNOWN","keycodes_down":None,"error_type":type(exc).__name__}
                record("post_batch_keymap_sample",status="UNKNOWN",error_type=type(exc).__name__)
            finally:
                sampler.close()
        return result
    backend.owner.call=observed_call
    def emit(row):
        key=row.get("key")
        keycode={"space":65,"F8":74}.get(key)
        sample=POST_SAMPLE or {"status":"UNKNOWN","keycodes_down":None}
        row["post_batch_server_keymap_status"]=sample["status"]
        row["post_batch_server_keycodes_down"]=sample["keycodes_down"]
        row["post_batch_server_key_down"]=(
            (keycode in sample["keycodes_down"]) if keycode is not None and sample["status"]=="SAMPLED" else None
        )
        row["instrumented_release_verified"]=(
            sample["status"]=="SAMPLED" and keycode not in sample["keycodes_down"]
            if keycode is not None else False
        ) if sample["status"]=="SAMPLED" else None
        rows.append(dict(row))
        record("telemetry_publish",key=key,status=row["post_batch_server_keymap_status"])
    backend.emit=emit
    try:
        result=backend.execute({"down":["F8","space"],"up":["space","F8"]},threading.Event(),f"a06-{case_name}",0)
        pre_cleanup=sorted(SERVER_KEYS)
        backend.owner.close()
        case={"name":case_name,"trace":list(TRACE),"release_rows":rows,
              "owner_records":list(backend.owner.records),"pre_cleanup_keycodes_down":pre_cleanup,
              "final_server_keycodes_down":sorted(SERVER_KEYS),"execution":result,
              "claims":{"physical_keyboard":False,"application":False}}
        append_jsonl(CASE_JOURNAL,case)
        return case
    except BaseException as exc:
        failure={"name":case_name,"trace":list(TRACE),"partial_release_rows":rows,
                 "server_keycodes_down":sorted(SERVER_KEYS),
                 "error_type":type(exc).__name__,"error":str(exc),
                 "cleanup_retried":False,
                 "claims":{"physical_keyboard":False,"application":False}}
        append_jsonl(FAILURE_JOURNAL,failure)
        raise

RUN.mkdir(parents=True,exist_ok=True)
CASE_JOURNAL.write_text("",encoding="utf-8")
FAILURE_JOURNAL.write_text("",encoding="utf-8")
cases=[]; failures=[]
scenarios=[
    ("normal",None,False),
    ("one_shot_suppressed_space_up",65,False),
    ("sampler_unavailable",None,True),
]
for name,drop,fail_query in scenarios:
    try:
        cases.append(run_case(name,drop_key=drop,fail_query=fail_query))
    except BaseException as exc:
        failures.append({"case":name,"error_type":type(exc).__name__,"error":str(exc)})
        break
raw={"schema":"v39-v15-keymap-journal-a06-raw-v1","cases":cases,"failures":failures,
     "case_journal":"run/cases.jsonl","failure_journal":"run/failures.jsonl",
     "claims":{"real_x11":False,"real_input":False,"application":False,"physical_keyboard":False}}
print(json.dumps(raw,sort_keys=True,separators=(",",":")))
if failures: sys.exit(1)
