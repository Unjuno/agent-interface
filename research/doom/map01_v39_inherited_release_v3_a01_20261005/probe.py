"""One paired fake-display composition probe for the current V39 release chain."""
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
sys.path.insert(0, str(LIVE))
sys.path.insert(0, str(ROOT))

# Pin ExecutorV3 and Lease imports to the captured current-main source before
# the legacy fake-display fixture adds its older dependency paths.
import executor_v3
import lease

sys.path.insert(0, str(ROOT / "research" / "live_control"))
from research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release import load_candidate


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


def run_case(final_drain):
    bridge_test, _hm, harness, _lease, _bridge_module, backend = load_candidate()
    coast = load_current_coast_backend()
    candidate_backend = type(backend)
    if final_drain:
        class ComposedBackend(candidate_backend, coast.Backend):
            def release_all(self):
                try:
                    return super().release_all()
                finally:
                    self._drain_owner_records()
    else:
        class ComposedBackend(candidate_backend, coast.Backend):
            pass
    backend.__class__ = ComposedBackend
    release_owner = next(cls for cls in ComposedBackend.__mro__
                         if "release_all" in cls.__dict__)
    if final_drain:
        assert release_owner is ComposedBackend
        inherited_owner = next(cls for cls in ComposedBackend.__mro__[1:]
                               if "release_all" in cls.__dict__)
    else:
        inherited_owner = release_owner
    assert inherited_owner.__module__ == "session_v5"
    assert inherited_owner.__name__ == "Backend"

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
    identity = "v13-v3-final-drain-a01" if final_drain else "v13-v3-inherited-only-a01"
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
        assert len(ups) == (1 if final_drain else 0), ups
        if final_drain:
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
            "final_drain_wrapper": final_drain,
            "release_method_owner": inherited_owner.__module__ + "." + inherited_owner.__name__,
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
        "base_main_sha": json.loads((PKG / "SOURCE_LOCK.json").read_text())["base_main_sha"],
        "control": control,
        "candidate": candidate,
        "scope": "paired fake-display forced schedule; current-main V39 coast Backend in MRO; release_all delegates to frozen session_v5.Backend; candidate wrapper drains pending owner records in finally; no real X11, OS input, game, application effect, or live allocation",
    }
    (PKG / "results" / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS_SCOPED_FINAL_DRAIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
