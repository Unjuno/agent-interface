"""One-shot offline probe using the exact executor/lease Git objects."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import threading
import time
import types

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASE = "673763554192ae26636e07d5a48f03b3cd7fb044"
SOURCES = {
    "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
    "executor": "research/live_control/executor_v10.py",
    "lease": "research/live_control/lease.py",
}
OUT = pathlib.Path(__file__).resolve().parent


def source(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def source_manifest():
    rows = {}
    for name, path in SOURCES.items():
        raw = source(path)
        compile(raw, path, "exec")
        rows[name] = {
            "path": path,
            "git_blob": subprocess.check_output(
                ["git", "rev-parse", f"{BASE}:{path}"], cwd=ROOT, text=True
            ).strip(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    return rows


def load_executor():
    lease_module = types.ModuleType("lease")
    lease_module.__file__ = "frozen-git-object:research/live_control/lease.py"
    exec(compile(source(SOURCES["lease"]), lease_module.__file__, "exec"), lease_module.__dict__)
    sys.modules["lease"] = lease_module
    executor_module = types.ModuleType("frozen_executor_v10")
    executor_module.__file__ = "frozen-git-object:research/live_control/executor_v10.py"
    exec(compile(source(SOURCES["executor"]), executor_module.__file__, "exec"), executor_module.__dict__)
    return executor_module.Executor


class CooperativeBackend:
    """Fake action that faithfully exits when the exact Lease signals cancel."""
    def __init__(self):
        self.sequence = 0
        self.release_ns = None
        self.cancel_observed_ns = None
        self.lease = None

    def validate(self, steps):
        if steps != [{"op": "hold"}]:
            raise ValueError("unexpected fake action program")

    def execute(self, step, cancel, identifier, index):
        while True:
            if cancel.is_set():
                self.cancel_observed_ns = time.perf_counter_ns()
                return
            if cancel.wait(0.002):
                self.cancel_observed_ns = time.perf_counter_ns()
                return

    def release_all(self):
        self.release_ns = time.perf_counter_ns()
        return {"verified": True}


def run_case(executor_class, name, timer_ms, clock_delay_ms, lease_ms, cancel_first):
    backend = CooperativeBackend()
    events = []
    lock = threading.Lock()
    terminal_event = threading.Event()

    def emit(row):
        with lock:
            events.append(dict(row))
        if row.get("event") == "terminal":
            terminal_event.set()

    executor = executor_class(backend, emit)
    started_ns = time.perf_counter_ns()
    executor.submit("fallback-" + name, [{"op": "hold"}], backend.sequence,
                    started_ns + lease_ms * 1_000_000)
    time.sleep(timer_ms / 1000)
    timer_expired_ns = time.perf_counter_ns()
    if cancel_first:
        executor.cancel("fallback-" + name)
        cancel_call_return_ns = time.perf_counter_ns()
        time.sleep(clock_delay_ms / 1000)
        clock_return_ns = time.perf_counter_ns()
    else:
        time.sleep(clock_delay_ms / 1000)
        clock_return_ns = time.perf_counter_ns()
        executor.cancel("fallback-" + name)
        cancel_call_return_ns = time.perf_counter_ns()
    if not terminal_event.wait(3):
        executor.close()
        raise TimeoutError(f"executor did not terminate in case {name}")
    executor.close()
    terminal = next(row for row in events if row.get("event") == "terminal")
    cancel_row = next(row for row in events if row.get("event") == "cancel_requested")
    return {
        "case": name,
        "ordering": "cancel-before-clock" if cancel_first else "clock-before-cancel",
        "timer_ms": timer_ms,
        "clock_delay_ms": clock_delay_ms,
        "lease_ms_from_start": lease_ms,
        "started_ns": started_ns,
        "timer_expired_ns": timer_expired_ns,
        "clock_return_ns": clock_return_ns,
        "cancel_call_return_ns": cancel_call_return_ns,
        "cancel_requested_ns": cancel_row.get("requested_ns"),
        "cancel_matched": cancel_row.get("matched"),
        "cancel_observed_ns": backend.cancel_observed_ns,
        "release_ns": backend.release_ns,
        "terminal_ns": terminal.get("terminal_ns"),
        "terminal_status": terminal.get("status"),
        "release_verified": terminal.get("release", {}).get("verified"),
        "events": events,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construct-only", action="store_true")
    args = parser.parse_args()
    sources = source_manifest()
    v6 = source(SOURCES["v6_runner"]).decode("utf-8")
    end_marker = "planner_end_ns = session.runtime_clock()"
    cancel_marker = 'session.send({"op": "cancel", "id": fallback_id})'
    end_pos = v6.index(end_marker)
    cancel_pos = v6.index(cancel_marker, end_pos)
    if not end_pos < cancel_pos:
        raise AssertionError("frozen v6 clock/cancel ordering did not match preregistration")
    if args.construct_only:
        Executor = load_executor()
        smoke = run_case(Executor, "construction-cooperative-cancel", 30, 0, 250, False)
        if not smoke["cancel_matched"] or smoke["cancel_observed_ns"] is None:
            raise AssertionError("construction failed to observe cooperative cancellation")
        release_delay_ms = (smoke["release_ns"] - smoke["cancel_requested_ns"]) / 1e6
        if smoke["terminal_status"] != "completed" or not smoke["release_verified"] or release_delay_ms > 50:
            raise AssertionError("construction cancellation/release gate failed")
        print(json.dumps({"construction": "PASS_COOPERATIVE_CANCEL_BEFORE_DEADLINE",
                          "release_delay_ms": release_delay_ms, "sources": sources}, indent=2))
        return

    Executor = load_executor()
    cases = [
        run_case(Executor, "A-clock-before-cancel-within-lease", 600, 400, 2000, False),
        run_case(Executor, "B-clock-before-cancel-past-lease", 600, 1600, 1500, False),
        run_case(Executor, "C-cancel-before-clock-within-lease", 600, 400, 2000, True),
    ]
    result = {
        "schema": "map01-v6-clock-cancel-order-t1-v1",
        "allocation": "MAP01-V6-CLOCK-CANCEL-ORDER-59-T1-20261002-01",
        "base_commit": BASE,
        "host": sys.platform,
        "python": sys.version,
        "docker_used": False,
        "scope": "actual executor_v10 and Lease Git objects; cooperative fake backend; no external effects",
        "v6_clock_before_cancel_source_order": True,
        "sources": sources,
        "cases": cases,
        "candidate_invocations": 1,
        "retries": 0,
    }
    (OUT / "raw_trace.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": [{k: row[k] for k in (
        "case", "timer_expired_ns", "clock_return_ns", "cancel_requested_ns",
        "cancel_observed_ns", "release_ns", "terminal_status", "cancel_matched",
        "release_verified") } for row in cases]}, indent=2))


if __name__ == "__main__":
    main()
