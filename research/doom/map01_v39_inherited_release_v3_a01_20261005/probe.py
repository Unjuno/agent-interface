"""One paired fake-display composition probe for the current V39 release chain."""
import importlib.util
import hashlib
import json
import sys
import threading
import time
import types
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[2]
LIVE = PKG / "source_snapshot" / "live_control"
CANDIDATE_BASELINE = PKG / "candidate_snapshot" / "baseline"
CANDIDATE_A08 = PKG / "candidate_snapshot" / "a08"
sys.path.insert(0, str(LIVE))
sys.path.insert(0, str(ROOT))

LOCK = json.loads((PKG / "SOURCE_LOCK.json").read_text())
for locked in LOCK["files"]:
    if not locked.get("runtime_dependency"):
        continue
    actual = hashlib.sha256((ROOT / locked["repo_path"]).read_bytes()).hexdigest()
    assert actual == locked["sha256"], f"runtime dependency drift: {locked['repo_path']}"

# Pin ExecutorV3 and Lease imports to the captured current-main source before
# the legacy fake-display fixture adds its older dependency paths.
import executor_v3
import lease

sys.path.insert(0, str(ROOT / "research" / "live_control"))


def load_frozen_candidate(candidate_dir):
    helper_path = candidate_dir / "test_cancel_release.py"
    spec = importlib.util.spec_from_file_location("frozen_cancel_release_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    assert spec.loader is not None
    spec.loader.exec_module(helper)
    helper.FIX_PATH = candidate_dir
    helper.BRIDGE_TEST_PATH = ROOT / "research" / "doom" / "map01_v39_perkey_bridge_a01" / "test_bridge.py"
    helper.OWNER_V13_PATH = candidate_dir / "input_owner_v13_candidate.py"
    helper.BRIDGE_V2_PATH = candidate_dir / "bridge_v2_candidate.py"
    return helper.load_candidate()


def load_current_coast_backend():
    # The fake-display fixture stubs the GUI libraries. The current V39 class
    # chain is imported from frozen source; its capture/session base is inert.
    pil = sys.modules["PIL"]
    pil.Image = types.SimpleNamespace(frombytes=lambda *args, **kwargs: None)
    sys.modules["PIL.Image"] = pil.Image
    session_v4 = types.ModuleType("session_v4")
    session_v4.Backend = type("SessionBase", (), {})
    session_v4.suite = object()
    session_v4.Encoder = session_v4.Decoder = session_v4.Frame = session_v4.ImageArtifactSink = object
    sys.modules["session_v4"] = session_v4
    # These owner implementations are not constructed in this no-display
    # composition; the bridge's fake owner is supplied by the retained harness.
    for name in ("input_owner", "input_owner_v2", "input_owner_v5"):
        sys.modules[name] = types.SimpleNamespace(InputOwner=object)
    sys.modules["quiet_window"] = types.SimpleNamespace(QuietWindow=object)
    spec = importlib.util.spec_from_file_location("coast_backend_v1", LIVE / "coast_backend_v1.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_case(candidate_fix):
    candidate_dir = CANDIDATE_A08 if candidate_fix else CANDIDATE_BASELINE
    bridge_test, _hm, harness, _lease, _bridge_module, backend = load_frozen_candidate(candidate_dir)
    coast = load_current_coast_backend()
    candidate_backend = type(backend)
    ComposedBackend = type("ComposedBackend", (candidate_backend, coast.Backend), {})
    backend.__class__ = ComposedBackend
    release_owner = next(cls for cls in ComposedBackend.__mro__
                         if "release_all" in cls.__dict__)
    inherited_owner = (next(cls for cls in ComposedBackend.__mro__[ComposedBackend.__mro__.index(release_owner) + 1:]
                            if "release_all" in cls.__dict__)
                       if candidate_fix else release_owner)
    assert inherited_owner.__module__ == "session_v5"
    assert inherited_owner.__name__ == "Backend"
    assert (release_owner.__module__ == "bridge_v2_candidate") == candidate_fix

    prior_lease = executor_v3.Lease

    class ObservedLease(prior_lease):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.expected_focus = 42
            self.intent_token = "intent-v13-v3-inherited-a01"

    executor_v3.Lease = ObservedLease
    parent = bridge_test.Backend.__bases__[0]
    missing = object()
    prior_execute = parent.__dict__.get("execute", missing)
    events = []
    admitted = threading.Event()
    cleanup_sync_entered = threading.Event()
    cleanup_sync_continue = threading.Event()
    release_barrier_called = threading.Event()
    terminal = threading.Event()

    real_sync = harness.d.sync
    sync_count = 0

    def gated_sync():
        nonlocal sync_count
        sync_count += 1
        if sync_count == 2:  # after fake KeyRelease, before owner receipt append
            cleanup_sync_entered.set()
            if not cleanup_sync_continue.wait(2.0):
                raise TimeoutError("test did not release expiry cleanup sync gate")
        return real_sync()

    harness.d.sync = gated_sync
    real_owner_call = backend.owner.call

    def observed_owner_call(operation, *args, **kwargs):
        if operation == "release":
            release_barrier_called.set()
        return real_owner_call(operation, *args, **kwargs)

    backend.owner.call = observed_owner_call

    def emit(row):
        events.append(row)
        if row.get("event") == "input_admission":
            admitted.set()
        if row.get("event") == "terminal":
            terminal.set()

    def expire_while_held(self, _step, _cancel, _identifier, _index):
        self.raw("F8", True)
        cutoff = time.monotonic() + 1.5
        while time.perf_counter_ns() < self.lease.deadline + 2_000_000:
            if time.monotonic() >= cutoff:
                raise TimeoutError("lease did not expire")
            time.sleep(0.001)
        raise lease.Expired()

    parent.execute = expire_while_held
    backend.sequence = 1
    backend.validate = lambda _steps: None
    backend.emit = emit
    executor = executor_v3.Executor(backend, emit)
    identity = "v13-v3-a08-candidate-a01" if candidate_fix else "v13-v3-inherited-only-a01"
    try:
        deadline = time.perf_counter_ns() + 30_000_000
        executor.submit(identity, [{"op": "hold"}], 1, deadline)
        assert admitted.wait(1.0), "admission did not occur"
        assert cleanup_sync_entered.wait(1.0), "expiry cleanup did not reach sync gate"
        assert release_barrier_called.wait(1.0), "ExecutorV3 final release barrier did not start"
        # The execute() final drain has already run while the owner record is
        # pending. Release the owner only after the inherited barrier queues.
        cleanup_sync_continue.set()
        assert terminal.wait(1.5), "terminal did not arrive"
        ups = [e for e in events if e.get("event") == "input_release_measurement"]
        downs = [e for e in events if e.get("event") == "input_admission"]
        terms = [e for e in events if e.get("event") == "terminal"]
        owner_releases = [r for r in backend.owner.records if r.get("event") == "owner_release"]
        assert len(terms) == 1 and terms[0]["status"] == "expired", terms
        assert terms[0]["release"].get("verified") is True, terms
        assert len(ups) == (1 if candidate_fix else 0), ups
        if candidate_fix:
            assert ups[0]["physical_key_measurement"]["classification"] == "CONFIRMED_PHYSICAL_UP"
            assert (ups[0]["id"], ups[0]["step"]) == (identity, 0)
            assert ups[0]["intent_token"] == "intent-v13-v3-inherited-a01"
            assert ups[0]["physical_key_measurement"]["actuation_id"] == downs[0]["physical_key_measurement"]["actuation_id"]
            names = [e.get("event") for e in events]
            assert names.index("input_release_measurement") < names.index("terminal"), names
        physical_empty = harness.d.physical == set()
        ledger_empty = backend.held == set()
        assert physical_empty and ledger_empty, (harness.d.physical, backend.held)
        return {
            "case": identity,
            "candidate_final_drain_implementation": candidate_fix,
            "release_method_owner": release_owner.__module__ + "." + release_owner.__name__,
            "inherited_release_method_owner": inherited_owner.__module__ + "." + inherited_owner.__name__,
            "terminal_status": terms[0]["status"],
            "terminal_release_verified": terms[0]["release"]["verified"],
            "contextual_up_receipt_count": len(ups),
            "owner_release_record_count": len(owner_releases),
            "owner_release_reasons": [r.get("reason") for r in owner_releases],
            "event_order": [e.get("event") for e in events],
            "physical_state_empty": physical_empty,
            "bridge_ledger_empty": ledger_empty,
        }
    finally:
        cleanup_sync_continue.set()
        executor.close()
        harness.close()
        if prior_execute is missing:
            delattr(parent, "execute")
        else:
            parent.execute = prior_execute
        executor_v3.Lease = prior_lease


def main():
    control = run_case(False)
    candidate = run_case(True)
    result = {
        "result": "PASS_SCOPED_FINAL_DRAIN" if candidate["contextual_up_receipt_count"] == 1 else "FAIL",
        "base_main_sha": LOCK["base_main_sha"],
        "candidate_commits": LOCK["candidate_commits"],
        "control": control,
        "candidate": candidate,
        "scope": "paired fake-display forced schedule; current-main V39 coast Backend in MRO; baseline inherits frozen session_v5.release_all; A08 candidate bridge delegates to that method and drains pending owner records in finally; test execute seam; no real X11, OS input, game, application effect, or live allocation",
    }
    (PKG / "results" / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS_SCOPED_FINAL_DRAIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
