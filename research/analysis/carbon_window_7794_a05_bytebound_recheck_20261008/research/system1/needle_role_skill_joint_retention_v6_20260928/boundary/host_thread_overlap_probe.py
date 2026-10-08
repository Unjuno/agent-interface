"""One-shot host thread-overlap instrumentation probe; no model/optimizer/seeds."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

SCHEMA = "needle-host-thread-overlap-boundary-v1"
TIMEOUT_SECONDS = 10.0


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: host_thread_overlap_probe.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists() or not output.parent.is_dir():
        raise SystemExit("STOP_OUTPUT_EXISTS_OR_PARENT_MISSING")

    call_entered = threading.Event()
    release_call = threading.Event()
    update_started = threading.Event()
    release_update = threading.Event()
    boxes = {}

    def inference_worker():
        worker = f"pid:{os.getpid()}:thread:{threading.get_ident()}"
        request_start = time.perf_counter_ns()
        call_start = time.perf_counter_ns()
        call_entered.set()
        if not release_call.wait(TIMEOUT_SECONDS):
            boxes["inference_error"] = "call_release_timeout"
            return
        call_end = time.perf_counter_ns()
        request_end = time.perf_counter_ns()
        boxes["query"] = {
            "query_id": "host-boundary-q1", "worker_id": worker,
            "role": "B", "scope": "synthetic-role-v1",
            "generation": 1, "adapter_generation": 1,
            "adapter_id": "placeholder-only",
            "snapshot": {"placeholder": True},
            "snapshot_sha256": hashlib.sha256(canonical({"placeholder": True})).hexdigest(),
            "inference_start_ns": request_start,
            "inference_end_ns": request_end,
            "inference_calls": [{"call_index": 0, "call_start_ns": call_start,
                                 "call_end_ns": call_end, "n": 1,
                                 "kind": "barrier-blocked-placeholder-no-model"}],
        }

    def trainer_worker():
        worker = f"pid:{os.getpid()}:thread:{threading.get_ident()}"
        if not call_entered.wait(TIMEOUT_SECONDS):
            boxes["trainer_error"] = "inference_call_start_timeout"
            return
        arrived = time.perf_counter_ns()
        start = time.perf_counter_ns()
        update_started.set()
        if not release_update.wait(TIMEOUT_SECONDS):
            boxes["trainer_error"] = "trainer_release_timeout"
            return
        end = time.perf_counter_ns()
        boxes["feedback"] = {
            "feedback_id": "host-boundary-f1", "query_id": "host-boundary-q1",
            "arrived_ns": arrived, "consumed_ns": start,
            "update_start_ns": start, "update_end_ns": end,
            "trainer_worker_id": worker,
            "activity_kind": "barrier-held-empty-critical-section-no-optimizer",
        }

    inference = threading.Thread(target=inference_worker, name="boundary-placeholder-inference")
    trainer = threading.Thread(target=trainer_worker, name="boundary-placeholder-trainer")
    inference.start()
    trainer.start()
    try:
        if not update_started.wait(TIMEOUT_SECONDS):
            raise RuntimeError("STOP_TRAINER_UPDATE_START_TIMEOUT")
        release_call.set()
        inference.join(TIMEOUT_SECONDS)
        if inference.is_alive():
            raise RuntimeError("STOP_INFERENCE_JOIN_TIMEOUT")
    finally:
        release_call.set()
        release_update.set()
        inference.join(TIMEOUT_SECONDS)
        trainer.join(TIMEOUT_SECONDS)
    if trainer.is_alive():
        raise RuntimeError("STOP_TRAINER_JOIN_TIMEOUT")
    if boxes.get("inference_error") or boxes.get("trainer_error"):
        raise RuntimeError(f"STOP_WORKER_ERROR:{boxes}")
    if "query" not in boxes or "feedback" not in boxes:
        raise RuntimeError(f"STOP_EVENT_RECORD_INCOMPLETE:{boxes}")

    document = {
        "schema": SCHEMA,
        "allocation": "needle-host-thread-overlap-boundary-20260928-v1",
        "execution_kind": "host-os-thread-instrumentation-boundary-only",
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        "process_id": os.getpid(), "clock": "time.perf_counter_ns",
                        "thread_count": 2, "docker_invocations": 0,
                        "formal_seed_access": False, "optimizer_steps": 0,
                        "model_calls": 0},
        "limitations": ["placeholder wait is not model inference",
                        "trainer critical section performs no optimizer or model work",
                        "does not establish CUDA/Docker/runtime scheduling or latency"],
        "online_window": {"queries": [boxes["query"]], "feedback": [boxes["feedback"]]},
    }
    payload = canonical(document) + b"\n"
    with output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"schema": SCHEMA, "result_bytes": len(payload),
                      "result_sha256": hashlib.sha256(payload).hexdigest(),
                      "workers_distinct": boxes["query"]["worker_id"] != boxes["feedback"]["trainer_worker_id"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
