from __future__ import annotations
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "source_snapshot" / "live_control"))
from executor_v12 import Executor as ExecutorV12  # noqa: E402
from executor_v13 import Executor as ExecutorV13  # noqa: E402


class FakeBackend:
    def __init__(self):
        self.sequence = 17
        self.lease = None
        self.execute_count = 0

    def validate(self, steps):
        if steps != [{"op": "hold", "keys": ["Up"], "duration_ms": 1}]:
            raise ValueError("unexpected frozen program")

    def execute(self, step, cancel, identifier, index):
        self.execute_count += 1

    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": []}


def run_cell(name, executor_type):
    backend = FakeBackend()
    callback_events = []

    def emit(event):
        if event.get("event") == "accepted":
            # The scorer baseline hook would execute here, before forwarding
            # accepted to the outer event sink. Its failure is injected.
            raise RuntimeError("injected scorer baseline failure")
        callback_events.append(event)

    executor = executor_type(backend, emit)
    caught = None
    try:
        executor.submit(f"barrier-a02-{name.lower()}",
                        [{"op": "hold", "keys": ["Up"], "duration_ms": 1}],
                        backend.sequence, time.perf_counter_ns() + 5_000_000_000)
    except Exception as exc:
        caught = {"type": type(exc).__name__, "message": str(exc)}

    active = executor.active
    worker = active[2] if active is not None else None
    before_close = {
        "exception": caught,
        "active_id": active[0] if active else None,
        "worker_started": bool(worker and worker.ident is not None),
        "worker_alive": bool(worker and worker.is_alive()),
        "execute_count": backend.execute_count,
        "used_id_retained": f"barrier-a02-{name.lower()}" in executor.used_ids,
        "backend_lease_set": backend.lease is not None,
        "admission_publication_error": executor.admission_publication_errors.get(
            f"barrier-a02-{name.lower()}"),
        "watcher_registered": f"barrier-a02-{name.lower()}" in
            getattr(executor, "release_watch_stops", {}),
    }
    close_error = None
    try:
        executor.close()
    except Exception as exc:
        close_error = {"type": type(exc).__name__, "message": str(exc)}
    return {
        "executor": name,
        "before_close": before_close,
        "close_error": close_error,
        "closed_after_close": executor.closed,
        "active_retained_after_close": executor.active is not None,
        "worker_alive_after_close": bool(worker and worker.is_alive()),
        "callback_events_after_failure": callback_events,
    }


def main():
    result = {
        "schema": "admission-baseline-barrier-a02-v1",
        "candidate_invocations": 1,
        "candidate_source": "PR #7429 head e22e59732033438916415f71b53f86695b1c448a",
        "cells": [run_cell("ExecutorV12", ExecutorV12),
                  run_cell("ExecutorV13", ExecutorV13)],
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
