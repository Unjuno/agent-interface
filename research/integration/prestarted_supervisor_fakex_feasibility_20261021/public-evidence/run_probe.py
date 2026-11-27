"""Construction-only process-start/deadline probe against a loopback Fake X oracle."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import socket
import socketserver
import threading
import time
import uuid
from pathlib import Path


HERE = Path(__file__).resolve().parent


class _FakeXState:
    def __init__(self):
        self.lock = threading.Lock()
        self.generation = None
        self.keys_down = set()
        self.accepted = []
        self.decisions = []

    def reset(self, generation):
        with self.lock:
            self.generation = generation
            self.keys_down = {"a"}
            self.accepted = []
            self.decisions = []

    def handle(self, row):
        with self.lock:
            now_ns = time.monotonic_ns()
            if row.get("op") == "reset":
                self.generation = row["generation"]
                self.keys_down = {"a"}
                self.accepted = []
                self.decisions = []
                return {"ok": True, "observed_ns": now_ns}
            if row.get("op") == "observe":
                return {
                    "ok": True,
                    "observed_ns": now_ns,
                    "generation": self.generation,
                    "keys_down": sorted(self.keys_down),
                    "accepted": list(self.accepted),
                    "decisions": list(self.decisions),
                }
            if row.get("op") == "key_release":
                reason = None
                if row.get("generation") != self.generation:
                    reason = "stale_generation"
                elif now_ns > row.get("deadline_ns", -1):
                    reason = "expired_deadline"
                elif row.get("key") not in self.keys_down:
                    reason = "key_not_down"
                if reason is not None:
                    decision = {
                        "request_id": row.get("request_id"),
                        "accepted": False,
                        "reason": reason,
                        "observed_ns": now_ns,
                    }
                    self.decisions.append(decision)
                    return {"ok": True, **decision}
                self.keys_down.remove(row["key"])
                event = {
                    "request_id": row["request_id"],
                    "kind": "KeyRelease",
                    "key": row["key"],
                    "generation": row["generation"],
                    "accepted_ns": now_ns,
                }
                self.accepted.append(event)
                return {"ok": True, "accepted": True, **event}
            raise ValueError("unknown Fake X operation")


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline()
        row = json.loads(raw.decode("utf-8"))
        result = self.server.fake_state.handle(row)
        self.wfile.write(json.dumps(result, sort_keys=True).encode("utf-8") + b"\n")


class _FakeXServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.fake_state = _FakeXState()


def _fake_x_call(address, row):
    with socket.create_connection(address, timeout=2.0) as connection:
        stream = connection.makefile("rwb")
        stream.write(json.dumps(row, sort_keys=True).encode("utf-8") + b"\n")
        stream.flush()
        response = json.loads(stream.readline().decode("utf-8"))
    return response


def _fake_x_worker(address, request, response_connection):
    started_ns = time.monotonic_ns()
    if started_ns > request["deadline_ns"]:
        result = _fake_x_call(address, {
            "op": "key_release",
            **request,
        })
        result["worker_decision"] = "attempted_after_deadline"
    else:
        result = _fake_x_call(address, {
            "op": "key_release",
            **request,
        })
        result["worker_decision"] = "attempted_before_deadline"
    result["worker_started_ns"] = started_ns
    result["worker_finished_ns"] = time.monotonic_ns()
    try:
        response_connection.send(result)
    finally:
        response_connection.close()


def _slow_start(process, delay_ms):
    # Keep the injection in the parent process. Replacing Process.start with a
    # local closure makes the Process object unpicklable under Windows spawn.
    time.sleep(delay_ms / 1000.0)
    process.start()


def _supervisor(command_receive, result_send, ready_send, address):
    context = multiprocessing.get_context("spawn")
    try:
        ready_send.send({"status": "ready", "pid": multiprocessing.current_process().pid})
    finally:
        ready_send.close()
    while True:
        command = command_receive.recv()
        if command.get("op") == "stop":
            result_send.send({"status": "stopped"})
            break
        result_receive, result_child = context.Pipe(duplex=False)
        process = context.Process(
            target=_fake_x_worker,
            args=(address, command["request"], result_child),
            name="fake-x-release-worker",
        )
        try:
            _slow_start(process, command["launch_delay_ms"])
            result_child.close()
            if not result_receive.poll(5.0):
                worker_result = {"status": "unknown", "reason": "worker_result_timeout"}
            else:
                worker_result = result_receive.recv()
            process.join(1.0)
            result_send.send({
                "request_id": command["request"]["request_id"],
                "worker": worker_result,
                "worker_exitcode": process.exitcode,
                "worker_retired": not process.is_alive(),
                "supervisor_completed_ns": time.monotonic_ns(),
            })
        except BaseException as error:
            result_send.send({
                "request_id": command["request"]["request_id"],
                "status": "unknown",
                "reason": "supervisor_error",
                "error": repr(error),
            })
        finally:
            result_receive.close()
            try:
                result_child.close()
            except OSError:
                pass
    command_receive.close()
    result_send.close()


def _start_supervisor(context, address):
    command_receive, command_send = context.Pipe(duplex=False)
    result_receive, result_send = context.Pipe(duplex=False)
    ready_receive, ready_send = context.Pipe(duplex=False)
    process = context.Process(
        target=_supervisor,
        args=(command_receive, result_send, ready_send, address),
        name="prestarted-fake-x-supervisor",
    )
    process.start()
    command_receive.close()
    result_send.close()
    ready_send.close()
    if not ready_receive.poll(5.0):
        process.terminate()
        process.join(1.0)
        raise RuntimeError("supervisor readiness deadline expired")
    ready = ready_receive.recv()
    ready_receive.close()
    if ready.get("status") != "ready":
        process.terminate()
        process.join(1.0)
        raise RuntimeError("supervisor readiness receipt malformed")
    return process, command_send, result_receive, ready


def _stop_supervisor(process, command_send, result_receive):
    if process.is_alive():
        command_send.send({"op": "stop"})
        if result_receive.poll(2.0):
            result_receive.recv()
        process.join(2.0)
    if process.is_alive():
        process.terminate()
        process.join(1.0)
    command_send.close()
    result_receive.close()


def _new_request(trial_id, generation, deadline_ns):
    return {
        "request_id": trial_id,
        "generation": generation,
        "key": "a",
        "deadline_ns": deadline_ns,
    }


def _run_sync_slow(context, address, state, trial, conditions):
    generation = "current-" + uuid.uuid4().hex
    state.reset(generation)
    start_ns = time.monotonic_ns()
    deadline_ns = start_ns + conditions["caller_deadline_ms"] * 1_000_000
    request = _new_request(trial, generation, deadline_ns)
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_fake_x_worker, args=(address, request, send))
    _slow_start(process, conditions["launch_delay_ms"])
    send.close()
    completed_before_return = receive.poll(2.0)
    worker_result = receive.recv() if completed_before_return else None
    process.join(1.0)
    response_ns = time.monotonic_ns()
    readback = _fake_x_call(address, {"op": "observe"})
    receive.close()
    return {
        "trial_id": trial,
        "arm": "synchronous-delayed-start",
        "started_ns": start_ns,
        "deadline_ns": deadline_ns,
        "response_ns": response_ns,
        "response_ms": (response_ns - start_ns) / 1_000_000,
        "deadline_met": response_ns <= deadline_ns,
        "worker": worker_result,
        "worker_exitcode": process.exitcode,
        "worker_retired": not process.is_alive(),
        "independent_fake_x_readback": readback,
    }


def _run_supervised(context, address, state, trial, arm, conditions, *, stale=False):
    process, command_send, result_receive, ready = _start_supervisor(context, address)
    current_generation = "current-" + uuid.uuid4().hex
    state.reset(current_generation)
    requested_generation = ("stale-" + uuid.uuid4().hex
                            if stale else current_generation)
    start_ns = time.monotonic_ns()
    deadline_ns = start_ns + conditions["caller_deadline_ms"] * 1_000_000
    request = _new_request(trial, requested_generation, deadline_ns)
    command_send.send({
        "op": "release",
        "request": request,
        "launch_delay_ms": conditions["launch_delay_ms"],
    })
    received_before_deadline = result_receive.poll(
        max(0.0, (deadline_ns - time.monotonic_ns()) / 1_000_000_000))
    caller_response_ns = time.monotonic_ns()
    caller_response = result_receive.recv() if received_before_deadline else None
    if caller_response is None:
        caller_status = "unknown_timeout"
    else:
        caller_status = "received_worker_result"
    completed_after_deadline = False
    if caller_response is None:
        if result_receive.poll(5.0):
            caller_response = result_receive.recv()
            completed_after_deadline = True
        else:
            caller_response = {"status": "unknown", "reason": "supervisor_completion_timeout"}
    readback = _fake_x_call(address, {"op": "observe"})
    row = {
        "trial_id": trial,
        "arm": arm,
        "supervisor_ready": ready,
        "started_ns": start_ns,
        "deadline_ns": deadline_ns,
        "caller_response_ns": caller_response_ns,
        "caller_response_ms": (caller_response_ns - start_ns) / 1_000_000,
        "caller_deadline_met": caller_response_ns <= deadline_ns,
        "caller_status_at_deadline": caller_status,
        "supervisor_result_arrived_after_deadline": completed_after_deadline,
        "supervisor_result": caller_response,
        "independent_fake_x_readback": readback,
    }
    _stop_supervisor(process, command_send, result_receive)
    return row


def _audit(rows, conditions):
    by_arm = {}
    for row in rows:
        by_arm.setdefault(row["arm"], []).append(row)
    failures = []
    expected_counts = {
        "synchronous-delayed-start": 3,
        "prestarted-supervisor-delayed-start": 3,
        "prestarted-supervisor-fast-control": 3,
        "prestarted-supervisor-stale-generation": 3,
    }
    for arm, count in expected_counts.items():
        if len(by_arm.get(arm, [])) != count:
            failures.append("%s: expected %s trials, got %s" % (
                arm, count, len(by_arm.get(arm, []))))
    for row in by_arm.get("synchronous-delayed-start", []):
        if row["deadline_met"]:
            failures.append(row["trial_id"] + ": synchronous arm unexpectedly met deadline")
        readback = row["independent_fake_x_readback"]
        if readback["keys_down"] != ["a"] or readback["accepted"]:
            failures.append(row["trial_id"] + ": expired synchronous worker changed Fake X state")
        if not row["worker"] or row["worker"].get("reason") != "expired_deadline":
            failures.append(row["trial_id"] + ": synchronous worker did not refuse after deadline")
    for row in by_arm.get("prestarted-supervisor-delayed-start", []):
        if row["caller_response_ms"] > (
                conditions["caller_deadline_ms"] + conditions["response_slack_ms"]):
            failures.append(row["trial_id"] + ": prestarted caller exceeded deadline plus slack")
        if row["caller_status_at_deadline"] != "unknown_timeout":
            failures.append(row["trial_id"] + ": delayed supervisor did not return UNKNOWN at deadline")
        readback = row["independent_fake_x_readback"]
        if readback["keys_down"] != ["a"] or readback["accepted"]:
            failures.append(row["trial_id"] + ": delayed worker changed Fake X after deadline")
        worker = row["supervisor_result"].get("worker", {})
        if (worker.get("reason") != "expired_deadline"
                or row["supervisor_result"].get("worker_retired") is not True
                or row["supervisor_result"].get("worker_exitcode") != 0
                or not row["supervisor_result_arrived_after_deadline"]):
            failures.append(row["trial_id"] + ": delayed worker lacks expired-deadline refusal")
    for row in by_arm.get("prestarted-supervisor-fast-control", []):
        readback = row["independent_fake_x_readback"]
        if (not row["caller_deadline_met"] or row["caller_status_at_deadline"] != "received_worker_result"
                or readback["keys_down"] != [] or len(readback["accepted"]) != 1
                or readback["accepted"][0]["kind"] != "KeyRelease"
                or row["supervisor_result"].get("worker_retired") is not True
                or row["supervisor_result"].get("worker_exitcode") != 0):
            failures.append(row["trial_id"] + ": healthy release control did not complete and read back")
    for row in by_arm.get("prestarted-supervisor-stale-generation", []):
        readback = row["independent_fake_x_readback"]
        reasons = [item.get("reason") for item in readback["decisions"]]
        if (not row["caller_deadline_met"] or readback["keys_down"] != ["a"]
                or readback["accepted"] or reasons != ["stale_generation"]
                or row["supervisor_result"].get("worker_retired") is not True
                or row["supervisor_result"].get("worker_exitcode") != 0):
            failures.append(row["trial_id"] + ": stale generation was not independently refused")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def run():
    conditions = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
    context = multiprocessing.get_context("spawn")
    fake_x = _FakeXServer()
    fake_x.fake_state.reset("bootstrap")
    address = fake_x.server_address
    server_thread = threading.Thread(target=fake_x.serve_forever, daemon=True)
    server_thread.start()
    rows = []
    try:
        for index in range(conditions["arms"]["synchronous-delayed-start"]["trials"]):
            trial = "sync-slow-%02d" % (index + 1)
            rows.append(_run_sync_slow(
                context, address, fake_x.fake_state, trial,
                conditions["arms"]["synchronous-delayed-start"]))
        for index in range(conditions["arms"]["prestarted-supervisor-delayed-start"]["trials"]):
            trial = "supervised-slow-%02d" % (index + 1)
            rows.append(_run_supervised(
                context, address, fake_x.fake_state, trial,
                "prestarted-supervisor-delayed-start",
                conditions["arms"]["prestarted-supervisor-delayed-start"]))
        for index in range(conditions["arms"]["prestarted-supervisor-fast-control"]["trials"]):
            trial = "supervised-fast-%02d" % (index + 1)
            rows.append(_run_supervised(
                context, address, fake_x.fake_state, trial,
                "prestarted-supervisor-fast-control",
                conditions["arms"]["prestarted-supervisor-fast-control"]))
        for index in range(conditions["arms"]["prestarted-supervisor-stale-generation"]["trials"]):
            trial = "supervised-stale-%02d" % (index + 1)
            rows.append(_run_supervised(
                context, address, fake_x.fake_state, trial,
                "prestarted-supervisor-stale-generation",
                conditions["arms"]["prestarted-supervisor-stale-generation"],
                stale=True))
    finally:
        fake_x.shutdown()
        fake_x.server_close()
        server_thread.join(1.0)
    result = {
        "schema": "agent-interface/prestarted-supervisor-fakex-result-v1",
        "classification": conditions["classification"],
        "conditions_sha256": __import__("hashlib").sha256(
            (HERE / "conditions.json").read_bytes()).hexdigest(),
        "host": {
            "platform": __import__("platform").platform(),
            "python": __import__("sys").version,
            "clock": "time.monotonic_ns",
        },
        "fake_x": {
            "transport": "loopback JSON state oracle, not X11 protocol",
            "address": "127.0.0.1:%s" % address[1],
            "server_pid": __import__("os").getpid(),
        },
        "trials": rows,
        "audit": _audit(rows, conditions["arms"]["prestarted-supervisor-delayed-start"]),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    if result["audit"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
