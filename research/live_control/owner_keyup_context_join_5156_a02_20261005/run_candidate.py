"""One fake-Xlib composition run through current-main retained backend v4."""
import importlib.util, json, os, sys, threading, time, traceback
from pathlib import Path
from fake_xlib import FakeServer, install

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ["OUT_DIR"])
sys.path.insert(0, str(HERE))
executor = type(sys)("executor_v3")
executor.Cancelled = type("Cancelled", (Exception,), {})
executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
sys.modules["executor_v3"] = executor

class Lease:
    def __init__(self, token):
        self.intent_token = token
        self.deadline = time.monotonic_ns() + 20_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 9
        self.focus_invalid = False
    def check(self):
        if time.monotonic_ns() >= self.deadline: raise TimeoutError("lease expired")
    def interruption_snapshot(self): return None

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod

def run_case(name, actions, step):
    server = FakeServer(); install(server)
    owner_mod = load("input_owner_v11_candidate.py", "input_owner_v11_candidate")
    wrapper_mod = load("input_transition_owner_v4_candidate.py", "input_transition_owner_v4_candidate")
    sys.modules["input_transition_owner_v3"] = wrapper_mod
    class Parent:
        def execute(self, action, cancel, identifier, index):
            for key, down in action["actions"]: self.raw(key, down)
            return "ok"
    parent_mod = type(sys)("doom_typed_coast_backend_v1")
    parent_mod.Backend, parent_mod.suite = Parent, object()
    sys.modules["doom_typed_coast_backend_v1"] = parent_mod
    backend_mod = load("doom_retained_input_backend_v4_frozen.py", "doom_retained_input_backend_v4_frozen")
    lease = Lease("token-" + name)
    owner = wrapper_mod.InputOwner("fake", _owner_cls=lambda display: owner_mod.InputOwner(display))
    backend = backend_mod.Backend.__new__(backend_mod.Backend)
    backend.owner, backend.lease, backend.held = owner, lease, set()
    backend._release_batch = threading.local()
    emitted = []; backend.emit = emitted.append
    answer = backend.execute({"actions": actions}, None, "trial-" + name, step)
    if answer != "ok": raise AssertionError("unexpected backend result")
    owner.close()
    return {"name": name, "step": step, "identifier": "trial-" + name,
            "intent_token": lease.intent_token, "owner_id": owner.owner_id,
            "events": emitted, "calls": server.calls, "sync_calls": server.sync_calls,
            "owner_records": owner.records, "final_down": sorted(server.down)}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"schema":"owner-keyup-context-join-result-v1", "cases":[], "runner_error":None}
    try:
        result["cases"] = [
            run_case("single", [("A",True),("A",False)], 3),
            run_case("reverse", [("A",True),("B",True),("B",False),("A",False)], 7),
            run_case("cycles", [("C",True),("C",False),("C",True),("C",False)], 11),
        ]
    except BaseException:
        result["runner_error"] = traceback.format_exc()
    (OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"runner_error":result["runner_error"],"case_count":len(result["cases"])}))
    return 0 if result["runner_error"] is None and len(result["cases"]) == 3 else 1

if __name__ == "__main__": raise SystemExit(main())
