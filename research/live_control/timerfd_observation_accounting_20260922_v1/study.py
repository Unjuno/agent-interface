#!/usr/bin/env python3
"""Issue 4001: single-owner timerfd accounting. No GUI/input/provider activity."""
import errno
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"

def worker(spec):
    row = {"index": spec["index"], "rep": spec["rep"], "mode": spec["mode"],
           "pid": os.getpid(), "byteorder": sys.byteorder,
           "source_sha256": digest(Path(__file__).read_bytes()), "events": [],
           "authority": "none", "gui_observations": 0, "input_calls": 0}
    events = row["events"]
    fd = None
    callback_id = 0
    generation = -1
    try:
        before = time.monotonic_ns()
        fd = os.timerfd_create(time.CLOCK_MONOTONIC,
                               flags=os.TFD_NONBLOCK | os.TFD_CLOEXEC)
        events.append({"op": "create", "before": before, "after": time.monotonic_ns(),
                       "inheritable": os.get_inheritable(fd),
                       "initial": list(os.timerfd_gettime_ns(fd))})

        def arm(period):
            nonlocal generation
            generation += 1
            first = time.monotonic_ns() + 50_000_000
            before = time.monotonic_ns()
            old = os.timerfd_settime_ns(fd, flags=os.TFD_TIMER_ABSTIME,
                                        initial=first, interval=period)
            events.append({"op": "arm", "generation": generation, "first": first,
                           "period": period, "before": before,
                           "after": time.monotonic_ns(), "old_timer": list(old)})
            return first

        def wait_until(target):
            before = time.monotonic_ns()
            while True:
                remaining = target - time.monotonic_ns()
                if remaining <= 0:
                    break
                time.sleep(remaining / 1_000_000_000)
            events.append({"op": "wait", "target": target, "before": before,
                           "after": time.monotonic_ns()})

        def read(size):
            nonlocal callback_id
            before = time.monotonic_ns()
            try:
                raw = os.read(fd, size)
                after = time.monotonic_ns()
                error = 0
            except OSError as exc:
                after, raw, error = time.monotonic_ns(), b"", exc.errno
            item = {"op": "read", "generation": generation, "size": size,
                    "before": before, "after": after, "errno": error,
                    "hex": raw.hex()}
            events.append(item)
            if error == 0 and len(raw) == 8:
                item["count"] = int.from_bytes(raw, sys.byteorder, signed=False)
                callback_id += 1
                # This receipt is a real invocation of a trivial mock callback.
                # It is NOT an image, application-state sample or model receipt.
                events.append({"op": "observe", "generation": generation,
                               "receipt": callback_id, "time": time.monotonic_ns(),
                               "mock": True, "history": "UNKNOWN", "authority": "none"})

        mode = spec["mode"]
        if mode == "DISARMED":
            read(8)
        else:
            period = 2_000_000 if mode.startswith("PERIODIC") else 0
            first = arm(period)
            delay = 60_000_000 if mode.endswith("60MS") else 20_000_000
            wait_until(first + delay)
            if mode == "REARM":
                before = time.monotonic_ns()
                ready = bool(select.select([fd], [], [], 0)[0])
                events.append({"op": "ready", "before": before,
                               "after": time.monotonic_ns(), "ready": ready,
                               "generation": generation})
                first = arm(0)
                read(8)
                wait_until(first + 20_000_000)
                read(8)
                read(8)
            elif mode == "SHORT_READ":
                read(7)
                read(8)
                read(8)
            elif period:
                read(8)
                wait_until(time.monotonic_ns() + 20_000_000)
                read(8)
            else:
                read(8)
                read(8)
        row["result"] = "COMPLETE"
    except Exception as exc:
        row["result"] = "STOP_SETUP_OR_WORKER"
        row["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if fd is not None:
            before = time.monotonic_ns()
            os.close(fd)
            try:
                os.fstat(fd)
                closed_errno = 0
            except OSError as exc:
                closed_errno = exc.errno
            events.append({"op": "close", "before": before,
                           "after": time.monotonic_ns(), "errno": closed_errno})
    reads = [e for e in events if e["op"] == "read" and "count" in e]
    n = sum(e["count"] for e in reads)
    row["accounting"] = {
        "reported_expirations": n, "callback_receipts": callback_id,
        "unobserved_from_reported": n - callback_id,
        "naive_observation_count": n,
        "discarded_unread_history": spec["mode"] == "REARM"}
    return row

def run(out):
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if digest((HERE / name).read_bytes()) != expected:
            raise RuntimeError("STOP_SOURCE_MISMATCH: " + name)
    plan = json.loads((HERE / "PLAN.json").read_text())
    out.mkdir(parents=True, exist_ok=False)
    invocation = {"allocation": plan["allocation"], "start_ns": time.monotonic_ns(),
                  "freeze_sha256": digest((HERE / "FREEZE.json").read_bytes()),
                  "planned": len(plan["schedule"]), "pid": os.getpid()}
    (out / "INVOCATION.json").write_text(encoded(invocation))
    count = 0
    disposition = "COMPLETE"
    with (out / "RAW.jsonl").open("x") as raw:
        for spec in plan["schedule"]:
            command = [sys.executable, "-B", str(HERE / "study.py"), "worker", str(spec["index"])]
            try:
                proc = subprocess.run(command, capture_output=True, timeout=3, cwd=HERE,
                                      env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                envelope = {"index": spec["index"], "command": command,
                            "returncode": proc.returncode, "stdout": proc.stdout.decode("utf-8"),
                            "stderr": proc.stderr.decode("utf-8"),
                            "stdout_sha256": digest(proc.stdout)}
            except subprocess.TimeoutExpired as exc:
                envelope = {"index": spec["index"], "command": command,
                            "returncode": None, "STOP": "WORKER_TIMEOUT",
                            "stdout": (exc.stdout or b"").decode("utf-8", errors="replace"),
                            "stderr": (exc.stderr or b"").decode("utf-8", errors="replace")}
            raw.write(encoded(envelope)); raw.flush(); os.fsync(raw.fileno())
            count += 1
            if envelope["returncode"] != 0:
                disposition = "STOP_WORKER"
                break
    terminal = {"status": disposition, "completed_envelopes": count,
                "end_ns": time.monotonic_ns(), "raw_sha256": digest((out / "RAW.jsonl").read_bytes())}
    (out / "COMPLETE.json").write_text(encoded(terminal))
    print(encoded(terminal), end="")
    return 0 if disposition == "COMPLETE" else 2

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "worker":
        spec = json.loads((HERE / "PLAN.json").read_text())["schedule"][int(sys.argv[2])]
        result = worker(spec)
        print(encoded(result), end="")
        raise SystemExit(0 if result["result"] == "COMPLETE" else 2)
    if len(sys.argv) == 3 and sys.argv[1] == "run":
        raise SystemExit(run(Path(sys.argv[2]).resolve()))
    raise SystemExit("usage: study.py worker INDEX | run FRESH_OUTPUT")
