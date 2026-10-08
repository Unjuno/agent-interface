"""One paired-source V39 × ExecutorV3 owner-timeout schedule."""
import hashlib
import importlib.util
import json
import sys
import threading
import time
import types
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[2]
LIVE = PKG / "source_snapshot" / "live_control"
CANDIDATE = PKG / "candidate_snapshot" / "a08"
sys.path.insert(0, str(LIVE))
sys.path.insert(0, str(ROOT))

LOCK = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
for row in LOCK["locked_files"]:
    path = PKG / row["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], row["path"]

import executor_v3
import lease
sys.path.insert(0, str(ROOT / "research" / "live_control"))


def load_frozen_candidate():
    helper_path = CANDIDATE / "test_cancel_release.py"
    spec = importlib.util.spec_from_file_location("frozen_cancel_release_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    assert spec.loader is not None
    spec.loader.exec_module(helper)
    helper.FIX_PATH = CANDIDATE
    helper.BRIDGE_TEST_PATH = PKG / "source_snapshot" / "repository" / "research" / "doom" / "map01_v39_perkey_bridge_a01" / "test_bridge.py"
    helper.OWNER_V13_PATH = CANDIDATE / "input_owner_v13_candidate.py"
    helper.BRIDGE_V2_PATH = CANDIDATE / "bridge_v2_candidate.py"
    return helper, helper.load_candidate()


def load_current_coast_backend():
    pil = sys.modules["PIL"]
    pil.Image = types.SimpleNamespace(frombytes=lambda *args, **kwargs: None)
    sys.modules["PIL.Image"] = pil.Image
    session_v4 = types.ModuleType("session_v4")
    session_v4.Backend = type("SessionBase", (), {})
    session_v4.suite = object()
    session_v4.Encoder = session_v4.Decoder = session_v4.Frame = session_v4.ImageArtifactSink = object
    sys.modules["session_v4"] = session_v4
    for name in ("input_owner", "input_owner_v2", "input_owner_v5"):
        sys.modules[name] = types.SimpleNamespace(InputOwner=object)
    sys.modules["quiet_window"] = types.SimpleNamespace(QuietWindow=object)
    spec = importlib.util.spec_from_file_location("coast_backend_v1", LIVE / "coast_backend_v1.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_once():
    helper, loaded = load_frozen_candidate()
    bridge_test, _hm, harness, _lease, _bridge_module, backend = loaded
    coast = load_current_coast_backend()
    ComposedBackend = type("ComposedBackend", (type(backend), coast.Backend), {})
    backend.__class__ = ComposedBackend
    release_owner = next(cls for cls in ComposedBackend.__mro__ if "release_all" in cls.__dict__)
    assert release_owner.__module__ == "bridge_v2_candidate"
    prior_lease = executor_v3.Lease

    class ObservedLease(prior_lease):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.expected_focus = 42
            self.intent_token = "intent-timeout-a01"

    executor_v3.Lease = ObservedLease

    parent = bridge_test.Backend.__bases__[0]
    missing = object()
    prior_execute = parent.__dict__.get("execute", missing)
    sync_entered, sync_open = threading.Event(), threading.Event()
    barrier_entered, barrier_returned, terminal = threading.Event(), threading.Event(), threading.Event()
    output, timing = [], {}
    real_sync = harness.d.sync
    sync_count = 0

    def gated_sync():
        nonlocal sync_count
        sync_count += 1
        if sync_count == 2:
            sync_entered.set()
            if not sync_open.wait(8.0):
                raise TimeoutError("frozen sync gate watchdog")
        return real_sync()

    harness.d.sync = gated_sync
    real_owner_call = backend.owner.call

    def observed_call(operation, *args, **kwargs):
        if operation == "release":
            timing["call_start_ns"] = time.perf_counter_ns()
            barrier_entered.set()
            try:
                return real_owner_call(operation, *args, **kwargs)
            except BaseException as exc:
                timing["call_error"] = repr(exc)
                raise
            finally:
                timing["call_end_ns"] = time.perf_counter_ns()
                barrier_returned.set()
        return real_owner_call(operation, *args, **kwargs)

    backend.owner.call = observed_call

    def emit(row):
        output.append(row)
        if row.get("event") == "terminal":
            terminal.set()

    def expire_while_held(self, _step, _cancel, identifier, index):
        self._input_event_context = (identifier, index)
        self.raw("F8", True)
        cutoff = time.monotonic() + 1.0
        while time.perf_counter_ns() < self.lease.deadline + 2_000_000:
            if time.monotonic() >= cutoff:
                raise TimeoutError("lease did not expire")
            time.sleep(.001)
        raise lease.Expired()

    parent.execute = expire_while_held
    backend.sequence = 1
    backend.validate = lambda _steps: None
    backend.emit = emit
    executor = executor_v3.Executor(backend, emit)
    try:
        executor.submit("timeout-a01", [{"op": "hold"}], 1, time.perf_counter_ns() + 30_000_000)
        assert sync_entered.wait(1.0), "expiry cleanup did not enter the frozen sync gate"
        assert barrier_entered.wait(1.0), "ExecutorV3 did not invoke the release barrier"
        assert barrier_returned.wait(3.0), "owner reply did not respect its declared bound"
        assert terminal.wait(1.0), "ExecutorV3 did not emit a terminal after release-barrier failure"
        timing["barrier_elapsed_ns"] = timing["call_end_ns"] - timing["call_start_ns"]
        term = next(row for row in output if row.get("event") == "terminal")
        at_terminal = {
            "terminal_status": term["status"],
            "release_verified": term["release"].get("verified"),
            "bridge_held": sorted(backend.held),
            "owner_release_records": len([r for r in backend.owner.records if r.get("event") == "owner_release"]),
            "physical": sorted(harness.d.physical),
            "up_receipts": len([r for r in output if r.get("event") == "input_release_measurement"]),
        }
        sync_open.set()
        if not backend.owner.stopped.wait(1.5):
            raise AssertionError("owner did not stop after its bounded request timeout")
        time.sleep(.02)
        after_owner_stop = {
            "bridge_held": sorted(backend.held),
            "owner_release_records": len([r for r in backend.owner.records if r.get("event") == "owner_release"]),
            "physical": sorted(harness.d.physical),
            "up_receipts": len([r for r in output if r.get("event") == "input_release_measurement"]),
            "owner_stopped": backend.owner.stopped.is_set(),
        }
        return {"timing": timing, "at_terminal": at_terminal, "after_owner_stop": after_owner_stop,
                "events": [r.get("event") for r in output],
                "scope": "one frozen fake-display owner-thread timeout schedule; no real X11, OS input, game, model, useful-feedback, recovery-efficacy, or live MAP01 evidence"}
    finally:
        sync_open.set()
        executor.close()
        harness.close()
        if prior_execute is missing:
            delattr(parent, "execute")
        else:
            parent.execute = prior_execute
        executor_v3.Lease = prior_lease


if __name__ == "__main__":
    result = run_once()
    (PKG / "results").mkdir(exist_ok=True)
    (PKG / "results" / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
