"""Private scientific actors; public runtime copies remain byte-identical."""
import json
import os
import sys
import time
import traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/"source"))
from Xlib import X
from Xlib.ext import xtest
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
now=time.monotonic_ns
def emit(event,**data): print(json.dumps({"event":event,**data}),flush=True)
def process_state(pid):
    try:
        tail=Path("/proc/"+str(pid)+"/stat").read_text().rsplit(") ",1)[1].split()
        return tail[0],int(tail[19])
    except FileNotFoundError: return "missing",None
def query(backend,tag):
    start=now(); bits=backend.d.query_keymap(); mask=backend.root.query_pointer().mask
    return {"tag":tag,"query_started_ns":start,"at_ns":now(),"keymap":bytes(bits).hex(),
            "buttons":mask & (X.Button1Mask|X.Button2Mask|X.Button3Mask)}
def trace_native():
    original=xtest.fake_input; calls=[]
    def traced(d,kind,code,*args,**kwargs):
        call={"kind":{X.KeyPress:"press",X.KeyRelease:"release"}.get(kind,str(kind)),
              "code":int(code),"started_ns":now()}
        result=original(d,kind,code,*args,**kwargs);call["returned_ns"]=now()
        calls.append(call);emit("native",call=call);return result
    xtest.fake_input=traced
    return calls
def owner(params,life):
    backend=X11Backend(params["display"],{"owned":params["window_id"]});trace_native()
    emit("init",pid=os.getpid(),nonce=params["nonce"],at_ns=now(),held=dict(backend.held_keycodes),
         keycode=backend._keycode("F8"),emissions=backend.emissions)
    if sys.stdin.readline().strip()!="GO": raise RuntimeError("STOP_OWNER_START_TOKEN")
    program={"schema":"agent-interface/program-v1","program_id":params["id"],
       "source":{"observation_seq":1,"binding_revision":0},
       "authority":{"lease_id":"owned-7024","expires_at_ns":now()+2_000_000_000},
       "terminal":{"release_all_required":True},
       "ops":[{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},
              {"op":"wait_update","timeout_ms":params["wait_ms"]},{"op":"release_all"}]}
    original_wait=backend._wait_update
    def wait_gate(ms):
        emit("ready",at_ns=now(),held=dict(backend.held_keycodes),emissions=backend.emissions,
             stack=[f.name for f in traceback.extract_stack()],program_input=program)
        original_wait(ms)
    backend._wait_update=wait_gate
    result=X11RuntimeSession(backend).dispatch(program,current_observation_seq=1,current_binding_revision=0)
    emit("completed",at_ns=now(),result=result)
    backend.close();os.close(life)
def supervisor(params,life):
    cap=params["capability"]; backend=X11Backend(cap["display"],{"owned":cap["window_id"]})
    calls=trace_native()
    state,ticks=process_state(cap["owner_pid"])
    if state in ("Z","missing") or ticks!=cap["owner_start_ticks"]: raise RuntimeError("STOP_OWNER_NOT_LIVE_AT_PREARM")
    emit("registered",at_ns=now(),held=dict(backend.held_keycodes),emissions=backend.emissions,capability=cap)
    if os.read(life,1)!=b"": raise RuntimeError("STOP_LIFETIME_PIPE_NOT_EOF")
    eof=now();state,ticks=process_state(cap["owner_pid"]); dead=now()
    if state not in ("Z","missing") or state=="Z" and ticks!=cap["owner_start_ticks"]:
        raise RuntimeError("STOP_EOF_NOT_ORIGINAL_OWNER_DEATH")
    before=query(backend,"supervisor_before");code=cap["keys"]["F8"]
    down=bool(bytes.fromhex(before["keymap"])[code//8]&(1<<(code%8)))
    scope=dict(cap["keys"])if params["policy"]=="prearmed_scope" and down else{}
    # Research-only injection of a prearmed cleanup catalog, never task authority.
    backend.held_keycodes=dict(scope)
    start=now();receipt=backend.release_all();end=now();after=query(backend,"supervisor_after")
    emit("result",eof_ns=eof,dead_ns=dead,death_state=state,death_start_ticks=ticks,
         before=before,after=after,scope=scope,release_started_ns=start,release_returned_ns=end,
         receipt=receipt,emissions=backend.emissions,native_calls=calls)
    backend.close();os.close(life)
def main():
    role=sys.argv[1];params=json.loads(sys.argv[2]);life=int(sys.argv[3])
    try: {"owner":owner,"supervisor":supervisor}[role](params,life)
    except Exception: emit("error",traceback=traceback.format_exc());raise
if __name__=="__main__":main()
