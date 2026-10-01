from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import pathlib
import queue
import subprocess
import sys
import tempfile
import threading
import time
import types

BASE = "4cf0a3dfde1219671b671bf0a9079a11dcb2e159"
ALLOCATION = "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3V-20261002-01"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
SOURCES = {
    "v6_runner": ("research/doom/map01_recovery_cover_mechanism_v6_runner.py",
                  "10344582ffa2ce339bc48dd8d680512a71f4eddc",
                  "9790becf98104b3a956c73bee945266a8517e41c2396c1a8b29c924e14d26012"),
    "executor": ("research/live_control/executor_v10.py",
                  "e0a31884307eeac405094a624e3a63222acc656f",
                  "e55f82e6f15c39914a4213873d39386205a792c98b54d0cf54be0812c69ecb2e"),
    "lease": ("research/live_control/lease.py",
              "b9dac6bb4063928354733d79bf371909a288a3d1",
              "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f"),
}


def atomic_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frozen_sources() -> tuple[dict[str, bytes], dict[str, dict[str, str]]]:
    sources, manifest = {}, {}
    for name, (path, expected_blob, expected_sha) in SOURCES.items():
        blob = subprocess.check_output(["git", "rev-parse", f"{BASE}:{path}"], text=True).strip()
        raw = subprocess.check_output(["git", "show", f"{BASE}:{path}"])
        compile(raw, f"{BASE}:{path}", "exec")
        digest = sha256_bytes(raw)
        if blob != expected_blob or digest != expected_sha:
            raise RuntimeError(f"FROZEN_SOURCE_MISMATCH:{name}:{blob}:{digest}")
        sources[name] = raw
        manifest[name] = {"path": path, "git_blob": blob, "sha256": digest, "bytes": str(len(raw))}
    return sources, manifest


def package_hashes() -> dict[str, str]:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    paths = {"plan": "PLAN.md", "candidate": "run_t3v.py", "auditor": "audit_t3v.py", "tests": "test_t3v.py"}
    found = {key: sha256_bytes((HERE / path).read_bytes()) for key, path in paths.items()}
    expected = freeze["package_sha256"]
    if found != expected:
        raise RuntimeError(f"FROZEN_PACKAGE_MISMATCH:{found}")
    return found


def load_exact_modules(clock):
    sources, manifest = frozen_sources()
    lease_module = types.ModuleType("lease")
    exec(compile(sources["lease"], SOURCES["lease"][0], "exec"), lease_module.__dict__)
    sys.modules["lease"] = lease_module
    executor_module = types.ModuleType("frozen_executor_v10")
    exec(compile(sources["executor"], SOURCES["executor"][0], "exec"), executor_module.__dict__)
    executor_module.Lease = lambda deadline: lease_module.Lease(deadline, clock=clock.now_ns)
    runner_module = types.ModuleType("frozen_map01_v6_runner")
    runner_module.__file__ = "git-object:" + SOURCES["v6_runner"][0]
    exec(compile(sources["v6_runner"], runner_module.__file__, "exec"), runner_module.__dict__)
    return executor_module.Executor, runner_module, manifest


class Clock:
    @staticmethod
    def now_ns() -> int:
        return time.perf_counter_ns()


class Process:
    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0


class Backend:
    def __init__(self, clock):
        self.clock = clock
        self.sequence = 7
        self.current_id = None
        self.cancel_observed_ns = {}
        self.releases = []

    def validate(self, steps):
        if type(steps) is not list or not steps:
            raise ValueError("nonempty steps required")

    def execute(self, step, cancel, identifier, index):
        self.current_id = identifier
        if identifier.endswith("-prelude"):
            return
        while not cancel.wait(0.002):
            pass
        self.cancel_observed_ns[identifier] = self.clock.now_ns()
        # Cooperative return is intentional: exact Executor-v10 reports completed.

    def release_all(self):
        row = {"id": self.current_id, "release_ns": self.clock.now_ns(), "verified": True}
        self.releases.append(row)
        return {"verified": True}


class Session:
    def __init__(self, case, clock, executor_class):
        self.case, self.clock, self.executor_class = case, clock, executor_class
        self.queue = queue.Queue()
        self.pending = collections.deque()
        self.events = []
        self.latest_exact = {"event": "observation", "sequence": 7,
                             "capture_ns": clock.now_ns() - 5_000_000, "exact": True}
        self.backend = Backend(clock)
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

    def wait(self, predicate, timeout=10.0):
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
        raise TimeoutError("mock event timeout")

    def runtime_clock(self):
        self.clock_calls += 1
        if self.clock_calls == 2:
            self.planner_start_ns = self.clock.now_ns()
            return self.planner_start_ns
        if self.clock_calls == 3:
            time.sleep(self.case["clock_delay_ms"] / 1000)
            value = self.clock.now_ns()
            self.clock_return_ns = value
            return value
        return self.clock.now_ns()

    def send(self, command):
        if command["op"] == "cancel":
            self.executor.cancel(command["id"])
        elif command["op"] == "finish":
            self._put({"event": "post_control_score", "score": {"mock": True}})
        else:
            raise ValueError(f"unexpected command: {command!r}")

    def terminate(self):
        if self.executor is not None:
            self.executor.close()


class TimedTimer(threading.Timer):
    def __init__(self, interval, function, case, clock):
        self.case, self.clock = case, clock
        def fire():
            self.case["timer_expired_ns"] = self.clock.now_ns()
            function()
        super().__init__(interval, fire)

    def start(self):
        self.case["timer_started_ns"] = self.clock.now_ns()
        super().start()


def make_case(case, executor_class, runner_module, clock):
    base = types.SimpleNamespace(ALLOCATION_ID=ALLOCATION, EXPECTED_WORKFLOW_PATH="offline",
        PLANNER_WAIT_MS=case["planner_wait_ms"], PRELUDE_KEYS=("forward",), PRELUDE_MS=5,
        SessionError=RuntimeError)

    def make_session(command):
        session = Session(case, clock, executor_class)
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
        "sequence": sequence + 1, "capture_ns": clock.now_ns()}
    base._source_guard = lambda session: (dict(session.latest_exact),
        {"frame_rgb_sha256": "synthetic-frame"}, {"health": 100})
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
    v5 = types.ModuleType("map01_recovery_cover_mechanism_v5_runner")
    v5.configure = lambda: base
    sys.modules[v5.__name__] = v5
    runner_module.threading = types.SimpleNamespace(Event=threading.Event,
        Timer=lambda interval, fn: TimedTimer(interval, fn, case, clock))
    return runner_module.configure()._run_arm


def invoke_case(definition):
    case = dict(definition)
    clock = Clock()
    executor_class, runner_module, manifest = load_exact_modules(clock)
    run_arm = make_case(case, executor_class, runner_module, clock)
    with tempfile.TemporaryDirectory(prefix="6261-t3v-") as scratch:
        summary = run_arm(pathlib.Path(scratch) / "run", 0, "BOUNDED_RECOVERY", pathlib.Path("fixture-unused"))
    session = case["session"]
    fallback_id = summary["fallback_id"]
    release = next(row for row in session.backend.releases if row["id"] == fallback_id)
    cancel = next((e for e in session.events if e.get("event") == "cancel_requested" and e.get("id") == fallback_id), None)
    return {
        **{key: value for key, value in case.items() if key != "session"},
        "planner_start_ns": session.planner_start_ns,
        "timer_started_ns": case.get("timer_started_ns"),
        "timer_expired_ns": case.get("timer_expired_ns"),
        "clock_return_ns": session.clock_return_ns,
        "planner_end_ns": summary["planner_window"]["end_ns"],
        "cancel_observed_ns": session.backend.cancel_observed_ns.get(fallback_id),
        "cancel_requested": cancel,
        "release_ns": release["release_ns"],
        "terminal_release_verified": summary["terminal_release_verified"],
        "fallback_terminal_status": summary["fallback_terminal_status"],
        "events": session.events,
        "runner_arm_summary": summary,
        "source_manifest": manifest,
    }


def case_definitions():
    return [
        {"name": "A-clock-before-cancel-within-lease", "planner_wait_ms": 600,
         "clock_delay_ms": 400, "lease_ms": 2000},
        {"name": "B-lease-before-clock-return", "planner_wait_ms": 600,
         "clock_delay_ms": 1600, "lease_ms": 1500},
    ]


def gate_errors(row, construction=False):
    errors = []
    name = row.get("name")
    if row.get("planner_end_ns") != row.get("clock_return_ns"):
        errors.append("PLANNER_END_NOT_EXACT_CLOCK_RETURN")
    if row.get("terminal_release_verified") is not True:
        errors.append("RELEASE_NOT_VERIFIED")
    cancel = row.get("cancel_requested") or {}
    if name == "A-clock-before-cancel-within-lease" or construction:
        if cancel.get("matched") is not True:
            errors.append("CANCEL_NOT_MATCHED")
        if row.get("cancel_observed_ns") is None:
            errors.append("BACKEND_DID_NOT_OBSERVE_CANCEL")
        if row.get("fallback_terminal_status") != "completed":
            errors.append("COOPERATIVE_TERMINAL_NOT_COMPLETED")
        low_ms, high_ms = (0, 50) if construction else (350, 2000)
        lag = (row.get("release_ns", 0) - row.get("timer_expired_ns", 0)) / 1_000_000
        if not low_ms <= lag <= high_ms:
            errors.append("A_RELEASE_TIMER_LAG_OUT_OF_RANGE")
        if row.get("release_ns", 0) < row.get("clock_return_ns", 0):
            errors.append("A_RELEASE_PRECEDES_CLOCK_RETURN")
        if row.get("release_ns", 0) - cancel.get("requested_ns", 0) > 50_000_000:
            errors.append("A_RELEASE_TOO_LATE_AFTER_CANCEL")
    else:
        deadline = row.get("planner_start_ns", 0) + row.get("lease_ms", 0) * 1_000_000
        if row.get("fallback_terminal_status") != "expired":
            errors.append("B_TERMINAL_NOT_EXPIRED")
        if not deadline <= row.get("release_ns", 0) <= deadline + 50_000_000:
            errors.append("B_RELEASE_OUTSIDE_LEASE_BOUND")
        if row.get("release_ns", 0) >= row.get("clock_return_ns", 0):
            errors.append("B_RELEASE_NOT_BEFORE_CLOCK_RETURN")
        if cancel.get("matched") is not False or cancel.get("requested_ns", 0) < row.get("clock_return_ns", 0):
            errors.append("B_LATE_CANCEL_NOT_UNMATCHED")
        if row.get("cancel_observed_ns") is not None:
            errors.append("B_BACKEND_OBSERVED_LATE_CANCEL")
    return errors


def run_construction():
    package_hashes()
    _, manifest = frozen_sources()
    row = invoke_case({"name": "construction", "planner_wait_ms": 30,
                       "clock_delay_ms": 0, "lease_ms": 250})
    errors = gate_errors(row, construction=True)
    attempt = {"allocation": ALLOCATION, "base_commit": BASE, "status": "PASS" if not errors else "STOP_CONSTRUCTION",
               "candidate_invocations": 0, "construction_invocations": 1, "retries": 0,
               "source_manifest": manifest, "package_sha256": package_hashes(), "case": row,
               "gate_errors": errors}
    atomic_json(RESULTS / "construction_attempt.json", attempt)
    print(json.dumps({"status": attempt["status"], "gate_errors": errors,
                      "terminal": row.get("fallback_terminal_status")}, sort_keys=True))
    return 0 if not errors else 1


def run_candidate():
    package_hashes()
    _, manifest = frozen_sources()
    cases, failures = [], []
    # A single invocation: preserve an exception as a row and never substitute/retry it.
    for definition in case_definitions():
        try:
            row = invoke_case(definition)
            row_errors = gate_errors(row)
            if row_errors:
                failures.extend(f"{definition['name']}:{error}" for error in row_errors)
            cases.append({"row": row, "gate_errors": row_errors})
        except Exception as exc:
            cases.append({"row": {"name": definition["name"], "exception": repr(exc)},
                          "gate_errors": ["CASE_EXCEPTION"]})
            failures.append(f"{definition['name']}:CASE_EXCEPTION")
            break
    freeze_raw = (HERE / "FREEZE.json").read_bytes()
    payload = {"schema": "map01-v6-runner-shared-clock-t3v-v1", "allocation": ALLOCATION,
               "base_commit": BASE, "python": sys.version, "platform": sys.platform,
               "scope": "exact v6 _run_arm + exact Executor-v10/Lease objects; fake session/backend; shared monotonic source",
               "candidate_invocations": 1, "retries": 0, "source_manifest": manifest,
               "package_sha256": package_hashes(), "freeze_sha256": sha256_bytes(freeze_raw),
               "cases": cases, "candidate_gate_errors": failures,
               "status": "PASS_CANDIDATE_GATES" if not failures and len(cases) == 2 else "FAIL_CANDIDATE_GATES"}
    atomic_json(RESULTS / "candidate_raw.json", payload)
    print(json.dumps({"status": payload["status"], "case_count": len(cases),
                      "gate_errors": failures}, sort_keys=True))
    return 0 if payload["status"] == "PASS_CANDIDATE_GATES" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    return run_construction() if args.construction else run_candidate()


if __name__ == "__main__":
    raise SystemExit(main())
