"""One matched baseline/candidate fake-display timeout and late-drain pair."""
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

PKG = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frozen_probe_a01", PKG.parent / "probe.py")
a01 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = a01
assert spec.loader is not None
spec.loader.exec_module(a01)


def run_case(candidate):
    helper, loaded = a01.load_frozen_candidate()
    bridge_test, _hm, harness, _lease, _bridge_module, backend = loaded
    coast = a01.load_current_coast_backend()
    ComposedBackend = type("ComposedBackend", (type(backend), coast.Backend), {})
    backend.__class__ = ComposedBackend
    release_owner = next(cls for cls in ComposedBackend.__mro__ if "release_all" in cls.__dict__)
    assert release_owner.__module__ == "bridge_v2_candidate"

    prior_lease = a01.executor_v3.Lease

    class ObservedLease(prior_lease):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.expected_focus = 42
            self.intent_token = "intent-timeout-a03"

    a01.executor_v3.Lease = ObservedLease
    parent = bridge_test.Backend.__bases__[0]
    missing = object()
    prior_execute = parent.__dict__.get("execute", missing)
    sync_entered, sync_open = threading.Event(), threading.Event()
    barrier_entered, timeout_seen, terminal = threading.Event(), threading.Event(), threading.Event()
    output, timing = [], {}
    real_sync = harness.d.sync
    sync_count = 0

    def gated_sync():
        nonlocal sync_count
        sync_count += 1
        if sync_count == 2:
            sync_entered.set()
            if not sync_open.wait(8.0):
                raise TimeoutError("A03 sync gate watchdog")
        return real_sync()

    harness.d.sync = gated_sync
    original_release_all = backend.release_all

    def bounded_release_all():
        try:
            return original_release_all()
        except BaseException as exc:
            if "owner reply timed out; cleanup unverified" not in repr(exc):
                raise
            timing["timeout_return_ns"] = time.perf_counter_ns()
            timeout_seen.set()
            def open_late_gate():
                timing["sync_gate_open_ns"] = time.perf_counter_ns()
                sync_open.set()
            threading.Timer(1.75, open_late_gate).start()
            if candidate:
                wait_start = time.perf_counter_ns()
                timing["owner_stopped_within_bound"] = backend.owner.stopped.wait(1.5)
                timing["late_drain_wait_ns"] = time.perf_counter_ns() - wait_start
                if timing["owner_stopped_within_bound"]:
                    backend._drain_owner_records()
            raise

    backend.release_all = bounded_release_all
    real_owner_call = backend.owner.call

    def observed_owner_call(operation, *args, **kwargs):
        if operation == "release":
            timing["barrier_call_start_ns"] = time.perf_counter_ns()
            barrier_entered.set()
            try:
                return real_owner_call(operation, *args, **kwargs)
            finally:
                timing["barrier_call_end_ns"] = time.perf_counter_ns()
        return real_owner_call(operation, *args, **kwargs)

    backend.owner.call = observed_owner_call

    def emit(row):
        output.append(dict(row))
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
        raise a01.lease.Expired()

    parent.execute = expire_while_held
    backend.sequence = 1
    backend.validate = lambda _steps: None
    backend.emit = emit
    executor = a01.executor_v3.Executor(backend, emit)
    identity = "timeout-a03-candidate" if candidate else "timeout-a03-baseline"
    try:
        executor.submit(identity, [{"op": "hold"}], 1, time.perf_counter_ns() + 30_000_000)
        assert sync_entered.wait(1.0), "expiry cleanup did not enter fake sync gate"
        assert barrier_entered.wait(1.0), "ExecutorV3 did not invoke release barrier"
        assert timeout_seen.wait(3.0), "owner call did not time out"
        assert terminal.wait(2.0), "ExecutorV3 did not emit failed terminal"
        terms = [row for row in output if row.get("event") == "terminal"]
        assert len(terms) == 1
        term = terms[0]
        owner_stopped_after_terminal = backend.owner.stopped.wait(1.5)
        time.sleep(.02)
        ups = [row for row in output if row.get("event") == "input_release_measurement"]
        owner_releases = []
        for row in backend.owner.records:
            if row.get("event") != "owner_release":
                continue
            owner_releases.append({
                "reason": row.get("reason"),
                "verified": row.get("verified"),
                "keys_down": row.get("keys_down"),
                "buttons_down": row.get("buttons_down"),
                "per_key_classifications": [
                    item.get("physical_key_measurement", {}).get("classification")
                    for item in row.get("per_key_release_measurements", [])
                ],
            })
        events = [row.get("event") for row in output]
        terminal_index = events.index("terminal")
        return {
            "arm": "candidate" if candidate else "baseline",
            "timing": timing,
            "terminal": {"status": term["status"], "release_verified": term["release"].get("verified")},
            "bridge_events": events,
            "up_rows": ups,
            "owner_releases": owner_releases,
            "owner_stopped_after_terminal": owner_stopped_after_terminal,
            "physical_empty": harness.d.physical == set(),
            "bridge_held": sorted(backend.held),
            "event_after_terminal": any(event == "input_release_measurement" for event in events[terminal_index + 1:]),
        }
    finally:
        sync_open.set()
        executor.close()
        harness.close()
        if prior_execute is missing:
            delattr(parent, "execute")
        else:
            parent.execute = prior_execute
        a01.executor_v3.Lease = prior_lease


def main():
    result = {
        "schema": "v39-owner-timeout-post-bound-control-supplement-v1",
        "base_main": a01.LOCK["base_main"],
        "candidate_pr_7805_head": a01.LOCK["candidate_pr_7805_head"],
        "control": run_case(False),
        "candidate": json.loads((PKG / "results" / "a03_v3" / "RESULT.json").read_text(encoding="utf-8"))["candidate"],
        "scope": "matched fake-display owner-thread timeout pair with gate released 1.75 s after timeout; no real X11, OS input, game, model, useful feedback, recovery efficacy, or live MAP01 evidence",
    }
    out = PKG / "results" / "a03_control_supplement_v2"
    if out.exists():
        raise FileExistsError(f"A03 control supplement output path already exists: {out}")
    out.mkdir(parents=True)
    (out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()





