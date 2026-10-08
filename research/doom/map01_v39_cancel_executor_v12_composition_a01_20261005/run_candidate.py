"""One-shot fake-display composition run; writes only the frozen output path."""
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results" / "formal_04" / "candidate.json"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite consumed output: {OUT}")

TEST = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("main_bridge_harness", TEST)
harness_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness_mod)

V13_PATH = HERE / "candidate_source/input_owner_v13_candidate.py"
v13_spec = importlib.util.spec_from_file_location("input_owner_v13_candidate", V13_PATH)
v13 = importlib.util.module_from_spec(v13_spec)
sys.modules[v13_spec.name] = v13
v13_spec.loader.exec_module(v13)
fixture_mod = harness_mod.load_v12_test_harness()
fixture_mod.owner_module = v13
harness = fixture_mod.Harness(v13)

sys.path.insert(0, str(ROOT / "research/live_control"))
from executor_v12 import Executor  # noqa: E402
import executor_v12 as executor_v12_module  # noqa: E402

bridge_path = HERE / "candidate_source/bridge_v2_candidate.py"
bridge_spec = importlib.util.spec_from_file_location("bridge_v2_candidate", bridge_path)
bridge = importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)
backend = object.__new__(bridge.Backend)
backend.owner = harness.owner
backend.lease = None
backend.held = set()
backend._input_event_context = ("v13-v12-a01", 0)
backend._owner_record_cursor = len(harness.owner.records)
backend.sequence = 1
backend.validate = lambda steps: None
events = []
backend.emit = events.append

entered = threading.Event()
def fake_execute(self, step, cancel, identifier, index):
    self.raw("F8", True)
    entered.set()
    while not cancel.wait(0.002):
        pass
    from executor_v3 import Cancelled
    raise Cancelled()

def fake_release_all(self):
    for key in tuple(self.held):
        self.raw(key, False)
    rec = self.owner.call("release", self.lease)
    self._drain_owner_records()
    state = self.owner.call("input_state", self.lease)
    return {"verified": rec.get("verified") is True and not state["owned_keycodes"] and not state["owned_buttons"],
            "keys_down": state["owned_keycodes"], "buttons_down": state["owned_buttons"]}

base = bridge.Backend.__bases__[0]
base.execute = fake_execute
base.release_all = fake_release_all
PreviousLease = executor_v12_module.Lease
class TestLease(PreviousLease):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_focus = 42
        self.intent_token = "intent-v13-v12-a01"
executor_v12_module.Lease = TestLease

try:
    executor = Executor(backend, events.append)
    executor.submit("v13-v12-a01", [{"op": "hold"}], 1, time.perf_counter_ns() + 10_000_000_000)
    if not entered.wait(2):
        raise RuntimeError("fake F8 down admission did not occur")
    if not executor.cancel("v13-v12-a01"):
        raise RuntimeError("cancel did not match admitted id")
    active = executor.active
    if active is not None:
        active[2].join(3)
    for watcher in executor.release_watchers:
        watcher.join(3)
    executor.close()
    result = {
        "schema": "map01-v39-cancel-executor-v12-composition-candidate-v1",
        "events": events,
        "owner_records": harness.owner.records,
        "fake_physical_keys": sorted(harness.d.physical),
        "backend_held": sorted(backend.held),
        "executor_active": executor.active is not None,
        "executor_release_errors": executor.release_publication_errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
finally:
    try:
        harness.close()
    finally:
        executor_v12_module.Lease = PreviousLease
        base.execute = lambda self, step, cancel, identifier, index: None
        base.release_all = lambda self: {"verified": True}
print(OUT)
