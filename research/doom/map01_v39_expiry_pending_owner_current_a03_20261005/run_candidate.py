"""One-shot current-PR-owner probe for expiry cleanup pending past execute exit."""
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results/formal_01/candidate.json"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite frozen output: {OUT}")

test = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("expiry_owner_a03_harness", test)
harness_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness_mod
spec.loader.exec_module(harness_mod)
fixture = harness_mod.load_v12_test_harness()
owner_path = HERE / "candidate_source/input_owner_v13_candidate.py"
sys.path.insert(0, str(owner_path.parent))
owner_mod = fixture.load("input_owner_v13_candidate", owner_path)
fixture.owner_module = owner_mod
harness = fixture.Harness(owner_mod)

sys.path.insert(0, str(HERE / "candidate_source"))
for name in ("bridge_v2_candidate", "bridge_v3_probe"):
    path = HERE / "candidate_source" / f"{name}.py"
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
bridge_mod = sys.modules["bridge_v3_probe"]

sys.path.insert(0, str(ROOT / "research/live_control"))
from executor_v12 import Executor  # noqa: E402
import executor_v12 as executor_module  # noqa: E402
from lease import Expired  # noqa: E402

backend = object.__new__(bridge_mod.Backend)
backend.owner = harness.owner
backend.lease = None
backend.held = set()
backend._input_event_context = None
backend._owner_record_cursor = len(harness.owner.records)
backend.sequence = 1
backend.validate = lambda steps: None
events = []
backend.emit = events.append

cleanup_sync_entered = threading.Event()
sync_gate = threading.Event()
release_all_entered = threading.Event()
original_sync = harness.d.sync
sync_count = 0
def controlled_sync():
    global sync_count
    sync_count += 1
    if sync_count == 2:
        cleanup_sync_entered.set()
        if not sync_gate.wait(3):
            raise TimeoutError("A03 frozen cleanup sync gate timed out")
    return original_sync()
harness.d.sync = controlled_sync

placeholder = bridge_mod.Backend.__bases__[0].__bases__[0]
old_execute = placeholder.__dict__.get("execute")
old_release_all = placeholder.__dict__.get("release_all")
def expire_during_owner_cleanup(self, _step, lease, identifier, index):
    self._input_event_context = (identifier, index)
    self.raw("F8", True)
    if not cleanup_sync_entered.wait(2):
        raise RuntimeError("current owner did not enter expiry cleanup")
    try:
        lease.check()
    except Expired:
        raise
    raise AssertionError("lease had not expired at the cleanup gate")

def session_v5_release_all(self):
    release_all_entered.set()
    result = self.owner.call("release", getattr(self, "lease", None))
    self.held.clear()
    return result

placeholder.execute = expire_during_owner_cleanup
placeholder.release_all = session_v5_release_all
old_lease = executor_module.Lease
class ObservedLease(old_lease):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_focus = 42
        self.intent_token = "intent-expiry-pending-a03"
executor_module.Lease = ObservedLease

executor = None
runner_error = None
try:
    executor = Executor(backend, events.append)
    deadline = time.perf_counter_ns() + 250_000_000
    executor.submit("expiry-pending-owner-a03", [{"op": "hold"}], 1, deadline)
    if not cleanup_sync_entered.wait(3):
        raise RuntimeError("expiry cleanup did not reach frozen sync gate")
    if not release_all_entered.wait(3):
        raise RuntimeError("ExecutorV12 did not reach release_all after execute exit")
    cursor_after_execute_drain = backend._owner_record_cursor
    owner_records_before_unblock = list(harness.owner.records)
    physical_state_while_sync_blocked = sorted(harness.d.physical)
    sync_gate.set()
    active = executor.active
    if active is not None:
        active[2].join(4)
    executor.close()
    result = {
        "schema": "map01-v39-expiry-pending-current-owner-a03-v1",
        "events": events,
        "owner_records_before_unblock": owner_records_before_unblock,
        "owner_records_after_unblock": harness.owner.records,
        "cursor_after_execute_drain": cursor_after_execute_drain,
        "physical_state_while_sync_blocked": physical_state_while_sync_blocked,
        "fake_physical_keys_after_terminal": sorted(harness.d.physical),
        "bridge_held_after_terminal": sorted(backend.held),
        "executor_active_after_terminal": executor.active is not None,
        "terminal_count": sum(row.get("event") == "terminal" for row in events),
    }
except BaseException as exc:
    runner_error = {"type": type(exc).__name__, "message": str(exc)}
    sync_gate.set()
finally:
    sync_gate.set()
    if executor is not None:
        try:
            executor.close()
        except Exception:
            pass
    try:
        harness.close()
    except Exception:
        pass
    executor_module.Lease = old_lease
    if old_execute is None:
        delattr(placeholder, "execute")
    else:
        placeholder.execute = old_execute
    if old_release_all is None:
        delattr(placeholder, "release_all")
    else:
        placeholder.release_all = old_release_all

if runner_error is not None:
    result = {"schema": "map01-v39-expiry-pending-current-owner-a03-v1",
              "runner_error": runner_error, "events": events}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT)
