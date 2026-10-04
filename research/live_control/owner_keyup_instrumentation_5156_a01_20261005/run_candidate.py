"""Single deterministic fake-Xlib run. Writes RESULT.json even on failure."""
import importlib.util, json, os, sys, threading, time, traceback
from pathlib import Path
from fake_xlib import FakeServer, install

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ["OUT_DIR"])
sys.path.insert(0, str(HERE))
sys.modules["executor_v3"] = type(sys)("executor_v3")
sys.modules["executor_v3"].Cancelled = type("Cancelled", (Exception,), {})
sys.modules["executor_v3"].DecisionRequired = type("DecisionRequired", (Exception,), {})

class Lease:
    def __init__(self, token):
        self.intent_token = token
        self.deadline = time.monotonic_ns() + 20_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 9
        self.focus_invalid = False
    def check(self):
        if time.monotonic_ns() >= self.deadline: raise TimeoutError("lease expired")

def load_owner(server):
    install(server)
    spec = importlib.util.spec_from_file_location("input_owner_v11_candidate", HERE / "input_owner_v11_candidate.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return mod.InputOwner("fake")

def run_case(name, keys, *, cancel=False, bulk=False, fail_sync=False):
    server = FakeServer(); owner = load_owner(server); lease = Lease("token-" + name)
    try:
        for key in keys: owner.call("down", lease, key)
        if fail_sync:
            server.fail_sync_at = server.sync_calls + 1
            try: owner.call("release", lease)
            except RuntimeError: pass
            else: raise AssertionError("injected XSync failure did not propagate")
            # Clear failure so owner shutdown can perform a later neutral cleanup.
            server.fail_sync_at = None
        elif cancel:
            lease.cancel.set()
            deadline = time.monotonic() + 1
            while not any(r.get("event") == "owner_release" for r in owner.records) and time.monotonic() < deadline:
                time.sleep(.001)
            if not any(r.get("event") == "owner_release" for r in owner.records):
                raise AssertionError("cancellation cleanup not observed")
        elif bulk:
            owner.call("release", lease)
        else:
            wrapper_spec = importlib.util.spec_from_file_location("input_transition_owner_v4_candidate", HERE / "input_transition_owner_v4_candidate.py")
            wrapper_mod = importlib.util.module_from_spec(wrapper_spec); sys.modules[wrapper_spec.name] = wrapper_mod; wrapper_spec.loader.exec_module(wrapper_mod)
            wrapped = wrapper_mod.InputOwner("fake", _owner_cls=lambda name: owner)
            receipts = [wrapped.call("up", lease, key) for key in keys]
            owner.close()
            return {"name": name, "keys": keys, "calls": server.calls, "sync_calls": server.sync_calls,
                    "records": owner.records, "receipts": receipts, "final_down": sorted(server.down)}
        if not owner.closed: owner.close()
        return {"name": name, "keys": keys, "calls": server.calls, "sync_calls": server.sync_calls,
                "records": owner.records, "final_down": sorted(server.down)}
    except BaseException:
        try: owner.close()
        except BaseException: pass
        raise

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"schema": "owner-keyup-construction-result-v1", "cases": [], "runner_error": None}
    try:
        result["cases"] = [run_case("single", ["A"]), run_case("ordered_two", ["A", "B"]),
                           run_case("bulk", ["A", "B"], bulk=True),
                           run_case("cancel", ["A", "B"], cancel=True),
                           run_case("sync_error", ["A"], fail_sync=True)]
    except BaseException:
        result["runner_error"] = traceback.format_exc()
    (OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"runner_error": result["runner_error"], "case_count": len(result["cases"])}))
    return 0 if result["runner_error"] is None and len(result["cases"]) == 5 else 1

if __name__ == "__main__": raise SystemExit(main())
