from __future__ import annotations

import json
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "source_snapshot" / "live_control"))
from executor_v12 import Executor  # noqa: E402


class FakeBackend:
    def __init__(self):
        self.sequence = 17
        self.lease = None
        self.execute_started = threading.Event()
        self.rows = []

    def validate(self, steps):
        if steps != [{"op": "hold", "keys": ["Up"], "duration_ms": 1}]:
            raise ValueError("unexpected frozen program")

    def execute(self, step, cancel, identifier, index):
        self.rows.append({"event": "backend_execute", "id": identifier,
                          "step": index, "thread_id": threading.get_ident(),
                          "time_ns": time.perf_counter_ns()})
        self.execute_started.set()
        time.sleep(0.001)

    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": []}


def run_success_arm():
    backend = FakeBackend()
    callback_entered = threading.Event()
    allow_baseline_finish = threading.Event()
    rows = []
    submit_thread = {}

    def emit(event):
        if event.get("event") == "accepted":
            submit_thread["id"] = threading.get_ident()
            rows.append({"event": "accepted_callback_enter", "id": event["id"],
                         "thread_id": threading.get_ident(),
                         "time_ns": time.perf_counter_ns(),
                         "accepted_ns": event["accepted_ns"]})
            callback_entered.set()
            if not allow_baseline_finish.wait(2):
                raise TimeoutError("test baseline gate timeout")
            rows.append({"event": "synthetic_baseline_complete", "id": event["id"],
                         "thread_id": threading.get_ident(),
                         "time_ns": time.perf_counter_ns(), "baseline": {"tick": 41}})
        else:
            rows.append(dict(event, callback_thread_id=threading.get_ident(),
                             callback_time_ns=time.perf_counter_ns()))

    executor = Executor(backend, emit)
    args = ("barrier-success", [{"op": "hold", "keys": ["Up"], "duration_ms": 1}],
            backend.sequence, time.perf_counter_ns() + 5_000_000_000)
    submitter = threading.Thread(target=executor.submit, args=args)
    submitter.start()
    entered = callback_entered.wait(2)
    execute_before_release = backend.execute_started.is_set()
    allow_baseline_finish.set()
    submitter.join(2)
    if submitter.is_alive():
        raise TimeoutError("submit did not return")
    if executor.active is not None:
        executor.active[2].join(2)
    rows.extend(backend.rows)
    terminal = next((r for r in rows if r.get("event") == "terminal"), None)
    baseline = next((r for r in rows if r.get("event") == "synthetic_baseline_complete"), None)
    execute = next((r for r in rows if r.get("event") == "backend_execute"), None)
    return {"callback_entered": entered, "execute_before_baseline_release": execute_before_release,
            "submit_thread_id": submit_thread.get("id"), "rows": rows,
            "baseline_before_execute": bool(baseline and execute and baseline["time_ns"] < execute["time_ns"]),
            "baseline_and_submit_thread_match": bool(baseline and baseline["thread_id"] == submit_thread.get("id")),
            "terminal_status": terminal.get("status") if terminal else None,
            "worker_stopped": executor.active is None}


def run_failure_arm():
    backend = FakeBackend()
    emitted = []

    def emit(event):
        emitted.append(dict(event))
        if event.get("event") == "accepted":
            raise RuntimeError("injected scorer baseline failure")

    executor = Executor(backend, emit)
    caught = None
    try:
        executor.submit("barrier-failure", [{"op": "hold", "keys": ["Up"], "duration_ms": 1}],
                        backend.sequence, time.perf_counter_ns() + 5_000_000_000)
    except Exception as exc:
        caught = {"type": type(exc).__name__, "message": str(exc)}
    active = executor.active
    worker = active[2] if active is not None else None
    result = {"exception": caught, "active_id_after_failure": active[0] if active else None,
              "worker_started": bool(worker and worker.ident is not None),
              "worker_alive": bool(worker and worker.is_alive()),
              "backend_execute_count": len(backend.rows), "emitted_events": emitted,
              "used_id_retained": "barrier-failure" in executor.used_ids,
              "backend_lease_set": backend.lease is not None}
    # The worker was never started and no input was issued. Restore the fake
    # harness object only; this is not a production lifecycle repair.
    executor.active = None
    return result


def main():
    result = {"schema": "admission-baseline-barrier-a01-v1",
              "candidate_invocations": 1,
              "candidate_source": "PR #7429 head 8fe1160c89cba797dacc235e28441d1660c13845",
              "success_arm": run_success_arm(),
              "failure_arm": run_failure_arm()}
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
