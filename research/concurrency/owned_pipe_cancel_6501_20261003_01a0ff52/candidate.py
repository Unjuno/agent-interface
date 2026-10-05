"""Frozen, isolated Linux pipe experiment; never imported by production code."""
import asyncio
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import platform
import selectors
import sys
import threading
import time

ALLOCATION = "6501-OWNED-PIPE-ORBSTACK-A01-20261003-01a0ff52-70ab"
POLICIES = ("wrapper_cancel", "close_reader", "control_pipe")
CONDITIONS = ("cancel_blocked", "data_ready")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Trace:
    def __init__(self):
        self.lock = threading.RLock()
        self.events = []
        self.resources = {}
        self.active = False
        self.tid = None

    def emit(self, kind, **data):
        with self.lock:
            self.events.append({"seq": len(self.events), "kind": kind, **data})

    def pipe(self, prefix):
        r, w = os.pipe()
        for name, fd in ((prefix + "_r", r), (prefix + "_w", w)):
            self.resources[name] = {"fd": fd, "closed": False}
            self.emit("fd_owned", resource=name, fd=fd)
        return r, w

    def close(self, name, actor):
        with self.lock:
            entry = self.resources[name]
            if entry["closed"]:
                raise RuntimeError("double close: " + name)
            os.close(entry["fd"])
            entry["closed"] = True
            self.emit("fd_closed", resource=name, fd=entry["fd"], actor=actor)

    def snapshot(self, task, future):
        with self.lock:
            fds = {}
            for name, entry in self.resources.items():
                try:
                    os.fstat(entry["fd"])
                    observed_open = True
                except OSError as exc:
                    if exc.errno != 9:
                        raise
                    observed_open = False
                if observed_open == entry["closed"]:
                    raise RuntimeError("FD ownership/OS state disagreement: " + name)
                fds[name] = {"fd": entry["fd"], "open": observed_open}
            return {"wrapper_done": task.done(), "wrapper_cancelled": task.cancelled(),
                    "future_done": future.done(), "future_cancelled": future.cancelled(),
                    "worker_active": self.active, "fds": fds}


def proc_observation(tid):
    p = pathlib.Path("/proc/self/task") / str(tid)
    call = (p / "syscall").read_text().split()
    state = (p / "stat").read_text().rsplit(")", 1)[1].split()[0]
    # Do not publish syscall buffer addresses, stack pointers, or PCs.
    return {"tid": tid, "state": state, "wchan": (p / "wchan").read_text().strip(),
            "syscall_nr": int(call[0]) if call[0] != "running" else None,
            "fd": int(call[1], 16) if len(call) > 1 else None}


async def blocked(trace, policy, label):
    end = time.monotonic() + 2.0
    while time.monotonic() < end:
        if trace.tid is not None:
            obs = proc_observation(trace.tid)
            expected = trace.resources["selector" if policy == "control_pipe" else "data_r"]["fd"]
            nr = 22 if policy == "control_pipe" else 63
            wchan = "__arm64_sys_epoll_pwait" if policy == "control_pipe" else "anon_pipe_read"
            if obs["state"] == "S" and obs["syscall_nr"] == nr and obs["fd"] == expected and obs["wchan"] == wchan:
                trace.emit("blocked_observed", label=label, observation=obs)
                return
        await asyncio.sleep(0.001)
    raise RuntimeError("STOP: no frozen OS blocked witness: " + label)


async def finished(future):
    end = time.monotonic() + 2.0
    while not future.done() and time.monotonic() < end:
        await asyncio.sleep(0.001)
    if not future.done():
        raise RuntimeError("STOP: callable did not finish within watchdog")


async def trial(policy, condition):
    trace = Trace()
    r, w = trace.pipe("data")
    control = trace.pipe("control") if policy == "control_pipe" else None
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="owned-pipe")
    task = None
    future = None
    failure = None
    checkpoint = None
    final = None
    wrapper_ready = asyncio.Event()

    def reader():
        selector = None
        try:
            if control:
                selector = selectors.DefaultSelector()
                with trace.lock:
                    trace.resources["selector"] = {"fd": selector.fileno(), "closed": False}
                    trace.emit("fd_owned", resource="selector", fd=selector.fileno())
                selector.register(r, selectors.EVENT_READ, "data")
                selector.register(control[0], selectors.EVENT_READ, "control")
            with trace.lock:
                trace.active = True
                trace.tid = threading.get_native_id()
                trace.emit("worker_enter", tid=trace.tid)
            if selector:
                keys = [key.data for key, _ in selector.select()]
                trace.emit("selector_ready", ready=sorted(keys))
                if "control" in keys:
                    data = os.read(control[0], 1)
                    trace.emit("control_ack", hex=data.hex())
                    return {"kind": "stopped", "hex": data.hex()}
            data = os.read(r, 1)
            trace.emit("read_return", hex=data.hex())
            return {"kind": "data", "hex": data.hex()}
        finally:
            with trace.lock:
                if not trace.resources["data_r"]["closed"]:
                    trace.close("data_r", "worker")
                if control:
                    trace.close("control_r", "worker")
                if selector:
                    entry = trace.resources["selector"]
                    selector.close()
                    entry["closed"] = True
                    trace.emit("fd_closed", resource="selector", fd=entry["fd"], actor="worker")
                trace.active = False
                trace.emit("worker_exit", tid=trace.tid)

    async def wrapper():
        trace.emit("wrapper_wait")
        wrapper_ready.set()
        try:
            value = await asyncio.wrap_future(future)
        except asyncio.CancelledError:
            trace.emit("wrapper_cancelled")
            raise
        trace.emit("wrapper_delivered", value=value)
        return value

    def write(fd, resource, purpose, byte):
        # Request is recorded before the syscall; worker ACK may precede return.
        trace.emit("write_requested", resource=resource, purpose=purpose, hex=byte.hex())
        count = os.write(fd, byte)
        trace.emit("write_return", resource=resource, purpose=purpose, count=count)
        if count != 1:
            raise RuntimeError("STOP: partial one-byte write")

    trace.emit("submit_requested")
    try:
        future = executor.submit(reader)
        trace.emit("submit_return")
        task = asyncio.create_task(wrapper())
        await asyncio.wait_for(wrapper_ready.wait(), 2.0)
        await blocked(trace, policy, "before_action")
        if condition == "cancel_blocked":
            trace.emit("cancel_requested")
            if not task.cancel():
                raise RuntimeError("STOP: cancel request not accepted")
            await asyncio.gather(task, return_exceptions=True)
            if policy == "close_reader":
                trace.close("data_r", "caller")
            elif policy == "control_pipe":
                write(control[1], "control_w", "primary_stop", b"C")
                await finished(future)
            if policy != "control_pipe":
                await blocked(trace, policy, "after_action")
            checkpoint = trace.snapshot(task, future)
            trace.emit("primary_checkpoint", state=checkpoint)
            if policy != "control_pipe":
                write(w, "data_w", "harness_release", b"D")
        else:
            write(w, "data_w", "primary_data", b"D")
            await asyncio.wait_for(task, 2.0)
            checkpoint = trace.snapshot(task, future)
            trace.emit("primary_checkpoint", state=checkpoint)
        await finished(future)
        value = future.result()
        trace.emit("future_collected", value=value)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
        trace.emit("trial_failure", **failure)
    finally:
        if future is not None and not future.done():
            try:
                if control:
                    write(control[1], "control_w", "emergency_cleanup", b"C")
                else:
                    write(w, "data_w", "emergency_cleanup", b"D")
                await finished(future)
            except BaseException as exc:
                trace.emit("cleanup_failure", type=type(exc).__name__, message=str(exc))
                # Outer process watchdog preserves partial output if shutdown blocks.
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        executor.shutdown(wait=True, cancel_futures=True)
        alive = trace.tid in [t.native_id for t in threading.enumerate()]
        trace.emit("executor_joined", thread_alive=alive)
        for name in ("data_r", "data_w", "control_r", "control_w"):
            if name in trace.resources and not trace.resources[name]["closed"]:
                trace.close(name, "harness")
        if task is not None and future is not None:
            final = trace.snapshot(task, future)
            trace.emit("final_checkpoint", state=final)
    return {"policy": policy, "condition": condition, "events": trace.events,
            "checkpoint": checkpoint, "final": final, "failure": failure}


def main():
    root = pathlib.Path(__file__).resolve().parent
    freeze = json.loads((root / "FREEZE.json").read_text())
    for name, expected in freeze["source_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("source pin mismatch: " + name)
    observed = {"python": platform.python_version(), "kernel": platform.release(), "machine": platform.machine(),
                "cpu_max": pathlib.Path("/sys/fs/cgroup/cpu.max").read_text().strip(),
                "memory_max": pathlib.Path("/sys/fs/cgroup/memory.max").read_text().strip()}
    if observed != freeze["environment"]:
        raise RuntimeError("STOP: environment mismatch")
    out = pathlib.Path(sys.argv[1])
    with out.open("x", encoding="utf-8") as stream:
        def append(record):
            line = json.dumps(record, sort_keys=True) + "\n"
            if stream.tell() + len(line.encode()) > 1048576:
                raise RuntimeError("STOP: output cap exceeded")
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        append({"record": "header", "allocation": ALLOCATION, "started_utc": utc(), "environment": observed,
                "freeze_sha256": hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest()})
        count = 0
        for policy in POLICIES:
            for condition in CONDITIONS:
                row = asyncio.run(trial(policy, condition))
                append({"record": "trial", "index": count, **row})
                count += 1
                if row["failure"] is not None:
                    append({"record": "footer", "ended_utc": utc(), "trials": count, "status": "STOP"})
                    return 2
        append({"record": "footer", "ended_utc": utc(), "trials": count, "status": "COMPLETE"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
