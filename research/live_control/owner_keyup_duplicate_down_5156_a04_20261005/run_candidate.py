"""One fake-Xlib case for repeated DOWN on a key already held by the same lease."""
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
    def __init__(self):
        self.intent_token = "token-duplicate-down"
        self.deadline = time.monotonic_ns() + 20_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 9
        self.focus_invalid = False

    def check(self):
        if time.monotonic_ns() >= self.deadline:
            raise TimeoutError("lease expired")

    def interruption_snapshot(self):
        return None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_case():
    server = FakeServer()
    install(server)
    owner_mod = load("input_owner_v12_candidate.py", "input_owner_v12_candidate")
    wrapper_mod = load("input_transition_owner_v5_candidate.py", "input_transition_owner_v5_candidate")
    sys.modules["input_transition_owner_v3"] = wrapper_mod

    class Parent:
        def execute(self, action, cancel, identifier, index):
            for key, down in action["actions"]:
                self.raw(key, down)
            return "ok"

    parent_mod = type(sys)("doom_typed_coast_backend_v1")
    parent_mod.Backend, parent_mod.suite = Parent, object()
    sys.modules["doom_typed_coast_backend_v1"] = parent_mod
    backend_mod = load("doom_retained_input_backend_v5_candidate.py", "doom_retained_input_backend_v5_candidate")
    lease = Lease()
    owner = wrapper_mod.InputOwner("fake", _owner_cls=lambda display: owner_mod.InputOwner(display))
    backend = backend_mod.Backend.__new__(backend_mod.Backend)
    backend.owner, backend.lease, backend.held = owner, lease, set()
    backend._release_batch = threading.local()
    emitted = []
    backend.emit = emitted.append
    try:
        answer = backend.execute(
            {"actions": [("A", True), ("A", True), ("A", False)]},
            None, "trial-duplicate-down", 13,
        )
        if answer != "ok":
            raise AssertionError("unexpected backend result")
    finally:
        owner.close()
    return {
        "name": "duplicate_down", "step": 13,
        "identifier": "trial-duplicate-down",
        "intent_token": lease.intent_token, "owner_id": owner.owner_id,
        "events": emitted, "calls": server.calls,
        "sync_calls": server.sync_calls, "owner_records": owner.records,
        "final_down": sorted(server.down),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "owner-keyup-duplicate-down-result-v1",
        "cases": [], "runner_error": None,
    }
    try:
        result["cases"] = [run_case()]
    except BaseException:
        result["runner_error"] = traceback.format_exc()
    (OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"runner_error": result["runner_error"], "case_count": len(result["cases"])}))
    return 0 if result["runner_error"] is None and len(result["cases"]) == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
