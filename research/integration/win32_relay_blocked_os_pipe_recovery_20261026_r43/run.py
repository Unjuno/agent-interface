"""One-shot public-relay Win32 cancellation under a genuinely blocked OS pipe."""
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
TARGET = "r42-owned-fixture"
VK_SHIFT = 0x10
sys.path.insert(0, str(ROOT))
from runtime.backends.win32_v1.backend import Win32Backend, virtual_key


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
        ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_request(stream, row):
    stream.write(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
    stream.flush()


def decode_body(row):
    content = (row.get("result") or {}).get("content") or []
    texts = [part["text"] for part in content if part.get("type") == "text"]
    if len(texts) != 1:
        raise RuntimeError("expected one JSON-text public relay response")
    return json.loads(texts[0])


def read_events(path):
    if not path.is_file():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            result.append(json.loads(line))
        except ValueError:
            continue
    return result


def native_state(hwnd):
    backend = Win32Backend({TARGET: hwnd})
    try:
        generation = backend.target_generation(TARGET)
        down = backend._key_down_state(virtual_key("SHIFT"), TARGET)
        witness = backend._last_state_query_witness
        return {"target_generation": generation, "shift_down": down,
            "state_query_witness": witness, "monotonic_ns": time.monotonic_ns(),
            "perf_counter_ns": time.perf_counter_ns()}
    finally:
        backend.close()


def pipe_state(stdout):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetNamedPipeInfo.argtypes = [wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetNamedPipeInfo.restype = wintypes.BOOL
    kernel32.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
        wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p]
    kernel32.PeekNamedPipe.restype = wintypes.BOOL
    handle = wintypes.HANDLE(msvcrt_handle(stdout.fileno()))
    flags = wintypes.DWORD()
    out_size = wintypes.DWORD()
    in_size = wintypes.DWORD()
    max_instances = wintypes.DWORD()
    named_ok = bool(kernel32.GetNamedPipeInfo(handle,
        ctypes.byref(flags), ctypes.byref(out_size),
        ctypes.byref(in_size), ctypes.byref(max_instances)))
    available = wintypes.DWORD()
    peek_ok = bool(kernel32.PeekNamedPipe(handle, None, 0, None,
        ctypes.byref(available), None))
    return {"get_named_pipe_info_ok": named_ok,
        "pipe_flags": flags.value, "outbound_buffer_bytes": out_size.value,
        "inbound_buffer_bytes": in_size.value, "peek_ok": peek_ok,
        "available_bytes": available.value,
        "full_by_reported_capacity": bool(named_ok and peek_ok and out_size.value
            and available.value >= out_size.value),
        "observed_perf_counter_ns": time.perf_counter_ns()}


def msvcrt_handle(fd):
    import msvcrt
    return msvcrt.get_osfhandle(fd)


def pump_lines(stdout, buffered, wanted, deadline):
    import msvcrt
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
        wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p]
    kernel32.PeekNamedPipe.restype = wintypes.BOOL
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(stdout.fileno()))
    found = {}
    while not wanted.issubset(found) and time.monotonic() < deadline:
        available = wintypes.DWORD()
        if kernel32.PeekNamedPipe(handle, None, 0, None,
                ctypes.byref(available), None) and available.value:
            chunk = os.read(stdout.fileno(), min(available.value, 65536))
            buffered.extend(chunk)
            while b"\n" in buffered:
                line, _, rest = buffered.partition(b"\n")
                buffered[:] = rest
                if line:
                    row = json.loads(line.decode("utf-8"))
                    found[row["id"]] = row
        else:
            time.sleep(.002)
    return found


def run():
    if RUN.exists():
        raise FileExistsError(f"immutable output path already exists: {RUN}")
    RUN.mkdir(parents=True)
    (RUN / "fixture").mkdir()
    (RUN / "server").mkdir()
    meta = RUN / "fixture" / "meta.json"
    effect = RUN / "fixture" / "effect.json"
    events = RUN / "fixture" / "events.jsonl"
    target_file = RUN / "targets.json"
    relay_events = RUN / "relay-events.jsonl"
    writes_log = RUN / "stdout-writes.jsonl"
    fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta), "--effect", str(effect), "--events", str(events)]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), env.get("PYTHONPATH", "")])
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsWindowEnabled.argtypes = [wintypes.HWND]
    user32.IsWindowEnabled.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
        wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    original_foreground = int(user32.GetForegroundWindow() or 0)
    fixture = None
    relay = None
    stdin = None
    stdout = None
    buffered = bytearray()
    target_hwnd = None
    attempt = {"attempt_id": "win32-public-relay-os-pipe-r43-20261026",
        "source_commit": "4aaeeb9c211ddc32799d5f5af048d1fb9c341510",
        "classification": "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
        "wslc_used": False, "docker_used": False}
    started = time.monotonic_ns()
    next_id = 1
    call_id = None
    cancel_sent = False
    ordinary_ids = []
    queued_id = None
    cancel_id = None
    try:
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(RUN / "fixture" / "stdout.bin").open("wb"),
            stderr=(RUN / "fixture" / "stderr.bin").open("wb"), env=env)
        end = time.monotonic() + 10
        while not meta.exists() and fixture.poll() is None and time.monotonic() < end:
            time.sleep(.02)
        if fixture.poll() is not None or not meta.exists():
            raise RuntimeError("owned fixture failed to become ready")
        target_hwnd = json.loads(meta.read_text(encoding="utf-8"))["hwnd"]
        if type(target_hwnd) is not int or not user32.IsWindow(wintypes.HWND(target_hwnd)):
            raise RuntimeError("fresh fixture HWND failed validation")
        targets = {TARGET: target_hwnd}
        target_file.write_text(json.dumps(targets), encoding="utf-8")
        focus_deadline = time.monotonic() + 30
        while (int(user32.GetForegroundWindow() or 0) != target_hwnd
                and fixture.poll() is None and time.monotonic() < focus_deadline):
            time.sleep(.02)
        preflight = native_state(target_hwnd)
        foreground = int(user32.GetForegroundWindow() or 0)
        attempt.update({"fixture_pid": fixture.pid, "target_hwnd": target_hwnd,
            "original_foreground_hwnd": original_foreground,
            "preflight": preflight, "foreground_preflight_hwnd": foreground})
        if (foreground != target_hwnd or preflight["shift_down"] is not False
                or preflight["target_generation"] is None
                or not user32.IsWindowVisible(wintypes.HWND(target_hwnd))
                or not user32.IsWindowEnabled(wintypes.HWND(target_hwnd))):
            raise RuntimeError("fresh fixture/foreground/SHIFT-up gate failed; no input sent")

        child = PACKET / "relay_child.py"
        relay_cmd = [sys.executable, str(child), "--targets", str(target_file),
            "--output-directory", str(RUN / "server"), "--events", str(writes_log)]
        relay = subprocess.Popen(relay_cmd, cwd=ROOT, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=(RUN / "relay-stderr.bin").open("wb"), bufsize=0)
        stdin, stdout = relay.stdin, relay.stdout

        observe = {"id": next_id, "tool": "interface_observe", "arguments": {
            "target": TARGET, "frame": "window_client", "region": [0, 0, 400, 180]}}
        write_request(stdin, observe)
        first = pump_lines(stdout, buffered, {next_id}, time.monotonic() + 10)[next_id]
        first_body = decode_body(first)
        receipt = first_body.get("receipt") or {}
        report = ((receipt.get("source") or {}).get("raw_report") or first_body)
        if report.get("target_generation") != preflight["target_generation"]:
            raise RuntimeError("public relay observation generation mismatch")
        next_id += 1
        program = {"schema": "agent-interface/program-v1",
            "program_id": "r42-held-shift-during-stdout-pressure",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {TARGET: preflight["target_generation"]}},
            "authority": {"lease_id": "r42-one-shot",
                "expires_at_ns": time.monotonic_ns() + 15_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": TARGET},
                {"op": "key_state", "key": "SHIFT", "down": True},
                {"op": "wait_update", "timeout_ms": 8000},
                {"op": "key_state", "key": "SHIFT", "down": False},
                {"op": "release_all"}]}
        dispatch_id = next_id
        write_request(stdin, {"id": dispatch_id, "tool": "interface_dispatch",
            "arguments": {"program": program, "current_observation_seq": 1,
                "current_binding_revision": 1, "wait_for_result_ms": 0}})
        dispatch_row = pump_lines(stdout, buffered, {dispatch_id}, time.monotonic() + 10)[dispatch_id]
        dispatch_body = decode_body(dispatch_row)
        call_id = dispatch_body.get("call_id")
        attempt["dispatch_response"] = dispatch_body
        attempt["call_id"] = call_id
        next_id += 1
        if not isinstance(call_id, str) or len(call_id) != 32:
            raise RuntimeError("public dispatch did not return an exact call ID")
        hold_deadline = time.monotonic() + 3
        held_state = native_state(target_hwnd)
        while held_state["shift_down"] is not True and time.monotonic() < hold_deadline:
            time.sleep(.005)
            held_state = native_state(target_hwnd)
        attempt["state_during_action"] = held_state
        if held_state["shift_down"] is not True:
            raise RuntimeError("SHIFT-down was not independently observed before pipe pressure")

        ordinary_ids = list(range(next_id, next_id + 16))
        for request_id in ordinary_ids:
            write_request(stdin, {"id": request_id, "tool": "interface_observe",
                "arguments": {"target": TARGET, "frame": "window_client",
                    "region": [0, 0, 400, 180]}})
        queued_id = next_id + 16
        cancel_id = next_id + 17
        write_request(stdin, {"id": queued_id, "tool": "interface_clock", "arguments": {}})
        write_request(stdin, {"id": cancel_id, "tool": "interface_cancel",
            "arguments": {"call_id": call_id}})
        cancel_sent = True
        attempt.update({"stdout_pressure_request_ids": ordinary_ids,
            "queued_ordinary_request_id": queued_id, "cancel_request_id": cancel_id,
            "cancel_sent": True,
            "cancel_sent_perf_counter_ns": time.perf_counter_ns()})

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        state_rows = []
        pipe_rows = []
        cancel_events = []
        started_writes = completed_writes = []
        gate_deadline = time.monotonic() + 6
        gate = False
        while time.monotonic() < gate_deadline:
            current_pipe = pipe_state(stdout)
            pipe_rows.append(current_pipe)
            current_state = native_state(target_hwnd)
            state_rows.append(current_state)
            child_events = read_events(writes_log)
            started_writes = [e for e in child_events if e.get("event") == "write_started"]
            completed_writes = [e for e in child_events if e.get("event") == "write_completed"]
            cancel_events = read_events(relay_events)
            sidecar_events = read_events(writes_log.with_name("relay-events.jsonl"))
            cancel_return = next((e for e in sidecar_events
                if e.get("event") == "interface_cancel_returned"), None)
            outstanding = len(started_writes) > len(completed_writes)
            if (cancel_return is not None and current_state["shift_down"] is False
                    and current_pipe["full_by_reported_capacity"] and outstanding):
                gate = True
                attempt["recovery_gate_state"] = current_state
                attempt["recovery_gate_pipe"] = current_pipe
                attempt["recovery_gate_cancel_return"] = cancel_return
                attempt["recovery_gate_outstanding_write_count"] = (
                    len(started_writes) - len(completed_writes))
                break
            time.sleep(.01)
        attempt["os_pipe_blocked_release_gate"] = gate
        attempt["pipe_observations_before_drain"] = pipe_rows
        attempt["input_state_observations_before_drain"] = state_rows
        attempt["stdout_write_events_before_drain"] = read_events(writes_log)
        attempt["relay_sidecar_events"] = read_events(writes_log.with_name("relay-events.jsonl"))
        if not gate:
            raise TimeoutError("did not observe recovery while a stdout write remained blocked on a full OS pipe")

        # Only after the release gate is frozen do we read/drain the OS pipe.
        response_ids = set(ordinary_ids + [queued_id, cancel_id])
        drained = pump_lines(stdout, buffered, response_ids, time.monotonic() + 15)
        attempt["drained_responses"] = {str(key): value for key, value in drained.items()}
        cancel_body = decode_body(drained[cancel_id])
        attempt["cancel_response"] = cancel_body
        next_id = cancel_id + 1
        write_request(stdin, {"id": next_id, "tool": "interface_results",
            "arguments": {"call_id": call_id}})
        result_row = pump_lines(stdout, buffered, {next_id}, time.monotonic() + 8)[next_id]
        retained = decode_body(result_row)
        attempt["retained_result"] = retained
        cancel_record = retained.get("cancellation") or {}
        final_state = native_state(target_hwnd)
        attempt["final_state"] = final_state
        attempt["final_recovery"] = cancel_record
        attempt["classification"] = ("PASS_OS_PIPE_BLOCKED_RELAY_RECOVERY" if
            gate and cancel_body.get("cancellation", {}).get("status") in {"pending", "recovered"}
            and cancel_record.get("status") == "recovered"
            and cancel_record.get("release_confirmed") is True
            and final_state.get("target_generation") == preflight["target_generation"]
            and final_state.get("shift_down") is False
            else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED")
    except BaseException as error:
        attempt["classification"] = "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED"
        attempt["error_type"] = type(error).__name__
        attempt["error"] = str(error)[:1000]
        # Keep caller custody explicit on every post-dispatch gate failure.
        # Cancel and query through the public relay before process teardown.
        if call_id is not None and relay is not None and relay.poll() is None:
            try:
                if not cancel_sent:
                    cancel_id = next_id
                    write_request(stdin, {"id": cancel_id, "tool": "interface_cancel",
                        "arguments": {"call_id": call_id}})
                    cancel_sent = True
                    next_id += 1
                    attempt["failure_path_cancel_sent"] = True
                response_ids = set(ordinary_ids)
                if queued_id is not None:
                    response_ids.add(queued_id)
                if cancel_id is not None:
                    response_ids.add(cancel_id)
                if response_ids:
                    drained = pump_lines(stdout, buffered, response_ids,
                        time.monotonic() + 15)
                    attempt["failure_path_drained_responses"] = {
                        str(key): value for key, value in drained.items()}
                results = []
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    request_id = next_id
                    next_id += 1
                    write_request(stdin, {"id": request_id,
                        "tool": "interface_results", "arguments": {"call_id": call_id}})
                    rows = pump_lines(stdout, buffered, {request_id},
                        min(deadline, time.monotonic() + 2))
                    if request_id not in rows:
                        results.append({"status": "response_unavailable",
                            "request_id": request_id})
                        break
                    body = decode_body(rows[request_id])
                    results.append(body)
                    call = body.get("call") or body.get("retained_call") or {}
                    action = call.get("action") or body.get("action") or {}
                    cancellation = body.get("cancellation") or call.get("cancellation") or {}
                    exact_receipt = (body.get("call_id") == call_id
                        or call.get("call_id") == call_id)
                    action_state = action.get("status")
                    if (exact_receipt and body.get("status") != "pending"
                            and action_state not in {None, "running", "queued", "pending", "starting"}
                            and cancellation.get("status") != "pending"):
                        break
                    time.sleep(.1)
                attempt["failure_path_exact_results"] = results
                last = results[-1] if results else {}
                last_call = last.get("call") or last.get("retained_call") or {}
                last_action = last_call.get("action") or last.get("action") or {}
                last_cancel = last.get("cancellation") or last_call.get("cancellation") or {}
                attempt["failure_path_result_terminal"] = bool(results) and (
                    (last.get("call_id") == call_id or last_call.get("call_id") == call_id)
                    and last.get("status") != "pending"
                    and last_action.get("status") not in {None, "running", "queued", "pending", "starting"}
                    and last_cancel.get("status") != "pending")
                close_id = next_id
                next_id += 1
                write_request(stdin, {"id": close_id, "tool": "interface_close", "arguments": {}})
                close_rows = pump_lines(stdout, buffered, {close_id}, time.monotonic() + 5)
                attempt["failure_path_close"] = (decode_body(close_rows[close_id])
                    if close_id in close_rows else {"status": "response_unavailable"})
            except BaseException as reconcile_error:
                attempt["failure_path_reconciliation_error"] = {
                    "type": type(reconcile_error).__name__,
                    "message": str(reconcile_error)[:1000]}
        if writes_log.is_file():
            attempt["stdout_write_events_at_failure"] = read_events(writes_log)
        sidecar = writes_log.with_name("relay-events.jsonl")
        if sidecar.is_file():
            attempt["relay_sidecar_events_at_failure"] = read_events(sidecar)
    finally:
        if target_hwnd and fixture is not None and fixture.poll() is None:
            try:
                state = native_state(target_hwnd)
                attempt["cleanup_state_before"] = state
                if state.get("shift_down") is True:
                    backend = Win32Backend({TARGET: target_hwnd})
                    try:
                        backend.key_state("SHIFT", False)
                        attempt["emergency_shift_up"] = True
                    finally:
                        backend.close()
                    attempt["cleanup_state_after_emergency"] = native_state(target_hwnd)
            except BaseException as error:
                attempt["cleanup_release_error"] = repr(error)
        if relay is not None and relay.poll() is None:
            try:
                if stdin is not None:
                    stdin.close()
                relay.wait(timeout=3)
            except BaseException:
                relay.terminate()
                try:
                    relay.wait(timeout=3)
                except BaseException:
                    relay.kill()
                    relay.wait(timeout=3)
        if fixture is not None and fixture.poll() is None:
            try:
                user32.PostMessageW(wintypes.HWND(target_hwnd), 0x0010, 0, 0)
                fixture.wait(timeout=5)
            except BaseException:
                fixture.terminate()
                fixture.wait(timeout=3)
        before_restore = int(user32.GetForegroundWindow() or 0)
        if original_foreground and user32.IsWindow(wintypes.HWND(original_foreground)):
            user32.SetForegroundWindow(wintypes.HWND(original_foreground))
        attempt["cleanup"] = {"fixture_exit_code": None if fixture is None else fixture.poll(),
            "foreground_before": original_foreground,
            "foreground_before_restore": before_restore,
            "foreground_after_restore": int(user32.GetForegroundWindow() or 0),
            "finished_monotonic_ns": time.monotonic_ns()}
        attempt["elapsed_ns"] = time.monotonic_ns() - started
        save(RUN / "result.json", attempt)
        rows = []
        for path in sorted(RUN.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                rows.append(f"{sha(path.read_bytes())}  {path.relative_to(RUN).as_posix()}\n")
        (RUN / "SHA256SUMS").write_text("".join(rows), encoding="utf-8", newline="\n")
        if relay is not None:
            if stdout is not None:
                stdout.close()
        if fixture is not None:
            for stream in (getattr(fixture, "stdout", None), getattr(fixture, "stderr", None)):
                if stream is not None:
                    stream.close()
    print(json.dumps({key: attempt.get(key) for key in (
        "attempt_id", "classification", "error_type", "error", "os_pipe_blocked_release_gate",
        "recovery_gate_pipe", "recovery_gate_state", "cleanup")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
