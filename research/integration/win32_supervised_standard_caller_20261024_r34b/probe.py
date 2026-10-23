"""One-shot public stdio-MCP trial of the supervised native Win32 caller."""
from __future__ import annotations

import asyncio
import base64
import ctypes
import datetime as dt
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
RAW = PACKET / "raw.json"
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
record = {
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": None,
    "source_tracked_tree_clean": None,
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "caller_kind": "mcp_stdio",
    "session_mode": "supervised-win32",
    "dispatch_attempts": 0,
    "probe_status": "UNKNOWN",
    "probe_pid": os.getpid(),
}
children = []
logs = []
sys.path.insert(0, str(ROOT))
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.IsWindow.restype = ctypes.c_int
user32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                ctypes.c_size_t, ctypes.c_ssize_t]
user32.PostMessageW.restype = ctypes.c_int
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.SetForegroundWindow.restype = ctypes.c_int
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                     ctypes.c_void_p, ctypes.c_uint32]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                  ctypes.c_size_t, ctypes.c_ssize_t]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = ctypes.c_int
user32.PostThreadMessageW.argtypes = [ctypes.c_uint32, ctypes.c_uint,
                                      ctypes.c_size_t, ctypes.c_ssize_t]
user32.PostThreadMessageW.restype = ctypes.c_int

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_QUIT = 0x0012
VK_Q = ord("Q")
LLKHF_INJECTED = 0x10
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                              ctypes.c_size_t, ctypes.c_ssize_t)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", ctypes.c_uint32), ("scanCode", ctypes.c_uint32),
                ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                ("dwExtraInfo", ctypes.c_size_t)]


class FrozenKeyHook:
    """One hook that passes injected Q-down then pauses the first Q-up."""
    def __init__(self):
        self.ready = threading.Event()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.trace = {"ready_ns": None, "callback_entry_ns": None,
                      "callback_return_ns": None, "thread_id": None,
                      "hook_handle": None, "error": None, "events": []}
        self.thread = threading.Thread(target=self._run,
                                       name="r05-owned-keyboard-hook", daemon=True)
        self.thread.start()
        if not self.ready.wait(5) or self.trace["error"]:
            raise RuntimeError(f"low-level hook failed to start: {self.trace}")

    def _run(self):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentThreadId.restype = ctypes.c_ulong
        self.trace["thread_id"] = int(kernel32.GetCurrentThreadId())
        hook_state = {"handle": None, "held_q_up": False}

        def callback(code, wparam, lparam):
            if code >= 0 and int(wparam) in (WM_KEYDOWN, WM_KEYUP):
                event = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if int(event.vkCode) == VK_Q and int(event.flags) & LLKHF_INJECTED:
                    row = {"message": int(wparam), "vk": int(event.vkCode),
                           "flags": int(event.flags),
                           "callback_entry_ns": time.perf_counter_ns()}
                    self.trace["events"].append(row)
                    if int(wparam) == WM_KEYDOWN:
                        self.trace["q_down_callback_ns"] = row["callback_entry_ns"]
                        next_result = user32.CallNextHookEx(
                            hook_state["handle"], code, wparam, lparam)
                        row["callback_return_ns"] = time.perf_counter_ns()
                        self.trace["q_down_callback_return_ns"] = row["callback_return_ns"]
                        return next_result
                    self.trace["q_up_callback_ns"] = row["callback_entry_ns"]
                    if not hook_state["held_q_up"]:
                        hook_state["held_q_up"] = True
                        self.trace.update(callback_entry_ns=row["callback_entry_ns"],
                                          vk=int(event.vkCode), flags=int(event.flags),
                                          held_message=WM_KEYUP)
                        self.entered.set()
                        self.release.wait(1.5)
                        row["callback_return_ns"] = time.perf_counter_ns()
                        self.trace["callback_return_ns"] = row["callback_return_ns"]
                    else:
                        next_result = user32.CallNextHookEx(
                            hook_state["handle"], code, wparam, lparam)
                        row["callback_return_ns"] = time.perf_counter_ns()
                        self.trace["recovery_q_up_callback_return_ns"] = row["callback_return_ns"]
                        return next_result
            return user32.CallNextHookEx(hook_state["handle"], code, wparam, lparam)

        callback_ref = HOOKPROC(callback)
        hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL,
                                        ctypes.cast(callback_ref, ctypes.c_void_p),
                                        None, 0)
        if not hook:
            self.trace["error"] = {"stage": "SetWindowsHookExW",
                                    "last_error": ctypes.get_last_error()}
            self.ready.set()
            return
        hook_state["handle"] = hook
        self.trace.update(hook_handle=int(hook), ready_ns=time.perf_counter_ns())
        self.ready.set()
        msg = wintypes.MSG()
        while True:
            status = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if status <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        unhooked = bool(user32.UnhookWindowsHookEx(hook))
        self.trace["unhook_return"] = unhooked
        self.trace["unhook_last_error"] = (None if unhooked else
                                             ctypes.get_last_error())

    def stop(self):
        self.release.set()
        if self.trace.get("thread_id"):
            user32.PostThreadMessageW(self.trace["thread_id"], WM_QUIT, 0, 0)
        self.thread.join(2)
        self.trace["thread_exited"] = not self.thread.is_alive()


def observe_exact_process_exit(identity, timeout_s):
    """Wait on an exact PID/creation-time process object and retain the witness."""
    if (type(identity) is not dict or type(identity.get("pid")) is not int
            or type(identity.get("creation_time_100ns")) is not int):
        return {"status": "unknown", "reason": "producer_identity_missing"}
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x00100000 | 0x1000, False, identity["pid"])
    if not handle:
        return {"status": "unknown", "reason": "OpenProcess_failed",
                "last_error": ctypes.get_last_error()}
    try:
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(handle, ctypes.byref(creation),
                                        ctypes.byref(exit_time), ctypes.byref(kernel),
                                        ctypes.byref(user)):
            return {"status": "unknown", "reason": "GetProcessTimes_failed",
                    "last_error": ctypes.get_last_error()}
        creation_ns100 = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        if creation_ns100 != identity["creation_time_100ns"]:
            return {"status": "unknown", "reason": "producer_creation_time_mismatch",
                    "observed_creation_time_100ns": creation_ns100}
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            wait = kernel32.WaitForSingleObject(handle, 0)
            if wait == 0:
                return {"status": "exited", "pid": identity["pid"],
                        "creation_time_100ns": creation_ns100,
                        "observed_monotonic_ns": time.perf_counter_ns()}
            if wait != 0x102:
                return {"status": "unknown", "reason": "WaitForSingleObject_failed",
                        "wait_result": int(wait), "last_error": ctypes.get_last_error()}
            time.sleep(0.001)
        return {"status": "unknown", "reason": "producer_exit_timeout",
                "pid": identity["pid"], "creation_time_100ns": creation_ns100}
    finally:
        kernel32.CloseHandle(handle)


def _readback_child(hwnd, expected_generation, connection):
    """Fresh process independently binds the HWND and samples VK_Q state."""
    backend = None
    try:
        from runtime.backends.win32_v1.backend import Win32Backend
        started_ns = time.perf_counter_ns()
        backend = Win32Backend({"fixture": int(hwnd)})
        before = backend.target_generation("fixture")
        down = backend._key_down_state(VK_Q, "fixture")
        witness = list(backend._last_state_query_witness)
        after = backend.target_generation("fixture")
        connection.send({"status": "observed", "started_monotonic_ns": started_ns,
            "returned_monotonic_ns": time.perf_counter_ns(),
            "expected_generation": expected_generation,
            "generation_before": before, "generation_after": after,
            "q_down": down, "state_witness": witness,
            "pid": os.getpid()})
    except BaseException as error:
        try:
            connection.send({"status": "unknown", "error": repr(error),
                             "pid": os.getpid()})
        except BaseException:
            pass
    finally:
        if backend is not None:
            backend.close()
        connection.close()


def independent_readback(hwnd, generation, timeout_s):
    context = multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_readback_child,
                              args=(hwnd, generation, send), daemon=True)
    process.start()
    send.close()
    try:
        if not receive.poll(timeout_s):
            process.terminate()
            process.join(1)
            return {"status": "unknown", "reason": "readback_timeout",
                    "pid": process.pid}
        result = receive.recv()
        process.join(1)
        result["exit_code"] = process.exitcode
        result["process_retired"] = not process.is_alive()
        return result
    finally:
        receive.close()
        if process.is_alive():
            process.terminate()
            process.join(1)
        process.close()


def parse_response(reply):
    item = next(block for block in reply.content
                if getattr(block, "type", None) == "text")
    return json.loads(item.text)


def save_content(blocks):
    content = []
    for block in blocks:
        kind = getattr(block, "type", None)
        if kind == "text":
            content.append({"type": "text", "text": block.text})
        elif kind == "image":
            data = block.data
            content.append({"type": "image", "mimeType": block.mimeType,
                            "data_b64": data if isinstance(data, str)
                            else base64.b64encode(data).decode("ascii")})
        else:
            content.append({"type": str(kind), "repr": repr(block)})
    return content


def source_preflight():
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT, text=True).strip()
    record["source_commit"] = commit
    record["source_tracked_tree_clean"] = not tracked
    if commit != CONDITIONS["source_commit"] or tracked:
        raise RuntimeError("source commit mismatch or tracked source is dirty")


def client_rect(hwnd):
    from ctypes import wintypes
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect")
    width, height = int(rect.right - rect.left), int(rect.bottom - rect.top)
    if width <= 70 or height <= 70:
        raise RuntimeError("owned fixture client area is too small for frozen click")
    return {"left": int(rect.left), "top": int(rect.top),
            "right": int(rect.right), "bottom": int(rect.bottom),
            "width": width, "height": height}


def start_fixture():
    folder = RUN / "fixture"
    folder.mkdir(parents=True)
    meta, effect, events = (folder / name for name in
                            ("fixture-meta.json", "effect.json", "events.jsonl"))
    log_path = folder / "fixture.log"
    log = log_path.open("wb")
    logs.append(log)
    process = subprocess.Popen(
        [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
         "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    row = {"pid": process.pid, "meta_path": str(meta), "effect_path": str(effect),
           "events_path": str(events), "log_path": str(log_path)}
    children.append((process, row))
    deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["fixture_ready"]
    while time.monotonic() < deadline and not meta.exists():
        if process.poll() is not None:
            raise RuntimeError(f"owned fixture exited before ready: {process.returncode}")
        time.sleep(0.025)
    if not meta.exists():
        raise TimeoutError("owned fixture did not become ready")
    row["meta"] = json.loads(meta.read_text(encoding="utf-8"))
    row["hwnd"] = int(row["meta"]["hwnd"])
    from runtime.backends.win32_v1.backend import Win32Backend
    backend = Win32Backend({"fixture": row["hwnd"]})
    try:
        row["target_identity"] = {
            "owner": backend._window_owner_identity_for_hwnd(row["hwnd"]),
            "generation": backend.target_generation("fixture"),
        }
    finally:
        backend.close()
    row["client_rect"] = client_rect(row["hwnd"])
    if row["target_identity"]["owner"]["pid"] != process.pid:
        raise RuntimeError("fixture HWND owner did not match the owned process")
    return process, row


def close_fixture(process, row):
    hwnd = row.get("hwnd")
    row["close_posted"] = bool(hwnd is not None
        and user32.PostMessageW(hwnd, 0x0010, 0, 0))
    try:
        process.wait(timeout=CONDITIONS["timeouts_seconds"]["fixture_close"])
    except subprocess.TimeoutExpired:
        row["terminate_attempted"] = True
        process.terminate()
        try:
            process.wait(timeout=CONDITIONS["timeouts_seconds"]["owned_process_terminate"])
        except subprocess.TimeoutExpired:
            row["kill_attempted"] = True
            process.kill()
            process.wait(timeout=CONDITIONS["timeouts_seconds"]["owned_process_terminate"])
    row["exit_code"] = process.returncode
    row["window_exists_after_exit"] = bool(user32.IsWindow(hwnd)) if hwnd else None
    event_path = Path(row["events_path"])
    row["events"] = ([json.loads(line) for line in
        event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if event_path.exists() else [])
    effect_path = Path(row["effect_path"])
    row["effect"] = (json.loads(effect_path.read_text(encoding="utf-8"))
        if effect_path.exists() else None)


def restore_foreground(hwnd):
    exists = bool(hwnd and user32.IsWindow(hwnd))
    if not exists:
        return {"attempted": False, "restored": False,
                "prior_hwnd_exists": False,
                "reason": "prior_window_unavailable"}
    set_result = bool(user32.SetForegroundWindow(hwnd))
    observed = int(user32.GetForegroundWindow() or 0)
    return {"attempted": True, "prior_hwnd_exists": True,
            "set_foreground_return": set_result,
            "observed_hwnd": observed, "restored": observed == int(hwnd)}


async def run_public_calls(targets_path, fixture_row, key_hook):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    calls_path = RUN / "calls"
    server_env = os.environ.copy()
    trace_path = RUN / "cancellation_call_trace.jsonl"
    server_env["AGENT_INTERFACE_CANCEL_TRACE"] = str(trace_path)
    server_env["AGENT_INTERFACE_REPO_ROOT"] = str(ROOT)
    old_pythonpath = server_env.get("PYTHONPATH", "")
    server_env["PYTHONPATH"] = str(PACKET / "instrumentation") + (os.pathsep + old_pythonpath if old_pythonpath else "")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets_path),
              "--output-directory", str(calls_path),
              "--session-mode", "supervised-win32"],
        cwd=str(ROOT), env=server_env)
    timeout = CONDITIONS["timeouts_seconds"]
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), timeout["mcp_initialize"])
            tools = await asyncio.wait_for(client.list_tools(), timeout["mcp_initialize"])
            record["tools"] = sorted(tool.name for tool in tools.tools)
            clock_reply = await asyncio.wait_for(
                client.call_tool("interface_clock", {}), timeout["mcp_initialize"])
            clock_body = parse_response(clock_reply)
            record["clock"] = clock_body
            observe_start = time.perf_counter_ns()
            observed = await asyncio.wait_for(client.call_tool("interface_observe", {
                "target": "fixture", "frame": "window_client",
                "region": [0, 0, fixture_row["client_rect"]["width"],
                            fixture_row["client_rect"]["height"]]}),
                timeout["observe"])
            observe_end = time.perf_counter_ns()
            observe_body = parse_response(observed)
            raw_observation = (observe_body.get("receipt", {}).get("source", {})
                               .get("raw_report", {}))
            record["public_observation"] = {
                "started_monotonic_ns": observe_start,
                "returned_monotonic_ns": observe_end,
                "is_error": observed.isError, "response": observe_body,
                "raw_report": raw_observation,
                "content": save_content(observed.content)}
            generation = raw_observation.get("target_generation")
            if not isinstance(generation, str):
                raise RuntimeError("public observation did not return target_generation")

            trial = CONDITIONS["trial"]
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": trial["program_id"],
                "source": {
                    "observation_seq": trial["admission"]["observation_seq"],
                    "binding_revision": trial["admission"]["binding_revision"],
                    "target_generations": {"fixture": generation},
                },
                "authority": {
                    "lease_id": trial["lease_id"],
                    "expires_at_ns": clock_body["monotonic_ns"]
                        + trial["lease_duration_seconds"] * 1_000_000_000,
                },
                "terminal": {"release_all_required": True},
                "ops": trial["operations"],
            }
            record["program"] = program
            validation_start = time.perf_counter_ns()
            validation = await asyncio.wait_for(
                client.call_tool("interface_validate", {"program": program}),
                timeout["validate"])
            validation_end = time.perf_counter_ns()
            record["public_validation"] = {
                "started_monotonic_ns": validation_start,
                "returned_monotonic_ns": validation_end,
                "is_error": validation.isError,
                "response": parse_response(validation),
                "content": save_content(validation.content)}
            if (validation.isError
                    or record["public_validation"]["response"].get("static_valid") is not True):
                return

            record["dispatch_attempts"] = 1
            dispatch_start = time.perf_counter_ns()
            dispatched = await asyncio.wait_for(client.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": trial["admission"]["observation_seq"],
                "current_binding_revision": trial["admission"]["binding_revision"],
                "wait_for_result_ms": trial["wait_for_result_ms"],
            }), timeout["dispatch_response"])
            dispatch_end = time.perf_counter_ns()
            dispatch_envelope = parse_response(dispatched)
            dispatch_body = (((dispatch_envelope.get("receipt") or {}).get("source")
                              or {}).get("raw_report"))
            if not isinstance(dispatch_body, dict):
                dispatch_body = dispatch_envelope
            call_id = dispatch_body.get("call_id")
            record["public_dispatch"] = {
                "is_error": dispatched.isError,
                "wait_for_result_ms": trial["wait_for_result_ms"],
                "started_monotonic_ns": dispatch_start,
                "returned_monotonic_ns": dispatch_end,
                "response": dispatch_body,
                "response_envelope": dispatch_envelope,
                "content": save_content(dispatched.content),
            }
            if not isinstance(call_id, str):
                raise RuntimeError("zero-wait dispatch did not return its call ID")
            record["blocked_call_id"] = call_id
            hook_wait_start = time.perf_counter_ns()
            hook_deadline = time.monotonic() + timeout["hook_entry"]
            poll_interval = trial["hook_status_poll_interval_ms"] / 1000
            status_polls = []
            hook_entered = False
            while time.monotonic() < hook_deadline:
                if key_hook.entered.is_set():
                    hook_entered = True
                    break
                poll_start = time.perf_counter_ns()
                poll_reply = await asyncio.wait_for(client.call_tool(
                    "interface_results", {"call_id": call_id}),
                    timeout["poll_response"])
                poll_end = time.perf_counter_ns()
                poll_body = parse_response(poll_reply)
                poll_row = (poll_body.get("result") if isinstance(
                    poll_body.get("result"), dict) else poll_body)
                poll_action = poll_row.get("action", {}) if isinstance(poll_row, dict) else {}
                poll_cancel = poll_row.get("cancellation") or {} if isinstance(poll_row, dict) else {}
                status_polls.append({
                    "started_monotonic_ns": poll_start,
                    "returned_monotonic_ns": poll_end,
                    "is_error": poll_reply.isError,
                    "status": poll_body.get("status"),
                    "error": poll_body.get("error"),
                    "operation_invoked": poll_body.get("operation_invoked"),
                    "call_id": poll_body.get("call_id"),
                    "action_status": poll_action.get("status"),
                    "operation_id": poll_action.get("operation_id"),
                    "input_dispatched": poll_row.get("input_dispatched"),
                    "cancellation_status": poll_cancel.get("status"),
                })
                if key_hook.entered.is_set():
                    hook_entered = True
                    break
                if poll_action.get("status") in ("completed", "recovered", "unknown"):
                    break
                remaining = hook_deadline - time.monotonic()
                if remaining <= 0:
                    break
                await asyncio.wait_for(asyncio.to_thread(
                    key_hook.entered.wait, min(poll_interval, remaining)),
                    min(poll_interval, remaining) + 0.2)
            record["hook_wait"] = {
                "started_monotonic_ns": hook_wait_start,
                "ended_monotonic_ns": time.perf_counter_ns(),
                "entered": bool(hook_entered),
                "poll_interval_ms": trial["hook_status_poll_interval_ms"],
                "status_polls": status_polls,
                "hook_trace": dict(key_hook.trace),
            }
            if hook_entered:
                baseline = await asyncio.wait_for(asyncio.to_thread(
                    independent_readback, fixture_row["hwnd"], generation,
                    timeout["independent_readback"]),
                    timeout["independent_readback"] + 1)
                record["pre_cancel_independent_readback"] = baseline
                if (baseline.get("status") != "observed"
                        or baseline.get("q_down") is not True
                        or baseline.get("generation_before") != generation
                        or baseline.get("generation_after") != generation):
                    record["pre_cancel_gate"] = "STOP_Q_DOWN_NOT_INDEPENDENTLY_CONFIRMED"
                    key_hook.release.set()
                    return
                before_cancel = await asyncio.wait_for(client.call_tool(
                    "interface_results", {"call_id": call_id}),
                    timeout["cancel_response"])
                record["pre_cancel_status_readback"] = parse_response(before_cancel)
                cancel_start = time.perf_counter_ns()
                cancelled = await asyncio.wait_for(client.call_tool(
                    "interface_cancel", {"call_id": call_id}), timeout["cancel_response"])
                cancel_end = time.perf_counter_ns()
                record["public_cancel"] = {
                    "started_monotonic_ns": cancel_start,
                    "returned_monotonic_ns": cancel_end,
                    "elapsed_ms": (cancel_end - cancel_start) / 1_000_000,
                    "is_error": cancelled.isError,
                    "response": parse_response(cancelled),
                    "content": save_content(cancelled.content),
                }
                cancel_body = record["public_cancel"]["response"]
                cancellation_record = cancel_body.get("cancellation", {})
                owner_result = cancellation_record.get("result", {})
                producer_identity = owner_result.get("producer_identity")
                record["producer_identity_from_cancel"] = producer_identity
                hold_ms = trial.get("post_cancel_hook_hold_ms", 0)
                if hold_ms > 0:
                    hold_started = time.perf_counter_ns()
                    hold_deadline = time.monotonic() + hold_ms / 1000
                    hold_polls = []
                    blocked_readback_task = None
                    readback_due_ns = (hold_started
                        + trial.get("post_cancel_readback_delay_ms", 700) * 1_000_000)
                    readback_start_ns = None
                    while time.monotonic() < hold_deadline:
                        if (blocked_readback_task is None
                                and time.perf_counter_ns() >= readback_due_ns):
                            readback_start_ns = time.perf_counter_ns()
                            blocked_readback_task = asyncio.create_task(asyncio.to_thread(
                                independent_readback, fixture_row["hwnd"], generation,
                                timeout["independent_readback"]))
                        poll_started = time.perf_counter_ns()
                        poll_reply = await asyncio.wait_for(client.call_tool(
                            "interface_results", {"call_id": call_id}),
                            timeout["poll_response"])
                        poll_returned = time.perf_counter_ns()
                        poll_body = parse_response(poll_reply)
                        poll_row = (poll_body.get("result") if isinstance(
                            poll_body.get("result"), dict) else poll_body)
                        poll_cancel = (poll_row.get("cancellation") or {}) if isinstance(
                            poll_row, dict) else {}
                        poll_action = poll_row.get("action", {}) if isinstance(
                            poll_row, dict) else {}
                        poll_cancel_result = poll_cancel.get("result", {})
                        hold_polls.append({
                            "started_monotonic_ns": poll_started,
                            "returned_monotonic_ns": poll_returned,
                            "is_error": poll_reply.isError,
                            "status": poll_body.get("status"),
                            "call_id": poll_row.get("call_id"),
                            "action_status": poll_action.get("status"),
                            "cancellation_status": poll_cancel.get("status"),
                            "cancellation_release_confirmed": poll_cancel.get(
                                "release_confirmed"),
                            "owner_release_confirmed": poll_cancel_result.get(
                                "release_confirmed"),
                        })
                        await asyncio.sleep(trial.get("hold_poll_delay_ms", 10) / 1000)
                    if blocked_readback_task is None:
                        readback_start_ns = time.perf_counter_ns()
                        blocked_readback_task = asyncio.create_task(asyncio.to_thread(
                            independent_readback, fixture_row["hwnd"], generation,
                            timeout["independent_readback"]))
                    hold_ended = time.perf_counter_ns()
                    record["post_cancel_io_hold"] = {
                        "target_hold_ms": hold_ms,
                        "started_monotonic_ns": hold_started,
                        "ended_monotonic_ns": hold_ended,
                        "hook_trace_before_release": dict(key_hook.trace),
                        "status_polls": hold_polls,
                        "independent_readback_started_ns": readback_start_ns,
                        "independent_readback_delay_ms": trial.get(
                            "post_cancel_readback_delay_ms", 700),
                        "independent_readback_completed_before_release":
                            blocked_readback_task.done(),
                    }
                    key_hook.release.set()
                    try:
                        record["blocked_io_independent_readback"] = await asyncio.wait_for(
                            blocked_readback_task,
                            timeout["independent_readback"] + 1)
                    except BaseException as error:
                        record["blocked_io_independent_readback"] = {
                            "status": "unknown", "error_type": type(error).__name__,
                            "error": str(error)}
                    record["post_cancel_io_hold"]["hook_trace_after_release"] = dict(
                        key_hook.trace)
                else:
                    key_hook.release.set()
                exit_start = time.perf_counter_ns()
                record["producer_exit_witness"] = await asyncio.wait_for(
                    asyncio.to_thread(observe_exact_process_exit, producer_identity,
                                      timeout["producer_exit"]),
                    timeout["producer_exit"] + 1)
                record["producer_exit_witness"]["wait_started_monotonic_ns"] = exit_start
            else:
                key_hook.release.set()
                status_reply = await asyncio.wait_for(client.call_tool(
                    "interface_results", {"call_id": call_id}), timeout["result_readback"])
                record["no_hook_status_readback"] = parse_response(status_reply)
            record["hook_trace_after_dispatch"] = dict(key_hook.trace)
            deadline = time.monotonic() + timeout["result_readback"]
            result_responses = []
            while isinstance(call_id, str) and time.monotonic() < deadline:
                result_start = time.perf_counter_ns()
                result_reply = await asyncio.wait_for(
                    client.call_tool("interface_results", {"call_id": call_id}), 5)
                result_end = time.perf_counter_ns()
                result_body = parse_response(result_reply)
                result_responses.append({"is_error": result_reply.isError,
                                         "started_monotonic_ns": result_start,
                                         "returned_monotonic_ns": result_end,
                                         "response": result_body})
                row = result_body.get("result") if isinstance(
                    result_body.get("result"), dict) else result_body
                cancellation = row.get("cancellation") or {}
                if (row.get("action", {}).get("status") in ("completed", "recovered", "unknown")
                        or cancellation.get("status") in ("recovered", "unknown")):
                    break
                await asyncio.sleep(0.05)
            record["result_readbacks"] = result_responses
            up_deadline = time.monotonic() + timeout["recovery_up_observation"]
            def distinct_recovery_q_up_seen():
                q_ups = [event for event in key_hook.trace.get("events", [])
                         if event.get("message") == WM_KEYUP
                         and event.get("vk") == VK_Q
                         and event.get("flags", 0) & LLKHF_INJECTED]
                return (len(q_ups) >= 2
                        and type(q_ups[0].get("callback_return_ns")) is int
                        and type(q_ups[1].get("callback_entry_ns")) is int
                        and q_ups[1]["callback_entry_ns"] > q_ups[0]["callback_return_ns"]
                        and type(q_ups[1].get("callback_return_ns")) is int)
            while time.monotonic() < up_deadline and not distinct_recovery_q_up_seen():
                await asyncio.sleep(0.005)
            record["distinct_recovery_q_up_wait"] = {
                "seen": distinct_recovery_q_up_seen(),
                "timeout_seconds": timeout["recovery_up_observation"],
                "hook_events": key_hook.trace.get("events", []),
            }
            record["hook_trace_after_recovery"] = dict(key_hook.trace)
            record["independent_readback"] = await asyncio.wait_for(
                asyncio.to_thread(independent_readback, fixture_row["hwnd"], generation,
                                  timeout["independent_readback"]),
                timeout["independent_readback"] + 1)
            call_dir = calls_path / str(call_id) if call_id else None
            report_path = call_dir / "report.json" if call_dir else None
            record["retained_report"] = (
                json.loads(report_path.read_text(encoding="utf-8"))
                if report_path is not None and report_path.exists() else None)

            effect_path = Path(fixture_row["effect_path"])
            readback_deadline = time.monotonic() + timeout["effect_readback"]
            while time.monotonic() < readback_deadline and not effect_path.exists():
                await asyncio.sleep(0.02)
            record["effect_readback"] = (
                json.loads(effect_path.read_text(encoding="utf-8"))
                if effect_path.exists() else None)
            close_deadline = time.monotonic() + timeout["close_drain"]
            close_attempts = []
            close_reply = None
            while time.monotonic() < close_deadline:
                close_start = time.perf_counter_ns()
                close_reply = await asyncio.wait_for(
                    client.call_tool("interface_close", {}),
                    timeout["close_response"])
                close_end = time.perf_counter_ns()
                close_body = parse_response(close_reply)
                close_attempts.append({
                    "started_monotonic_ns": close_start,
                    "returned_monotonic_ns": close_end,
                    "is_error": close_reply.isError,
                    "response": close_body,
                    "content": save_content(close_reply.content),
                })
                if close_body.get("status") != "busy":
                    break
                remaining = close_deadline - time.monotonic()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(
                    trial["close_retry_interval_ms"] / 1000, remaining))
            record["public_close_attempts"] = close_attempts
            record["public_close"] = close_attempts[-1] if close_attempts else None
            session_id = ((record.get("retained_report") or {}).get("session") or {}).get(
                "session_id")
            close_report_path = (calls_path / f"session-{session_id}-close.json"
                                 if isinstance(session_id, str) else None)
            record["session_close_report"] = (
                json.loads(close_report_path.read_text(encoding="utf-8"))
                if close_report_path is not None and close_report_path.exists() else None)


def main():
    if sys.platform != "win32":
        raise SystemExit("native Win32 attempt requires Windows")
    source_preflight()
    for path in (RUN, RAW, PACKET / "audit.json", PACKET / "SHA256SUMS"):
        if path.exists():
            raise SystemExit(f"one-shot output already exists; refusing to overwrite: {path}")
    if not CONDITIONS["trial"]["operations"]:
        raise SystemExit("frozen input program unexpectedly empty")
    RUN.mkdir()
    process = None
    fixture = None
    hook = None
    previous_foreground = int(user32.GetForegroundWindow() or 0)
    record["previous_foreground_hwnd"] = previous_foreground
    try:
        process, fixture = start_fixture()
        record["fixture"] = fixture
        targets = RUN / "targets.json"
        targets.write_text(json.dumps({"fixture": fixture["hwnd"]}, sort_keys=True)
                           + "\n", encoding="utf-8")
        hook = FrozenKeyHook()
        record["hook_started"] = dict(hook.trace)
        asyncio.run(asyncio.wait_for(
            run_public_calls(targets, fixture, hook),
            CONDITIONS["timeouts_seconds"]["attempt_total"]))
        hook.stop()
        record["hook_stopped"] = dict(hook.trace)
        effect_deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["effect_readback"]
        effect_path = Path(fixture["effect_path"])
        while time.monotonic() < effect_deadline and not effect_path.exists():
            time.sleep(0.02)
        close_fixture(process, fixture)
        record["probe_status"] = ("completed_with_independent_effect"
            if fixture.get("effect") == CONDITIONS["trial"]["expected_effect"]
            else "completed_without_expected_effect")
    except BaseException as error:
        record["error"] = {"type": type(error).__name__, "detail": str(error)}
        record["probe_status"] = "FAIL_OR_UNKNOWN"
        for owned_process, owned_row in children:
            if owned_process.poll() is None:
                try:
                    close_fixture(owned_process, owned_row)
                except BaseException as cleanup_error:
                    record["cleanup_error"] = {
                        "type": type(cleanup_error).__name__,
                        "detail": str(cleanup_error)}
    finally:
        if hook is not None:
            hook.stop()
            record["hook_stopped"] = dict(hook.trace)
        if children:
            record["foreground_restore"] = restore_foreground(previous_foreground)
        trace_path = RUN / "cancellation_call_trace.jsonl"
        if trace_path.exists():
            record["cancellation_call_trace"] = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        record["conditions_sha256"] = hashlib.sha256((PACKET / "conditions.json").read_bytes()).hexdigest()
        record["ended_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False)
                       + "\n", encoding="utf-8")
        for log in logs:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
