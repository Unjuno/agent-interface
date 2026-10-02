"""One-shot host-only run of the exact current-main v6 _run_arm closure."""
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

BASE = "279679a33f6029c6e13eca6be51890d8bebb25e7"
ALLOCATION = "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3S-20261002-01"
HERE = pathlib.Path(__file__).resolve().parent
SOURCES = {
    "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
    "executor": "research/live_control/executor_v10.py",
    "lease": "research/live_control/lease.py",
}


def git(*args, text=False):
    return subprocess.check_output(["git", *args], text=text)


def frozen(path):
    return git("show", f"{BASE}:{path}")


def source_manifest():
    result = {}
    for name, path in SOURCES.items():
        raw = frozen(path)
        compile(raw, f"{BASE}:{path}", "exec")
        result[name] = {
            "path": path,
            "git_blob": git("rev-parse", f"{BASE}:{path}", text=True).strip(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    return result


def load_executor():
    lease_module = types.ModuleType("lease")
    exec(compile(frozen(SOURCES["lease"]), SOURCES["lease"], "exec"), lease_module.__dict__)
    sys.modules["lease"] = lease_module
    executor_module = types.ModuleType("frozen_executor_v10")
    exec(compile(frozen(SOURCES["executor"]), SOURCES["executor"], "exec"), executor_module.__dict__)
    return executor_module.Executor


class Backend:
    def __init__(self):
        self.sequence = 7
        self.lease = None
        self.current_id = None
        self.cancel_observed_ns = {}
        self.releases = []

    def validate(self, steps):
        if type(steps) is not list or not steps:
            raise ValueError("nonempty list of steps required")

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
        row = {"id": self.current_id, "release_ns": time.perf_counter_ns(), "verified": True}
        self.releases.append(row)
        return {"verified": True}


class Process:
    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0


class Session:
    def __init__(self, case):
        self.case = case
        self.queue = queue.Queue()
        self.pending = collections.deque()
        self.events = []
        self.latest_exact = {"event": "observation", "sequence": 7,
                             "capture_ns": time.perf_counter_ns() - 5_000_000, "exact": True}
        self.backend = Backend()
        self.executor = None
        self.process = Process()
        self.clock_calls = 0
        self.planner_start_ns = None
        self.clock_return_ns = None
        self._put({"event": "ready", "presentation": "full"})
        self._put(dict(self.latest_exact))

    def _put(self, row):
        self.queue.put(dict(row))

    def emit_executor_event(self, row):
        if row.get("event") == "terminal" and row.get("release", {}).get("verified") is True:
            receipt = {"event": "input_released", "id": row["id"], "verified": True,
                       "release_ns": self.backend.releases[-1]["release_ns"]}
            self.events.append(receipt)
            self._put(receipt)
        self.events.append(dict(row))
        self._put(row)

    def wait(self, predicate, timeout=20.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for _ in range(len(self.pending)):
                row = self.pending.popleft()
                if predicate(row):
                    return row
                self.pending.append(row)
            try:
                row = self.queue.get(timeout=min(0.05, max(0.005, deadline - time.monotonic())))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError("mock process exited before expected event")
                continue
            if predicate(row):
                return row
            self.pending.append(row)
        raise TimeoutError("mock session event timeout")

    def runtime_clock(self):
        self.clock_calls += 1
        if self.clock_calls == 2:
            self.planner_start_ns = time.perf_counter_ns()
        elif self.clock_calls == 3:
            time.sleep(self.case["clock_delay_ms"] / 1000)
            self.clock_return_ns = time.perf_counter_ns()
        return time.perf_counter_ns()

    def send(self, command):
        if command["op"] == "cancel":
            self.executor.cancel(command["id"])
        elif command["op"] == "finish":
            self._put({"event": "post_control_score", "score": {"mock": True}})
        else:
            raise ValueError(f"unexpected command {command!r}")

    def terminate(self):
        if self.executor is not None:
            self.executor.close()


class Timer(threading.Timer):
    def __init__(self, interval, function, case):
        self.case = case
        def fire():
            self.case["timer_expired_ns"] = time.perf_counter_ns()
            function()
        super().__init__(interval, fire)

    def start(self):
        self.case["timer_started_ns"] = time.perf_counter_ns()
        super().start()


def build_base(case, executor_class):
    base = types.SimpleNamespace(
        ALLOCATION_ID=ALLOCATION, EXPECTED_WORKFLOW_PATH="offline",
        PLANNER_WAIT_MS=case["planner_wait_ms"], PRELUDE_KEYS=("forward",),
        PRELUDE_MS=5, SessionError=RuntimeError,
    )
    def make_session(command):
        session = Session(case)
        case["session"] = session
        return session
    def submit(session, identifier, steps, valid_until_ns):
        executor = executor_class(session.backend, session.emit_executor_event)
        if identifier.endswith("-prelude"):
            executor.submit(identifier, steps, session.backend.sequence, valid_until_ns)
            executor.active[2].join()
            executor.close()
        else:
            session.executor = executor
            executor.submit(identifier, steps, session.backend.sequence, valid_until_ns)
    class Window:
        def __init__(self, start_ns, end_ns):
            self.start_ns, self.end_ns = start_ns, end_ns
            self.duration_ns = end_ns - start_ns
    base.JsonSession = make_session
    base._session_command = lambda runtime, fixture: {"runtime": str(runtime), "fixture": str(fixture)}
    base._submit = submit
    base._wait_exact_after = lambda session, sequence: {**session.latest_exact,
        "sequence": sequence + 1, "capture_ns": time.perf_counter_ns()}
    base._source_guard = lambda session: (
        dict(session.latest_exact), {"frame_rgb_sha256": "synthetic-frame"}, {"health": 100})
    base.recovery_valid_until_ns = lambda capture_ns, planner_start_ns: (
        planner_start_ns + case["lease_ms"] * 1_000_000)
    base.build_coast_steps = lambda: [{"op": "coast"}]
    base.build_recovery_steps = lambda: [{"op": "hold", "keys": ["forward"], "duration_ms": 5000}]
    base.recovery_guard_failed = lambda *args: (False, None)
    base.Window = Window
    base.fallback_input_bounds = lambda events, identifier, window: {
        "event_count": sum(e.get("id") == identifier for e in events),
        "window_duration_ns": window.duration_ns}
    base.terminal_release_ok = lambda events, identifier: any(
        e.get("event") == "input_released" and e.get("id") == identifier and e.get("verified") is True
        for e in events)
    base.load_json = lambda path: {"mock": True, "name": pathlib.Path(path).name}
    return base


def invoke(case, executor_class, root):
    base = build_base(case, executor_class)
    v5 = types.ModuleType("map01_recovery_cover_mechanism_v5_runner")
    v5.configure = lambda: base
    sys.modules[v5.__name__] = v5
    module = types.ModuleType("frozen_map01_recovery_cover_mechanism_v6_runner")
    module.__file__ = "git-object:" + SOURCES["v6_runner"]
    exec(compile(frozen(SOURCES["v6_runner"]), module.__file__, "exec"), module.__dict__)
    module.threading = types.SimpleNamespace(Event=threading.Event,
        Timer=lambda interval, fn: Timer(interval, fn, case))
    summary = module.configure()._run_arm(root, 0, "BOUNDED_RECOVERY", pathlib.Path("fixture-unused"))
    session = case["session"]
    fallback_id = summary["fallback_id"]
    release = next(e for e in session.backend.releases if e["id"] == fallback_id)
    row = {
        "case": case["name"], "planner_wait_ms": case["planner_wait_ms"],
        "clock_delay_ms": case["clock_delay_ms"], "lease_ms": case["lease_ms"],
        "planner_start_ns": session.planner_start_ns,
        "timer_started_ns": case["timer_started_ns"],
        "timer_expired_ns": case["timer_expired_ns"],
        "clock_return_ns": session.clock_return_ns,
        "planner_end_ns": summary["planner_window"]["end_ns"],
        "cancel_observed_ns": session.backend.cancel_observed_ns.get(fallback_id),
        "release_ns": release["release_ns"],
        "terminal_release_verified": summary["terminal_release_verified"],
        "fallback_terminal_status": summary["fallback_terminal_status"],
        "events": session.events, "runner_arm_summary": summary,
    }
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    executor_class = load_executor()
    if args.construction:
        case = {"name": "construction", "planner_wait_ms": 30, "clock_delay_ms": 0, "lease_ms": 250}
        with tempfile.TemporaryDirectory(prefix="6242-t3s-construction-") as scratch:
            row = invoke(case, executor_class, pathlib.Path(scratch) / "run")
        delay_ms = (row["release_ns"] - row["timer_expired_ns"]) / 1e6
        if not row["terminal_release_verified"] or row["cancel_observed_ns"] is None or delay_ms > 50:
            raise SystemExit("construction gate failed")
        out = {"status": "PASS_EXACT_RUN_ARM_CONSTRUCTION", "release_after_timer_ms": delay_ms,
               "source_manifest": source_manifest()}
        (HERE / "construction_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return
    cases = [
        {"name": "A-clock-before-cancel-within-lease", "planner_wait_ms": 600, "clock_delay_ms": 400, "lease_ms": 2000},
        {"name": "B-lease-before-clock-return", "planner_wait_ms": 600, "clock_delay_ms": 1600, "lease_ms": 1500},
    ]
    with tempfile.TemporaryDirectory(prefix="6242-t3s-formal-") as scratch:
        rows = [invoke(case, executor_class, pathlib.Path(scratch) / case["name"]) for case in cases]
    raw = {
        "schema": "map01-v6-runner-clock-cancel-t3-successor-v1",
        "allocation": ALLOCATION, "base_commit": BASE, "python": sys.version,
        "host_platform": sys.platform, "docker_used": False,
        "scope": "exact frozen v6 _run_arm; fake JsonSession/backend; exact executor-v10 and Lease git objects",
        "candidate_invocations": 1, "retries": 0, "source_manifest": source_manifest(), "cases": rows,
    }
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    raw["freeze_sha256"] = hashlib.sha256(freeze_bytes).hexdigest()
    raw["frozen_candidate_sha256"] = json.loads(freeze_bytes)["candidate_sha256"]
    raw["frozen_auditor_sha256"] = json.loads(freeze_bytes)["auditor_sha256"]
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    (results / "raw_trace.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps([{k: row[k] for k in ("case", "timer_expired_ns", "clock_return_ns",
        "planner_end_ns", "cancel_observed_ns", "release_ns", "terminal_release_verified",
        "fallback_terminal_status")} for row in rows], sort_keys=True))


if __name__ == "__main__":
    main()
