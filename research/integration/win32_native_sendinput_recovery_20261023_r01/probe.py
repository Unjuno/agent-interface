"""One-shot real SendInput accepted-before-return recovery discriminator."""
from __future__ import annotations

import asyncio
import ctypes
import datetime as dt
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time
import traceback

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
sys.path.insert(0, str(ROOT))
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
RAW = PACKET / "raw.json"
RUN = PACKET / "run"
if sys.platform != "win32":
    raise SystemExit("native Win32 trial requires Windows")
if RAW.exists() or RUN.exists():
    raise SystemExit("frozen R01 output exists; refusing to overwrite")

from runtime.backends.win32_v1.backend import (  # noqa: E402
    INPUT_KEYBOARD, KEYEVENTF_KEYUP, VK_CONTROL, Win32Backend,
)
from runtime.guarded_win32_v1.operation_owner import OperationOwner  # noqa: E402
from runtime.guarded_win32_v1.process_cancellation import (  # noqa: E402
    OperationCancellationSupervisor,
)

LIVE_FIXTURES = []
LIVE_PRODUCERS = []
LIVE_SUPERVISORS = []
LIVE_CLEANUP = []


def _trace(trace, lock, kind, **fields):
    with lock:
        trace.append({"kind": kind, "monotonic_ns": time.monotonic_ns(), **fields})


def _process_identity(process):
    """Read identity through the retained multiprocessing process handle."""
    popen = getattr(process, "_popen", None)
    handle = getattr(popen, "_handle", None)
    if handle is None or type(getattr(process, "pid", None)) is not int:
        raise RuntimeError("retained Windows process handle is unavailable")
    from ctypes import wintypes
    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME))
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    creation, exit_time, kernel_time, user_time = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not kernel32.GetProcessTimes(wintypes.HANDLE(int(handle)),
                                    ctypes.byref(creation), ctypes.byref(exit_time),
                                    ctypes.byref(kernel_time), ctypes.byref(user_time)):
        raise ctypes.WinError(ctypes.get_last_error())
    created = (int(creation.high) << 32) | int(creation.low)
    if created <= 0:
        raise RuntimeError("Windows returned an invalid process creation time")
    return {"pid": process.pid, "creation_time_100ns": created}


class _Response:
    def __init__(self, connection):
        self.connection = connection

    def send(self, value):
        self.connection.send(value)

    def close(self):
        return None


def _helper_server(connection, name, handler, args):
    connection.send({"status": "ready", "helper": name})
    response = _Response(connection)
    while True:
        request = connection.recv()
        if request is None:
            return
        handler(request, response, *args)
        connection.send({"control": "operation_complete",
                         "request_id": request["request_id"]})


def _helper_factory(context, name, handler, args):
    def factory():
        parent, child = context.Pipe(duplex=True)
        process = context.Process(target=_helper_server,
            args=(child, name, handler, tuple(args)), daemon=True)
        return process, parent
    return factory


def _recovery_handler(request, response, hwnd, event_queue):
    from runtime.backends.win32_v1.backend import Win32Backend, VK_CONTROL
    started = time.monotonic_ns()
    backend = Win32Backend({"fixture": int(hwnd)})
    generation = backend.target_generation("fixture")
    foreground = int(backend.user32.GetForegroundWindow() or 0)
    identity_ok = generation == request["target_generation"]
    foreground_ok = foreground == int(hwnd)
    release = None
    if identity_ok and foreground_ok:
        # The frozen supervisor obligation, rather than the producer's mutable
        # ledger, supplies the one possible held CTRL release after retirement.
        backend.held_keys["CTRL"] = VK_CONTROL
        backend.held_key_targets["CTRL"] = "fixture"
        release = backend.release_all()
    accepted = (release is not None and release.get("verified") is True
                and release.get("keys_down") == []
                and release.get("buttons_down") == []
                and release.get("keys_unknown") == []
                and release.get("buttons_unknown") == [])
    detail = {
        "kind": "recovery", "monotonic_ns": started,
        "ended_ns": time.monotonic_ns(), "foreground_hwnd": foreground,
        "foreground_ok": foreground_ok, "generation": generation,
        "generation_ok": identity_ok, "release_receipt": release,
        "release_accepted": accepted,
    }
    event_queue.put(detail)
    response.send({"operation_id": request["operation_id"],
        "target_generation": request["target_generation"],
        "recovery_id": request["recovery_id"],
        "release_accepted": accepted, "release_receipt": release,
        "foreground_ok": foreground_ok, "generation_ok": identity_ok})


def _observer_handler(request, response, hwnd, event_queue):
    from runtime.backends.win32_v1.backend import Win32Backend, VK_CONTROL
    backend = Win32Backend({"fixture": int(hwnd)})
    started = time.monotonic_ns()
    horizon_ns = int(CONDITIONS["cleanup"]["late_down_observation_horizon_ms"] * 1_000_000)
    interval_s = CONDITIONS["cleanup"]["late_down_poll_interval_ms"] / 1000.0
    deadline = started + horizon_ns
    samples = []
    while True:
        now = time.monotonic_ns()
        generation = backend.target_generation("fixture")
        foreground = int(backend.user32.GetForegroundWindow() or 0)
        state = backend._key_down_state(VK_CONTROL, "fixture")
        witness = getattr(backend, "_last_state_query_witness", None)
        samples.append({"monotonic_ns": now, "state": state,
                        "generation": generation, "foreground_hwnd": foreground,
                        "witness": witness})
        if now >= deadline:
            break
        time.sleep(min(interval_s, max(0.0, (deadline - now) / 1_000_000_000)))
    neutral = (len(samples) >= 2
        and all(item["state"] is False for item in samples)
        and all(item["generation"] == request["target_generation"] for item in samples)
        and all(item["foreground_hwnd"] == int(hwnd) for item in samples)
        and all(item["witness"] for item in samples))
    result = {"kind": "observer", "started_ns": started,
        "ended_ns": time.monotonic_ns(), "horizon_ns": horizon_ns,
        "sample_count": len(samples), "neutral": neutral,
        "samples": samples}
    event_queue.put(result)
    response.send({"operation_id": request["operation_id"],
        "target_generation": request["target_generation"],
        "recovery_id": request["recovery_id"], "neutral": neutral,
        "sample_count": len(samples), "horizon_ns": horizon_ns})


def _producer(mode, hwnd, start_gate, connection):
    from runtime.backends.win32_v1.backend import INPUT_KEYBOARD, KEYEVENTF_KEYUP, VK_CONTROL, Win32Backend
    if not start_gate.wait(5):
        connection.send({"phase": "start_gate_timeout", "monotonic_ns": time.monotonic_ns()})
        return
    backend = Win32Backend({"fixture": int(hwnd)})
    backend.focus("fixture")
    if int(backend.user32.GetForegroundWindow() or 0) != int(hwnd):
        connection.send({"phase": "focus_mismatch", "monotonic_ns": time.monotonic_ns()})
        while True:
            time.sleep(0.02)
    real_send = backend._send
    def stalled_send(item):
        is_ctrl_down = (item.type == INPUT_KEYBOARD
                        and item.ki.wVk == VK_CONTROL
                        and not (item.ki.dwFlags & KEYEVENTF_KEYUP))
        if not is_ctrl_down:
            return real_send(item)
        if mode == "blocked-before-native-call":
            connection.send({"phase": "before_native_call",
                             "monotonic_ns": time.monotonic_ns()})
        else:
            real_send(item)  # real user32.SendInput; returns only after accept
            connection.send({"phase": "sendinput_accepted",
                             "monotonic_ns": time.monotonic_ns(),
                             "accepted_emissions": backend.emissions})
        while True:
            time.sleep(0.02)
    # Instance-level hook blocks around one exact call; no replacement of the
    # Windows API and no other operation can send input in this child.
    backend._send = stalled_send
    backend.key_state("CTRL", True)


def _start_fixture(label):
    folder = RUN / label
    folder.mkdir(parents=True)
    meta, effect, events = (folder / name for name in
        ("fixture-meta.json", "effect.json", "events.jsonl"))
    log_path = folder / "fixture.log"
    log = log_path.open("wb")
    process = subprocess.Popen([sys.executable,
        "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    row = {"label": label, "pid": process.pid, "meta_path": str(meta),
        "effect_path": str(effect), "events_path": str(events),
        "log_path": str(log_path), "started_ns": time.monotonic_ns()}
    LIVE_FIXTURES.append(row)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not meta.exists():
        if process.poll() is not None:
            log.close()
            LIVE_FIXTURES.remove(row)
            raise RuntimeError(f"fixture {label} exited before ready: {process.returncode}")
        time.sleep(0.02)
    if not meta.exists():
        process.terminate()
        process.wait(timeout=2)
        log.close()
        LIVE_FIXTURES.remove(row)
        raise TimeoutError(f"fixture {label} readiness timeout")
    row["meta"] = json.loads(meta.read_text(encoding="utf-8"))
    row["hwnd"] = int(row["meta"]["hwnd"])
    from runtime.backends.win32_v1.backend import Win32Backend
    backend = Win32Backend({"fixture": row["hwnd"]})
    row["target_generation"] = backend.target_generation("fixture")
    row["owner_identity"] = backend._window_owner_identity_for_hwnd(row["hwnd"])
    if row["owner_identity"].get("pid") != process.pid:
        raise RuntimeError("fixture HWND process owner mismatch")
    row["log_handle"] = log
    row["process"] = process
    return row


def _close_fixture(row):
    if row is None:
        return
    process = row["process"]
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = (ctypes.c_void_p, ctypes.c_uint,
                                    ctypes.c_size_t, ctypes.c_ssize_t)
    user32.PostMessageW.restype = ctypes.c_int
    user32.IsWindow.argtypes = (ctypes.c_void_p,)
    user32.IsWindow.restype = ctypes.c_int
    row["close_posted"] = bool(user32.PostMessageW(row["hwnd"], 0x0010, 0, 0))
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        row["terminate_attempted"] = True
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            row["kill_attempted"] = True
            process.kill()
            process.wait(timeout=2)
    row["exit_code"] = process.returncode
    row["window_exists_after_exit"] = bool(user32.IsWindow(row["hwnd"]))
    events = Path(row["events_path"])
    row["events"] = ([json.loads(x) for x in events.read_text(encoding="utf-8").splitlines() if x]
                      if events.exists() else [])
    effect = Path(row["effect_path"])
    row["effect"] = json.loads(effect.read_text(encoding="utf-8")) if effect.exists() else None
    row["closed_ns"] = time.monotonic_ns()
    row["log_handle"].close()
    row.pop("process", None)
    row.pop("log_handle", None)
    if row in LIVE_FIXTURES:
        LIVE_FIXTURES.remove(row)


def _observe_ctrl(backend):
    state = backend._key_down_state(VK_CONTROL, "fixture")
    return {"state": state,
            "foreground_hwnd": int(backend.user32.GetForegroundWindow() or 0),
            "witness": getattr(backend, "_last_state_query_witness", None),
            "monotonic_ns": time.monotonic_ns()}


def _run_schedule(context, owner, mode, index):
    fixture = _start_fixture(f"schedule-{index}")
    hwnd = fixture["hwnd"]
    generation = fixture["target_generation"]
    row = {"mode": mode, "fixture": {k: v for k, v in fixture.items()
                                      if k not in ("process", "log_handle")},
           "target_generation": generation, "timeline": []}
    backend = Win32Backend({"fixture": hwnd})
    initial = _observe_ctrl(backend)
    row["initial_ctrl_state"] = initial
    if initial["state"] is not False or initial["foreground_hwnd"] != hwnd or not initial["witness"]:
        row["status"] = "FAIL_OR_UNKNOWN"
        row["reason"] = "CTRL not independently confirmed up on the fixture input desktop before trial"
        _close_fixture(fixture)
        row["fixture"] = {k: v for k, v in fixture.items() if k not in ("process", "log_handle")}
        return row

    helper_events = context.Queue()
    operation_id = f"native-sendinput-r01-schedule-{index}"
    supervisor = OperationCancellationSupervisor(owner,
        recovery_process_factory=_helper_factory(context, "recovery", _recovery_handler,
                                                (hwnd, helper_events)),
        observer_process_factory=_helper_factory(context, "observer", _observer_handler,
                                                (hwnd, helper_events)),
        process_identity_reader=_process_identity,
        terminate_grace_s=0.25, kill_grace_s=0.25, poll_interval_s=0.005,
        startup_timeout_s=5.0)
    LIVE_SUPERVISORS.append((supervisor, owner, operation_id, generation))
    deadline_ns = time.monotonic_ns() + 20_000_000_000
    owner.admit(operation_id, generation, deadline_ns, ["CTRL"], start_gate_required=True)
    start_gate = context.Event()
    parent, child = context.Pipe(duplex=True)
    producer = context.Process(target=_producer, args=(mode, hwnd, start_gate, child), daemon=True)
    producer.start()
    LIVE_PRODUCERS.append(producer)
    identity = _process_identity(producer)
    if not supervisor.producer_started(operation_id, generation, producer,
                                       process_identity=identity):
        raise RuntimeError("owner refused exact producer identity")
    if not owner.authorize_producer_start(operation_id, generation, producer, start_gate.set):
        raise RuntimeError("owner refused producer start gate")

    process_exit_event = {"done": False}
    timeline_lock = threading.Lock()
    original_join = producer.join
    def monitored_join(timeout=None):
        result = original_join(timeout)
        if not process_exit_event["done"] and not producer.is_alive():
            process_exit_event["done"] = True
            _trace(row["timeline"], timeline_lock, "producer_exit_confirmed_by_join",
                   exitcode=producer.exitcode)
        return result
    producer.join = monitored_join

    trigger = None
    if parent.poll(4):
        trigger = parent.recv()
    row["producer_trigger"] = trigger
    row["timeline"].append({"kind": "trigger_received", "monotonic_ns": time.monotonic_ns()})
    row["state_before_cancel"] = _observe_ctrl(backend)
    cleanup_deadline = time.monotonic_ns() + 8_000_000_000
    cancel_started = time.monotonic_ns()
    row["cancel_response"] = supervisor.cancel(operation_id, generation,
                                                cleanup_deadline_ns=cleanup_deadline)
    row["cancel_returned_ns"] = time.monotonic_ns()
    row["cancel_response_ms"] = (row["cancel_returned_ns"] - cancel_started) / 1_000_000
    terminal_deadline = time.monotonic() + 8.0
    terminal = owner.result(operation_id)
    while terminal["status"] in {"cancel_pending", "producer_retired", "recovery_pending"}:
        if time.monotonic() >= terminal_deadline:
            break
        time.sleep(0.005)
        terminal = owner.result(operation_id)
    row["terminal"] = terminal
    row["terminal_ns"] = time.monotonic_ns()
    row["terminal_elapsed_ms"] = (row["terminal_ns"] - cancel_started) / 1_000_000
    if producer.is_alive():
        producer.terminate()
        producer.join(1.0)
    row["producer_exitcode"] = producer.exitcode
    row["producer_alive_after_terminal"] = producer.is_alive()
    try:
        producer.close()
    except Exception:
        pass
    if producer in LIVE_PRODUCERS:
        LIVE_PRODUCERS.remove(producer)
    child.close()
    parent.close()
    helper_details = []
    for _ in range(2):
        try:
            helper_details.append(helper_events.get(timeout=2))
        except Exception:
            break
    row["helper_events"] = sorted(helper_details,
                                  key=lambda item: item.get("monotonic_ns", item.get("started_ns", 0)))
    supervisor.close()
    for entry in list(LIVE_SUPERVISORS):
        if entry[0] is supervisor:
            LIVE_SUPERVISORS.remove(entry)
    helper_events.close()
    if process_exit_event["done"]:
        pass
    elif not row["producer_alive_after_terminal"]:
        # Preserve an explicit parent observation if join instrumentation did
        # not run through the cancellation supervisor path.
        _trace(row["timeline"], timeline_lock, "producer_exit_confirmed_after_terminal",
               exitcode=row["producer_exitcode"])
    _close_fixture(fixture)
    row["fixture"] = {k: v for k, v in fixture.items() if k not in ("process", "log_handle")}
    row["status"] = "PASS" if (trigger and trigger.get("phase") ==
        ("before_native_call" if mode == "blocked-before-native-call" else "sendinput_accepted")
        and terminal.get("status") == "recovered"
        and row["producer_exitcode"] is not None
        and not row["producer_alive_after_terminal"]
        and row["cancel_response_ms"] <= 1000
        and row["terminal_elapsed_ms"] <= 8000) else "FAIL_OR_UNKNOWN"
    return row


def _content(reply):
    result = []
    for block in getattr(reply, "content", []):
        kind = getattr(block, "type", None)
        if kind == "text":
            result.append({"type": "text", "text": block.text})
        elif kind == "image":
            import base64
            data = block.data
            result.append({"type": "image", "mimeType": block.mimeType,
                           "data_b64": data if isinstance(data, str)
                           else base64.b64encode(data).decode("ascii")})
        else:
            result.append({"type": str(kind), "repr": repr(block)})
    return result


def _parse_response(reply):
    block = next(item for item in reply.content if getattr(item, "type", None) == "text")
    return json.loads(block.text)


async def _run_fresh_public_effect(fixture, record):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    hwnd = fixture["hwnd"]
    generation = fixture["target_generation"]
    targets = RUN / "fresh-effect-targets.json"
    calls = RUN / "fresh-effect-calls"
    targets.write_text(json.dumps({"fixture": hwnd}) + "\n", encoding="utf-8")
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(calls)], cwd=str(ROOT))
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await asyncio.wait_for(client.initialize(), timeout=10)
            tool_list = await asyncio.wait_for(client.list_tools(), timeout=10)
            record["public_tools"] = sorted(item.name for item in tool_list.tools)
            started = time.monotonic_ns()
            observed = await asyncio.wait_for(client.call_tool("interface_observe", {
                "target": "fixture", "frame": "window_client", "region": [0, 0, 300, 100]}), 15)
            ended = time.monotonic_ns()
            observation = _parse_response(observed)
            source_report = observation.get("receipt", {}).get("source", {}).get("raw_report", {})
            record["public_observation"] = {"is_error": observed.isError,
                "started_ns": started, "ended_ns": ended,
                "response": observation, "content": _content(observed)}
            if (observed.isError or source_report.get("target_generation") != generation
                    or source_report.get("target_generation_consistency") != "matched"):
                return
            text_value = CONDITIONS["task_effect"]["text"]
            program = {"schema": "agent-interface/program-v1",
                "program_id": "native-recovery-fresh-effect-r01",
                "source": {"observation_seq": 1, "binding_revision": 1,
                           "target_generations": {"fixture": generation}},
                "authority": {"lease_id": "native-recovery-r01",
                    "expires_at_ns": time.monotonic_ns() + 60_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [{"op": "focus", "target": "fixture"},
                    {"op": "text", "text": text_value},
                    {"op": "key_chord", "keys": ["CTRL", "S"]},
                    {"op": "release_all"}]}
            record["public_program"] = program
            validate_started = time.monotonic_ns()
            validated = await asyncio.wait_for(client.call_tool("interface_validate",
                {"program": program}), 10)
            validate_ended = time.monotonic_ns()
            validation = _parse_response(validated)
            record["public_validation"] = {"is_error": validated.isError,
                "started_ns": validate_started, "ended_ns": validate_ended,
                "response": validation, "content": _content(validated)}
            if validated.isError or validation.get("static_valid") is not True:
                return
            dispatch_started = time.monotonic_ns()
            dispatched = await asyncio.wait_for(client.call_tool("interface_dispatch", {
                "program": program, "current_observation_seq": 1,
                "current_binding_revision": 1}), 15)
            dispatch_ended = time.monotonic_ns()
            dispatch_response = _parse_response(dispatched)
            call_id = dispatch_response.get("call_id")
            report_path = calls / str(call_id) / "report.json" if call_id else None
            record["public_dispatch"] = {"is_error": dispatched.isError,
                "started_ns": dispatch_started, "ended_ns": dispatch_ended,
                "response": dispatch_response, "content": _content(dispatched),
                "raw_report": json.loads(report_path.read_text(encoding="utf-8"))
                    if report_path is not None and report_path.exists() else None}
            effect_path = Path(fixture["effect_path"])
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and not effect_path.exists():
                await asyncio.sleep(0.02)
            record["effect_readback_ns"] = time.monotonic_ns()
            if effect_path.exists():
                record["effect_readback"] = json.loads(effect_path.read_text(encoding="utf-8"))


def _run_fresh_effect(record):
    fixture = _start_fixture("fresh-effect")
    record["fresh_effect_fixture"] = {k: v for k, v in fixture.items()
                                      if k not in ("process", "log_handle")}
    try:
        asyncio.run(asyncio.wait_for(_run_fresh_public_effect(fixture, record), timeout=60))
    except BaseException as error:
        record["fresh_effect_error"] = {"type": type(error).__name__, "detail": str(error)}
        record["fresh_effect_traceback"] = traceback.format_exc()
    finally:
        _close_fixture(fixture)
        record["fresh_effect_fixture"] = {k: v for k, v in fixture.items()
                                          if k not in ("process", "log_handle")}


def main():
    if os.environ.get("SOURCE_COMMIT") != CONDITIONS["source_commit"]:
        raise SystemExit("SOURCE_COMMIT does not match frozen conditions")
    if RUN.exists() or RAW.exists():
        raise SystemExit("one-shot output exists; refusing to overwrite")
    RUN.mkdir(parents=True)
    record = {"schema": "win32-native-sendinput-recovery-raw-v1",
        "attempt_id": CONDITIONS["attempt_id"],
        "source_commit": os.environ["SOURCE_COMMIT"],
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform": platform.platform(), "python": sys.version,
        "scope": CONDITIONS["scope"], "status": "FAIL_OR_UNKNOWN",
        "schedules": []}
    active_fixture = None
    context = mp.get_context("spawn")
    owner = OperationOwner(clock_ns=time.monotonic_ns,
                           process_identity_reader=_process_identity)
    record["cleanup_errors"] = LIVE_CLEANUP
    try:
        for index, mode in enumerate(("blocked-before-native-call",
                                      "real-sendinput-accepted-before-backend-return"), 1):
            result = _run_schedule(context, owner, mode, index)
            record["schedules"].append(result)
            if result.get("status") != "PASS":
                break
        if len(record["schedules"]) == 2 and all(
                item.get("status") == "PASS" for item in record["schedules"]):
            previous_generations = {item["target_generation"] for item in record["schedules"]}
            _run_fresh_effect(record)
            fresh = record.get("fresh_effect_fixture", {})
            effect = record.get("effect_readback")
            dispatch = (record.get("public_dispatch", {}).get("raw_report") or {}).get("result", {})
            releases = dispatch.get("execution", {}).get("releases", [])
            release = releases[-1] if releases else {}
            expected = CONDITIONS["task_effect"]["expected"]
            effect_ok = (effect == expected and fresh.get("effect") == expected
                and len(fresh.get("events", [])) == len(expected["text"]) + 2
                and fresh.get("exit_code") == 0
                and fresh.get("window_exists_after_exit") is False
                and fresh.get("target_generation") not in previous_generations)
            release_ok = (release.get("verified") is True
                and release.get("keys_down") == [] and release.get("buttons_down") == []
                and release.get("keys_unknown", []) == []
                and release.get("buttons_unknown", []) == [])
            record["fresh_effect_checks"] = {"effect_exact": effect == expected,
                "effect_persists_after_close": fresh.get("effect") == expected,
                "event_count": len(fresh.get("events", [])),
                "expected_event_count": len(expected["text"]) + 2,
                "release_verified": release_ok,
                "fresh_generation": fresh.get("target_generation"),
                "previous_generations": sorted(previous_generations),
                "fixture_exit": fresh.get("exit_code"),
                "hwnd_gone": fresh.get("window_exists_after_exit") is False}
            record["status"] = "PASS" if effect_ok and release_ok else "FAIL_OR_UNKNOWN"
    except BaseException as error:
        record["error"] = {"type": type(error).__name__, "detail": str(error)}
        record["traceback"] = traceback.format_exc()
    finally:
        # Preserve custody through normal cancellation if the probe itself
        # faults after authorizing a producer. A repeated request for the same
        # operation is idempotent and cannot create a second recovery attempt.
        for supervisor, active_owner, operation_id, generation in list(LIVE_SUPERVISORS):
            try:
                status = active_owner.result(operation_id).get("status")
                if status in {"running", "cancel_pending", "producer_retired", "recovery_pending"}:
                    supervisor.cancel(operation_id, generation,
                        cleanup_deadline_ns=time.monotonic_ns() + 8_000_000_000)
                    deadline = time.monotonic() + 8.0
                    while time.monotonic() < deadline:
                        status = active_owner.result(operation_id).get("status")
                        if status not in {"cancel_pending", "producer_retired", "recovery_pending"}:
                            break
                        time.sleep(0.005)
            except BaseException as cleanup_error:
                LIVE_CLEANUP.append({"kind": "supervisor_cancel",
                    "type": type(cleanup_error).__name__, "detail": str(cleanup_error)})
        for producer in list(LIVE_PRODUCERS):
            try:
                if producer.is_alive():
                    producer.terminate()
                    producer.join(1.0)
                if producer.is_alive() and callable(getattr(producer, "kill", None)):
                    producer.kill()
                    producer.join(1.0)
                LIVE_CLEANUP.append({"kind": "producer_final_state", "pid": producer.pid,
                                     "exitcode": producer.exitcode,
                                     "alive": producer.is_alive()})
                if not producer.is_alive():
                    producer.close()
            except BaseException as cleanup_error:
                LIVE_CLEANUP.append({"kind": "producer_retire",
                    "type": type(cleanup_error).__name__, "detail": str(cleanup_error)})
        for supervisor, _active_owner, _operation_id, _generation in list(LIVE_SUPERVISORS):
            try:
                supervisor.close()
            except BaseException as cleanup_error:
                LIVE_CLEANUP.append({"kind": "supervisor_close",
                    "type": type(cleanup_error).__name__, "detail": str(cleanup_error)})
        for fixture in list(LIVE_FIXTURES):
            try:
                _close_fixture(fixture)
            except BaseException as cleanup_error:
                LIVE_CLEANUP.append({"kind": "fixture_close", "pid": fixture.get("pid"),
                    "type": type(cleanup_error).__name__, "detail": str(cleanup_error)})
        record["ended_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True,
                                  ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
