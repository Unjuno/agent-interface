"""One-shot fake-display expiry race through PR #7805 bridge + ExecutorV12."""
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

test_path = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("expiry_bridge_harness", test_path)
bridge_test = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge_test
spec.loader.exec_module(bridge_test)
fixture = bridge_test.load_v12_test_harness()
owner_path = ROOT / "research/doom/map01_v39_cancel_executor_v12_composition_a01_20261005/candidate_source/input_owner_v13_candidate.py"
owner_mod = fixture.load("input_owner_v13_candidate", owner_path)
fixture.owner_module = owner_mod
harness = fixture.Harness(owner_mod)

sys.path.insert(0, str(HERE / "candidate_source"))
bridge_path = HERE / "candidate_source/bridge_v2_candidate.py"
bridge_spec = importlib.util.spec_from_file_location("bridge_v2_candidate", bridge_path)
bridge_mod = importlib.util.module_from_spec(bridge_spec)
sys.modules[bridge_spec.name] = bridge_mod
bridge_spec.loader.exec_module(bridge_mod)

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
            raise TimeoutError("frozen cleanup sync gate timed out")
    return original_sync()
harness.d.sync = controlled_sync

placeholder = bridge_mod.Backend.__bases__[0].__bases__[0]
old_execute = placeholder.__dict__.get("execute")
old_release_all = placeholder.__dict__.get("release_all")
def expire_during_owner_cleanup(self, _step, lease, identifier, index):
    self._input_event_context = (identifier, index)
    self.raw("F8", True)
    if not cleanup_sync_entered.wait(2):
        raise RuntimeError("owner did not enter deadline cleanup")
    try:
        lease.check()
    except Expired:
        raise
    raise AssertionError("lease had not expired after owner expiry cleanup began")

def session_v5_release_all(self):
    # Exact operation order from pinned research/live_control/session_v5.py.
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
        self.intent_token = "intent-expiry-pending-a01"
executor_module.Lease = ObservedLease

executor = None
runner_error = None
try:
    executor = Executor(backend, events.append)
    deadline = time.perf_counter_ns() + 250_000_000
    executor.submit("expiry-pending-a01", [{"op": "hold"}], 1, deadline)
    if not cleanup_sync_entered.wait(3):
        raise RuntimeError("expiry cleanup sync was not reached")
    if not release_all_entered.wait(3):
        raise RuntimeError("ExecutorV12 did not reach release_all after execute exit")
    # At this exact boundary execute() has returned/raised and its one drain is done,
    # while owner release is still blocked before creating owner_release evidence.
    cursor_after_execute_drain = backend._owner_record_cursor
    owner_records_before_unblock = list(harness.owner.records)
    physical_state_while_sync_blocked = sorted(harness.d.physical)
    sync_gate.set()
    active = executor.active
    if active is not None:
        active[2].join(4)
    executor.close()
    terminal_rows = [row for row in events if row.get("event") == "terminal"]
    result = {
        "schema": "map01-v39-expiry-pending-cleanup-candidate-v1",
        "events": events,
        "owner_records_before_unblock": owner_records_before_unblock,
        "owner_records_after_unblock": harness.owner.records,
        "cursor_after_execute_drain": cursor_after_execute_drain,
        "physical_state_while_sync_blocked": physical_state_while_sync_blocked,
        "fake_physical_keys_after_terminal": sorted(harness.d.physical),
        "bridge_held_after_terminal": sorted(backend.held),
        "executor_active_after_terminal": executor.active is not None,
        "terminal_count": len(terminal_rows),
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
    result = {"schema": "map01-v39-expiry-pending-cleanup-candidate-v1",
              "runner_error": runner_error, "events": events}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT)
