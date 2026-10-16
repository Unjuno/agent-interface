"""One-shot candidate probe: accepted-event delivery fails before baseline/input."""
import json
import platform
import sys
import time
from pathlib import Path


root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "source_snapshot"))
from executor_v13_admission_baseline import Executor  # noqa: E402


class Backend:
    def __init__(self):
        self.sequence = 17
        self.lease = None
        self.execute_count = 0

    def validate(self, steps):
        if not isinstance(steps, list):
            raise ValueError("steps must be a list")

    def execute(self, *args):
        self.execute_count += 1


events = []
baseline_calls = []
backend = Backend()


def emit(event):
    events.append(dict(event))
    if event.get("event") == "accepted":
        # Model accept-then-raise: the sink may have written before losing ack.
        raise RuntimeError("injected accepted-event acknowledgement loss")


def baseline(identifier, accepted_ns):
    baseline_calls.append({"identifier": identifier, "accepted_ns": accepted_ns})


executor = Executor(backend, emit, pre_input_baseline=baseline)
submit_error = None
try:
    executor.submit(
        "sink-compose-1",
        [{"key": "w", "duration_ms": 10}],
        expected_sequence=17,
        valid_until_ns=time.perf_counter_ns() + 10_000_000_000,
    )
except BaseException as exc:
    submit_error = {"type": type(exc).__name__, "message": str(exc)}

active_before_close = executor.active
worker = active_before_close[2] if active_before_close else None
lease = active_before_close[1] if active_before_close else None
before_close = {
    "active_id": active_before_close[0] if active_before_close else None,
    "backend_lease_matches_active": backend.lease is lease and lease is not None,
    "used_id_retained": "sink-compose-1" in executor.used_ids,
    "worker_started": worker is not None and worker.ident is not None,
    "worker_alive": worker is not None and worker.is_alive(),
    "backend_execute_count": backend.execute_count,
    "baseline_calls": baseline_calls,
    "events": events,
}

close_error = None
try:
    executor.close()
except BaseException as exc:
    close_error = {"type": type(exc).__name__, "message": str(exc)}

after_close = {
    "active_id": executor.active[0] if executor.active else None,
    "backend_lease_retained": backend.lease is not None,
    "worker_started": worker is not None and worker.ident is not None,
}
result = {
    "schema": "admission-baseline-sink-compose-a02-v1",
    "run_id": "MAP01-ADMISSION-BASELINE-SINK-COMPOSE-A02-20261004",
    "environment": {
        "platform": platform.platform(),
        "python": sys.version,
    },
    "candidate_source": "#7440 head 99b7d130742b4e884709a862bc074d15e6b42ac9",
    "comparison_fix_source": "#7429 head 7de3932c9435256796322b11409da1a6b09d6809",
    "scope": "exact source copies for #7440 ExecutorV12-derived baseline candidate; fake backend and sink only",
    "submit_error": submit_error,
    "before_close": before_close,
    "close_error": close_error,
    "after_close": after_close,
}
(root / "RAW.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
