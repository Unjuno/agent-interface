"""Invoke the frozen v6 _run_arm with a mock session and exact executor/lease."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import queue
import subprocess
import sys
import tempfile
import threading
import time
import types

BASE = "2240189b46c5f393bb7b1d5080e8eace748b0251"
ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent
SOURCES = {
    "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
    "executor": "research/live_control/executor_v10.py",
    "lease": "research/live_control/lease.py",
}


def frozen(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def source_manifest():
    out = {}
    for name, path in SOURCES.items():
        raw = frozen(path)
        compile(raw, path, "exec")
        out[name] = {
            "path": path,
            "git_blob": subprocess.check_output(
                ["git", "rev-parse", f"{BASE}:{path}"], cwd=ROOT, text=True
            ).strip(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    return out


def load_executor():
    lease_mod = types.ModuleType("lease")
    lease_mod.__file__ = "frozen-git-object:research/live_control/lease.py"
    exec(compile(frozen(SOURCES["lease"]), lease_mod.__file__, "exec"), lease_mod.__dict__)
    sys.modules["lease"] = lease_mod
    exec_mod = types.ModuleType("frozen_executor_v10")
    exec_mod.__file__ = "frozen-git-object:research/live_control/executor_v10.py"
    exec(compile(frozen(SOURCES["executor"]), exec_mod.__file__, "exec"), exec_mod.__dict__)
    return exec_mod.Executor


class CooperativeBackend:
    def __init__(self, sequence=7):
        self.sequence = sequence
        self.lease = None
        self.current_id = None
        self.cancel_observed_ns = {}
        self.releases = []

    def validate(self, steps):
        if not isinstance(steps, list) or not steps:
            raise ValueError("fake runner received an empty program")

    def execute(self, step, cancel, identifier, index):
        self.current_id = identifier
        if identifier.endswith("-prelude"):
            return
        while True:
            if cancel.is_set():
                self.cancel_observed_ns[identifier] = time.perf_counter_ns()
                return
            if cancel.wait(0.002):
                self.cancel_observed_ns[identifier] = time.perf_counter_ns()
                return

    def release_all(self):
        self.releases.append({"id": self.current_id, "release_ns": time.perf_counter_ns(), "verified": True})
        return {"verified": True}


class FakeProcess:
    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0


class FakeSession:
    def __init__(self, case, executor_class):
        self.case = case
        self.queue = queue.Queue()
        self._pending = collections.deque()
        self.events = []
        self.latest_exact = {"event": "observation", "sequence": 7,
                             "capture_ns": time.perf_counter_ns() - 5_000_000, "exact": True}
        self.backend = CooperativeBackend()
        self.executor_class = executor_class
        self.executor = None
        self.process = FakeProcess()
        self.clock_calls = 0
        self.planner_start_ns = None
        self.timer_started_ns = None
        self.timer_expired_ns = None
        self.clock_return_ns = None
        self.cancel_delay_ms = case["clock_delay_ms"]
        self._put({"event": "ready", "presentation": "full"})
        self._put(dict(self.latest_exact))

    def _put(self, row):
        self.queue.put(dict(row))

    def emit_executor_event(self, row):
        # The mock session models the existing runtime's distinct release receipt
        # from the exact executor's verified terminal release object.
        if row.get("event") == "terminal" and row.get("release", {}).get("verified") is True:
            self._put({"event": "input_released", "id": row.get("id"),
                       "verified": True, "release_ns": self.backend.releases[-1]["release_ns"]})
            self.events.append(dict(self.queue.queue[-1]))
        self.events.append(dict(row))
        self._put(row)

    def wait(self, predicate, timeout=20.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for _ in range(len(self._pending)):
                row = self._pending.popleft()
                if predicate(row):
                    return row
                self._pending.append(row)
            try:
                row = self.queue.get(timeout=min(0.05, max(0.005, deadline - time.monotonic())))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError("mock process unexpectedly exited")
                continue
            if predicate(row):
                return row
            self._pending.append(row)
        raise TimeoutError("fake session event timeout")

    def runtime_clock(self):
        self.clock_calls += 1
        if self.clock_calls == 2:
            self.planner_start_ns = time.perf_counter_ns()
        elif self.clock_calls == 3:
            # Simulate only the synchronous reply delay; the frozen v6 caller
            # itself performs this runtime_clock call after the timer fires.
            time.sleep(self.cancel_delay_ms / 1000)
            self.clock_return_ns = time.perf_counter_ns()
        return time.perf_counter_ns()

    def send(self, command):
        if command["op"] == "cancel":
            self.executor.cancel(command["id"])
        elif command["op"] == "finish":
            self._put({"event": "post_control_score", "score": {"mock": True}})
        else:
            raise ValueError(f"unexpected session command: {command}")

    def terminate(self):
        if self.executor is not None:
            self.executor.close()


class ObservedTimer(threading.Timer):
    def __init__(self, interval, function, case):
        self.case = case

        def fire():
            self.case["timer_expired_ns"] = time.perf_counter_ns()
            function()

        super().__init__(interval, fire)

    def start(self):
        self.case["timer_started_ns"] = time.perf_counter_ns()
        super().start()


def make_base(case, executor_class):
    base = types.SimpleNamespace()
    base.ALLOCATION_ID = "offline-runner-mock"
    base.EXPECTED_WORKFLOW_PATH = "offline"
    base.PLANNER_WAIT_MS = case["planner_wait_ms"]
    base.PRELUDE_KEYS = ("forward",)
    base.PRELUDE_MS = 5
    base.SessionError = RuntimeError
    base.JsonSession = lambda command: FakeSession(case, executor_class)
    base._session_command = lambda runtime, fixture: {"runtime": runtime, "fixture": fixture}
    base._submit = lambda session, identifier, steps, valid_until_ns: submit(session, identifier, steps, valid_until_ns, executor_class)
    base._wait_exact_after = lambda session, sequence: {**session.latest_exact, "sequence": sequence + 1,
                                                        "capture_ns": time.perf_counter_ns()}
    base._source_guard = lambda session: (dict(session.latest_exact, sequence=session.latest_exact["sequence"] + 1),
                                          {"frame_rgb_sha256": "synthetic-frame"}, {"health": 100})
    base.recovery_valid_until_ns = lambda capture_ns, planner_start_ns: (
        planner_start_ns + case["lease_ms"] * 1_000_000)
    base.build_coast_steps = lambda: [{"op": "coast"}]
    base.build_recovery_steps = lambda: [{"op": "hold", "keys": ["forward"], "duration_ms": 5000}]
    base.recovery_guard_failed = lambda *args: (False, None)

    class Window:
        def __init__(self, start_ns, end_ns):
            self.start_ns, self.end_ns = start_ns, end_ns
            self.duration_ns = end_ns - start_ns

    base.Window = Window
    base.fallback_input_bounds = lambda events, identifier, window: {"event_count": len(events),
                                                                       "window_duration_ns": window.duration_ns}
    base.terminal_release_ok = lambda events, identifier: any(
        e.get("event") == "input_released" and e.get("id") == identifier and e.get("verified") is True
        for e in events)
    base.load_json = lambda path: {"mock": True, "path": path.name}
    return base


def submit(session, identifier, steps, valid_until_ns, executor_class):
    if identifier.endswith("-prelude"):
        executor = executor_class(session.backend, session.emit_executor_event)
        executor.submit(identifier, steps, session.backend.sequence, valid_until_ns)
        executor.close()
    else:
        session.executor = executor_class(session.backend, session.emit_executor_event)
        session.executor.submit(identifier, steps, session.backend.sequence, valid_until_ns)


def invoke_frozen_run_arm(case, root, executor_class):
    base = make_base(case, executor_class)
    v5 = types.ModuleType("map01_recovery_cover_mechanism_v5_runner")
    v5.configure = lambda: base
    sys.modules["map01_recovery_cover_mechanism_v5_runner"] = v5

    v6_source = frozen(SOURCES["v6_runner"])
    module = types.ModuleType("frozen_map01_recovery_cover_mechanism_v6_runner")
    module.__dict__["__file__"] = "frozen-git-object:" + SOURCES["v6_runner"]
    exec(compile(v6_source, module.__file__, "exec"), module.__dict__)
    module.threading = types.SimpleNamespace(Event=threading.Event,
                                            Timer=lambda interval, fn: ObservedTimer(interval, fn, case))
    result = module.configure()._run_arm(root, 0, "BOUNDED_RECOVERY", pathlib.Path("unused-fixture"))
    # The closure owns the FakeSession; expose its rows/clock marks from the
    # executor callback records saved by the closure's instance through hooks.
    session = case["session"]
    return result, session


def run_case(executor_class, name, planner_wait_ms, clock_delay_ms, lease_ms, root):
    case = {"name": name, "planner_wait_ms": planner_wait_ms,
            "clock_delay_ms": clock_delay_ms, "lease_ms": lease_ms}
    base = make_base(case, executor_class)
    # Keep the actual session instance visible to the raw recorder without
    # replacing the frozen runner function.
    def session_factory(command):
        session = FakeSession(case, executor_class)
        case["session"] = session
        return session
    base.JsonSession = session_factory
    v5 = types.ModuleType("map01_recovery_cover_mechanism_v5_runner")
    v5.configure = lambda: base
    sys.modules["map01_recovery_cover_mechanism_v5_runner"] = v5
    module = types.ModuleType("frozen_map01_recovery_cover_mechanism_v6_runner")
    module.__dict__["__file__"] = "frozen-git-object:" + SOURCES["v6_runner"]
    exec(compile(frozen(SOURCES["v6_runner"]), module.__file__, "exec"), module.__dict__)
    module.threading = types.SimpleNamespace(Event=threading.Event,
                                            Timer=lambda interval, fn: ObservedTimer(interval, fn, case))
    result = module.configure()._run_arm(root, 0, "BOUNDED_RECOVERY", pathlib.Path("unused-fixture"))
    session = case["session"]
    fallback_id = result["fallback_id"]
    release = next(x for x in session.backend.releases if x["id"] == fallback_id)
    record = {
        "case": name,
        "planner_wait_ms": planner_wait_ms,
        "clock_delay_ms": clock_delay_ms,
        "lease_ms_from_planner_start": lease_ms,
        "planner_start_ns": session.planner_start_ns,
        "timer_started_ns": case["timer_started_ns"],
        "timer_expired_ns": case["timer_expired_ns"],
        "clock_return_ns": session.clock_return_ns,
        "planner_end_ns": result["planner_window"]["end_ns"],
        "cancel_observed_ns": session.backend.cancel_observed_ns.get(fallback_id),
        "release_ns": release["release_ns"],
        "terminal_release_verified": result["terminal_release_verified"],
        "fallback_terminal_status": result["fallback_terminal_status"],
        "events": session.events,
        "runner_arm_summary": result,
    }
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construct-only", action="store_true")
    args = parser.parse_args()
    sources = source_manifest()
    executor_class = load_executor()
    if args.construct_only:
        case = {"name": "construction", "planner_wait_ms": 30, "clock_delay_ms": 0, "lease_ms": 250}
        with tempfile.TemporaryDirectory(prefix="issue6242-construction-") as scratch:
            result = run_case(executor_class, "construction-full-v6-run-arm", 30, 0, 250,
                              pathlib.Path(scratch) / "construction")
        release_delta_ms = (result["release_ns"] - result["timer_expired_ns"]) / 1e6
        if not result["terminal_release_verified"] or result["cancel_observed_ns"] is None or release_delta_ms > 50:
            raise SystemExit("construction smoke failed release/cancel gate")
        (OUT / "construction_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"construction": "PASS_EXACT_V6_RUN_ARM_FAKE_SESSION",
                          "release_after_timer_ms": release_delta_ms, "sources": sources}, indent=2))
        return

    rows = [
        run_case(executor_class, "A-clock-before-cancel-within-lease", 600, 400, 2000,
                 OUT / "candidate" / "A"),
        run_case(executor_class, "B-lease-before-clock-return", 600, 1600, 1500,
                 OUT / "candidate" / "B"),
    ]
    result = {"schema": "map01-v6-runner-clock-cancel-t3-v1",
              "allocation": "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3-20261002-01",
              "base_commit": BASE, "host": sys.platform, "python": sys.version,
              "docker_used": False,
              "scope": "exact frozen v6 _run_arm; mock base/JsonSession; actual executor-v10 and Lease Git objects",
              "sources": sources, "candidate_invocations": 1, "retries": 0, "cases": rows}
    (OUT / "raw_trace.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps([{k: row[k] for k in ("case", "timer_expired_ns", "clock_return_ns",
                                           "planner_end_ns", "cancel_observed_ns", "release_ns",
                                           "terminal_release_verified", "fallback_terminal_status")}
                      for row in rows], indent=2))


if __name__ == "__main__":
    main()
