"""Offline lease-release timing probe for the frozen v6 clock/cancel order."""
from __future__ import annotations

import hashlib
import importlib.util
import argparse
import json
import pathlib
import subprocess
import sys
import threading
import time
import types

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASE = "14b81dd1f6853623a694266b98538f812847257a"
SOURCES = {
    "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
    "v5_runner": "research/doom/map01_recovery_cover_mechanism_v5_runner.py",
    "base_runner": "research/doom/map01_recovery_cover_matched_v2_runner.py",
    "executor": "research/live_control/executor_v10.py",
    "lease": "research/live_control/lease.py",
}
OUT = pathlib.Path(__file__).resolve().parent


def frozen_source(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def load_exact_runtime():
    lease_bytes = frozen_source(SOURCES["lease"])
    lease_module = types.ModuleType("lease")
    lease_module.__file__ = "frozen-git-object:research/live_control/lease.py"
    exec(compile(lease_bytes, lease_module.__file__, "exec"), lease_module.__dict__)
    sys.modules["lease"] = lease_module

    executor_bytes = frozen_source(SOURCES["executor"])
    executor_module = types.ModuleType("frozen_executor_v10")
    executor_module.__file__ = "frozen-git-object:research/live_control/executor_v10.py"
    exec(compile(executor_bytes, executor_module.__file__, "exec"), executor_module.__dict__)
    return executor_module.Executor


class FakeBackend:
    def __init__(self):
        self.sequence = 0
        self.lease = None
        self.release_ns = None

    def validate(self, steps):
        if steps != [{"op": "hold"}]:
            raise ValueError("unexpected fake program")

    def execute(self, step, cancel, identifier, index):
        while True:
            cancel.wait(0.002)

    def release_all(self):
        self.release_ns = time.perf_counter_ns()
        return {"verified": True}


def run_case(executor_class, name, timer_ms, clock_delay_ms, lease_ms, cancel_first):
    backend = FakeBackend()
    events = []
    event_lock = threading.Lock()

    def emit(row):
        with event_lock:
            events.append(dict(row))

    executor = executor_class(backend, emit)
    started_ns = time.perf_counter_ns()
    executor.submit("fallback-" + name, [{"op": "hold"}], backend.sequence,
                    started_ns + lease_ms * 1_000_000)
    time.sleep(timer_ms / 1000)
    timer_expired_ns = time.perf_counter_ns()

    if cancel_first:
        executor.cancel("fallback-" + name)
        cancel_sent_ns = time.perf_counter_ns()
        time.sleep(clock_delay_ms / 1000)
        clock_return_ns = time.perf_counter_ns()
    else:
        time.sleep(clock_delay_ms / 1000)  # synchronous runtime_clock response wait
        clock_return_ns = time.perf_counter_ns()
        executor.cancel("fallback-" + name)
        cancel_sent_ns = time.perf_counter_ns()

    executor.close()
    terminal = next(row for row in events if row.get("event") == "terminal")
    record = {
        "case": name,
        "ordering": "cancel-before-clock" if cancel_first else "clock-before-cancel",
        "timer_ms": timer_ms,
        "clock_delay_ms": clock_delay_ms,
        "lease_ms_from_start": lease_ms,
        "started_ns": started_ns,
        "timer_expired_ns": timer_expired_ns,
        "clock_return_ns": clock_return_ns,
        "cancel_sent_ns": cancel_sent_ns,
        "release_ns": backend.release_ns,
        "terminal_ns": terminal.get("terminal_ns"),
        "terminal_status": terminal.get("status"),
        "release_verified": terminal.get("release", {}).get("verified"),
        "events": events,
    }
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construct-only", action="store_true")
    args = parser.parse_args()
    sources = {}
    for name, path in SOURCES.items():
        raw = frozen_source(path)
        compile(raw, path, "exec")
        sources[name] = {
            "path": path,
            "git_blob": subprocess.check_output(
                ["git", "rev-parse", f"{BASE}:{path}"], cwd=ROOT, text=True
            ).strip(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }

    # Construction mode validates exact source availability and syntax without
    # constructing the executor or consuming the single preregistered run.
    if args.construct_only:
        print(json.dumps({"construction": "PASS_SOURCE_AND_SYNTAX_ONLY", "sources": sources}, indent=2))
        return

    Executor = load_exact_runtime()
    rows = [
        run_case(Executor, "A-clock-before-cancel-within-lease", 600, 400, 2000, False),
        run_case(Executor, "B-clock-before-cancel-past-lease", 600, 1600, 1500, False),
        run_case(Executor, "C-cancel-before-clock-within-lease", 600, 400, 2000, True),
    ]
    result = {
        "schema": "map01-v6-clock-cancel-order-t0-v1",
        "base_commit": BASE,
        "host": sys.platform,
        "python": sys.version,
        "docker_used": False,
        "scope": "offline fake backend; actual frozen executor_v10 and lease modules loaded from Git objects",
        "sources": sources,
        "cases": rows,
        "retries": 0,
    }
    (OUT / "raw_trace.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": [{k: r[k] for k in (
        "case", "started_ns", "timer_expired_ns", "clock_return_ns", "cancel_sent_ns",
        "release_ns", "terminal_status", "release_verified")
        } for r in rows], "sources": sources}, indent=2))


if __name__ == "__main__":
    main()
