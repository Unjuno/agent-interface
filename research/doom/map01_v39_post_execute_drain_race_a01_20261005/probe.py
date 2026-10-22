import importlib.util, sys, threading, time, json
from pathlib import Path

fix=Path("source/research/doom/map01_v39_cancel_release_fix_a01_20261005")
bt_path=Path("source/research/doom/map01_v39_perkey_bridge_a01/test_bridge.py")
spec=importlib.util.spec_from_file_location("bridge_test",bt_path)
bt=importlib.util.module_from_spec(spec);sys.modules[spec.name]=bt;spec.loader.exec_module(bt)
hm=bt.load_v12_test_harness()
owner_module=hm.load("input_owner_v13_candidate",fix/"input_owner_v13_candidate.py")
sys.path.insert(0,str(fix))
spec=importlib.util.spec_from_file_location("bridge_v2_candidate",fix/"bridge_v2_candidate.py")
bm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=bm;spec.loader.exec_module(bm)
h=hm.Harness(owner_module)
backend=object.__new__(bm.Backend)
backend.owner=h.owner;backend.lease=None;backend.held=set();backend._input_event_context=None
backend._owner_record_cursor=0;backend.events=[]
admitted=threading.Event(); drained=threading.Event(); armed=threading.Event()
focus_blocked=threading.Event(); allow_focus=threading.Event(); terminal=threading.Event()
original_fake_input=owner_module.xtest.fake_input
def expire_on_admitted_keypress(d,event_type,code=None,**kwargs):
    result=original_fake_input(d,event_type,code,**kwargs)
    if event_type==owner_module.X.KeyPress:
        backend.lease.deadline=time.perf_counter_ns()-1
        armed.set()
    return result
owner_module.xtest.fake_input=expire_on_admitted_keypress
events=[]
def emit(row):
    events.append(row)
    if row.get("event")=="input_admission": admitted.set()
    if row.get("event")=="terminal": terminal.set()
backend.emit=emit
orig_drain=backend._drain_owner_records
def observed_drain():
    orig_drain()
    drained.set()
backend._drain_owner_records=observed_drain
real_focus=h.d.get_input_focus
def barrier_focus():
    if armed.is_set() and not allow_focus.is_set():
        focus_blocked.set()
        if not allow_focus.wait(2):
            raise RuntimeError("focus barrier timeout")
    return real_focus()
h.d.get_input_focus=barrier_focus

import executor_v3
from lease import Expired
Executor=executor_v3.Executor
old_lease=executor_v3.Lease
class ObservedLease(old_lease):
    def __init__(self,deadline):
        super().__init__(deadline)
        self.expected_focus=42
        self.intent_token="intent-execute-exit-race"
executor_v3.Lease=ObservedLease
parent=bt.Backend.__bases__[0]
missing=object()
old_execute=parent.__dict__.get("execute",missing)
old_release=parent.__dict__.get("release_all",missing)
def expire_immediately(self,_step,_cancel,_identifier,_index):
    self.raw("F8",True)
    self.lease.check()
    raise AssertionError("lease should have expired after key admission")
def delayed_release_all(self):
    state=self.owner.call("input_state",self.lease)
    result["state_seen_by_release_all"]=state
    result["held_seen_by_release_all"]=sorted(self.held)
    result["owner_ops_before_release_all_state"]=list(owner_ops)
    return {"verified":state.get("owned_keycodes")==[] and state.get("owned_buttons")==[]}
parent.execute=expire_immediately
parent.release_all=delayed_release_all
backend.sequence=1
backend.validate=lambda _steps:None
owner_ops=[]
original_owner_call=h.owner.call
def traced_owner_call(op,*args,**kwargs):
    owner_ops.append(op)
    return original_owner_call(op,*args,**kwargs)
h.owner.call=traced_owner_call
executor=Executor(backend,emit)
result={}
try:
    executor.submit("execute-exit-race", [{"op":"hold"}],1,time.perf_counter_ns()+10_000_000_000)
    if not admitted.wait(1): raise RuntimeError("admission timeout")
    if not focus_blocked.wait(1): raise RuntimeError("owner did not reach controlled expiry/focus barrier")
    if not drained.wait(1): raise RuntimeError("bridge execute-finally drain did not complete")
    result["records_at_bridge_drain"]=len(h.owner.records)
    result["release_rows_at_bridge_drain"]=sum(len(r.get("per_key_release_measurements",[])) for r in h.owner.records if r.get("event")=="owner_release")
    result["bridge_held_at_drain"]=sorted(backend.held)
    allow_focus.set()
    if not terminal.wait(1): raise RuntimeError("executor terminal timeout")
    state=h.owner.call("input_state",backend.lease)
    result.update({
      "event_names":[r.get("event") for r in events],
      "terminal_event":next(r for r in events if r.get("event")=="terminal"),
      "release_rows_published":len([r for r in events if r.get("event")=="input_release_measurement"]),
      "terminal_status":next(r.get("status") for r in events if r.get("event")=="terminal"),
      "terminal_release_verified":next(r.get("release",{}).get("verified") for r in events if r.get("event")=="terminal"),
      "owner_cleanup_reasons":[r.get("reason") for r in h.owner.records if r.get("event")=="owner_release"],
      "owner_cleanup_release_rows":sum(len(r.get("per_key_release_measurements",[])) for r in h.owner.records if r.get("event")=="owner_release"),
      "owner_keys_after_terminal":state.get("owned_keycodes"),
      "state_after_terminal":state,
      "fake_physical_keys_after_terminal":sorted(h.d.physical),
      "bridge_held_after_terminal":sorted(backend.held),
      "cleanup_record_cursor":backend._owner_record_cursor,
    })
    print(json.dumps(result,indent=2))
finally:
    allow_focus.set()
    executor.close();h.close()
    if old_execute is missing: delattr(parent,"execute")
    else: parent.execute=old_execute
    if old_release is missing: delattr(parent,"release_all")
    else: parent.release_all=old_release
    executor_v3.Lease=old_lease
