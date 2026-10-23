"""One-shot Windows experiment: retire a child blocked in native SendInput."""
from __future__ import annotations

import ctypes
import hashlib
import json
import multiprocessing as mp
import os
import pathlib
import platform
import queue
import struct
import sys
import threading
import time
import uuid
import winreg
from ctypes import wintypes

# Direct script execution puts this packet directory on sys.path, not the repo.
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from runtime.backends.win32_v1.backend import (
    INPUT, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP, Win32Backend,
)
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor

RAW = ROOT / "raw.json"
VK_F13 = 0x7C
WM_KEYDOWN = 0x0100
LLKHF_INJECTED = 0x10
HOOK_STALL_S = 0.200
CANCEL_DEADLINE_NS = 2_500_000_000
LRESULT = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", ctypes.c_uint32), ("scanCode", ctypes.c_uint32),
                ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                ("dwExtraInfo", ULONG_PTR)]


HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, ctypes.c_size_t,
                              ctypes.c_ssize_t)


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD),
                ("dwHighDateTime", wintypes.DWORD)]


class TimedProcess:
    """Parent-side timing wrapper retaining the exact multiprocessing handle."""
    def __init__(self, process, trace, name):
        self.inner, self.trace, self.name = process, trace, name

    @property
    def pid(self): return self.inner.pid
    @property
    def exitcode(self): return self.inner.exitcode
    @property
    def sentinel(self): return self.inner.sentinel
    def start(self): return self.inner.start()
    def is_alive(self): return self.inner.is_alive()
    def terminate(self):
        self.trace[self.name + "_terminate_ns"] = time.perf_counter_ns()
        return self.inner.terminate()
    def kill(self):
        self.trace[self.name + "_kill_ns"] = time.perf_counter_ns()
        return self.inner.kill()
    def join(self, timeout=None):
        result = self.inner.join(timeout)
        if not self.inner.is_alive():
            self.trace.setdefault(self.name + "_exit_observed_ns", time.perf_counter_ns())
            self.trace[self.name + "_exitcode"] = self.inner.exitcode
        return result
    def close(self): return self.inner.close()


class TraceConnection:
    def __init__(self, connection, trace, role):
        self.inner, self.trace, self.role = connection, trace, role
    def poll(self, timeout=0): return self.inner.poll(timeout)
    def send(self, value):
        self.trace.setdefault(self.role + "_requests", []).append(value)
        return self.inner.send(value)
    def recv(self):
        value = self.inner.recv()
        self.trace.setdefault(self.role + "_messages", []).append(value)
        return value
    def close(self): return self.inner.close()


def _process_identity(process):
    """Read creation time through this exact retained process handle."""
    handle_value = int(process.sentinel)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE,
        ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME)]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    creation, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not kernel32.GetProcessTimes(wintypes.HANDLE(handle_value),
            ctypes.byref(creation), ctypes.byref(exited),
            ctypes.byref(kernel), ctypes.byref(user)):
        raise OSError(ctypes.get_last_error(), "GetProcessTimes on retained process handle")
    created = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
    if created <= 0 or type(process.pid) is not int or process.pid <= 0:
        raise RuntimeError("invalid retained process identity")
    return {"pid": process.pid, "creation_time_100ns": created}


def _new_backend(hwnd):
    backend = Win32Backend({"fixture": int(hwnd)})
    backend.focused_target = "fixture"
    return backend


def _helper_server(connection, role, hwnd, expected_generation):
    connection.send({"status": "ready", "helper": role,
                     "pid": os.getpid(), "ready_ns": time.perf_counter_ns()})
    try:
        while True:
            request = connection.recv()
            if request is None:
                return
            started = time.perf_counter_ns()
            backend = _new_backend(hwnd)
            before = backend.target_generation("fixture")
            if role == "recovery":
                valid_request = (request.get("obligations") == ["key:VK_F13"]
                    and request.get("target_generation") == expected_generation
                    and before == expected_generation)
                release = None
                if valid_request:
                    backend.held_keys = {"VK_F13": VK_F13}
                    backend.held_key_targets = {"VK_F13": "fixture"}
                    release_started = time.perf_counter_ns()
                    release = backend.release_all()
                    release_returned = time.perf_counter_ns()
                else:
                    release_started = release_returned = None
                after = backend.target_generation("fixture")
                receipt = {
                    "operation_id": request.get("operation_id"),
                    "target_generation": request.get("target_generation"),
                    "recovery_id": request.get("recovery_id"),
                    "release_accepted": bool(valid_request and after == before
                        and isinstance(release, dict) and release.get("verified") is True),
                    "release": release, "helper_generation_before": before,
                    "helper_generation_after": after, "helper_started_ns": started,
                    "release_started_ns": release_started,
                    "release_returned_ns": release_returned,
                    "helper_pid": os.getpid(),
                }
            else:
                valid_request = (request.get("target_generation") == expected_generation
                                 and before == expected_generation)
                state = backend._key_down_state(VK_F13, "fixture") if valid_request else None
                witness = list(backend._last_state_query_witness)
                after = backend.target_generation("fixture")
                receipt = {
                    "operation_id": request.get("operation_id"),
                    "target_generation": request.get("target_generation"),
                    "recovery_id": request.get("recovery_id"),
                    "neutral": bool(valid_request and before == after and state is False),
                    "f13_down": state, "witness": witness,
                    "helper_generation_before": before,
                    "helper_generation_after": after,
                    "observed_ns": time.perf_counter_ns(), "helper_pid": os.getpid(),
                }
            backend.close()
            connection.send(receipt)
            connection.send({"control": "operation_complete",
                             "request_id": request.get("request_id")})
    except (EOFError, BrokenPipeError):
        return
    finally:
        connection.close()


def _producer_child(start_gate, event_queue, hwnd, target_generation):
    backend = _new_backend(hwnd)
    actual_generation = backend.target_generation("fixture")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p,
                                         ctypes.c_uint32]
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                      ctypes.c_size_t, ctypes.c_ssize_t]
    user32.CallNextHookEx.restype = LRESULT
    user32.GetMessageW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_uint, ctypes.c_uint]
    user32.GetMessageW.restype = ctypes.c_int
    user32.PeekMessageW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
    hook_state = {"handle": None, "entered": False}
    hook_ready = threading.Event()

    def hook_loop():
        msg = ctypes.create_string_buffer(48)
        user32.PeekMessageW(msg, None, 0, 0, 0)
        @HOOKPROC
        def callback(code, wparam, lparam):
            if code >= 0:
                event = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if (not hook_state["entered"] and int(event.vkCode) == VK_F13
                        and int(wparam) == WM_KEYDOWN
                        and int(event.flags) & LLKHF_INJECTED):
                    hook_state["entered"] = True
                    entry_ns = time.perf_counter_ns()
                    event_queue.put({"kind": "hook_entry", "pid": os.getpid(),
                        "vk": int(event.vkCode), "flags": int(event.flags),
                        "callback_entry_ns": entry_ns})
                    time.sleep(HOOK_STALL_S)
                    event_queue.put({"kind": "hook_return", "pid": os.getpid(),
                        "callback_return_ns": time.perf_counter_ns()})
            return user32.CallNextHookEx(hook_state["handle"], code, wparam, lparam)
        hook_state["callback"] = callback
        hook = user32.SetWindowsHookExW(13, callback, None, 0)
        if not hook:
            event_queue.put({"kind": "hook_setup_error", "last_error": ctypes.get_last_error()})
            hook_ready.set()
            return
        hook_state["handle"] = hook
        event_queue.put({"kind": "hook_ready", "pid": os.getpid(),
            "thread_id": threading.get_native_id(),
            "ready_ns": time.perf_counter_ns()})
        hook_ready.set()
        while True:
            result = int(user32.GetMessageW(msg, None, 0, 0))
            if result <= 0:
                break

    thread = threading.Thread(target=hook_loop, name="native-f13-hook", daemon=True)
    thread.start()
    if not hook_ready.wait(2.0) or not start_gate.wait(3.0):
        return
    if actual_generation != target_generation:
        event_queue.put({"kind": "generation_mismatch", "actual": actual_generation})
        return
    event_queue.put({"kind": "send_down_begin", "pid": os.getpid(),
                     "at_ns": time.perf_counter_ns(), "target_generation": actual_generation})
    item = INPUT(type=INPUT_KEYBOARD)
    item.ki = KEYBDINPUT(VK_F13, 0, 0, 0, 0)
    backend._send(item)
    event_queue.put({"kind": "send_down_return", "pid": os.getpid(),
                     "at_ns": time.perf_counter_ns()})
    # Hold the producer alive with the input obligation until the parent retires it.
    threading.Event().wait(10.0)


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", wintypes.POINT)]


def _configure_pump(user32):
    user32.PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND,
                                    wintypes.UINT, wintypes.UINT, wintypes.UINT]
    user32.PeekMessageW.restype = wintypes.BOOL
    user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
    user32.DispatchMessageW.restype = LRESULT


def _pump(user32):
    msg = MSG()
    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def _make_fixture(user32):
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR,
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU,
        wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
    style = 0x00CF0000 | 0x10000000  # WS_OVERLAPPEDWINDOW | WS_VISIBLE
    hwnd = user32.CreateWindowExW(0, "EDIT", "F13 recovery fixture",
        style, 24, 24, 420, 140, None, None, kernel32.GetModuleHandleW(None), None)
    if not hwnd:
        raise OSError(ctypes.get_last_error(), "CreateWindowExW EDIT fixture")
    user32.ShowWindow(hwnd, 5)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetFocus(hwnd)
    return int(hwnd)


def _wait_queue(event_queue, raw, user32, predicate, timeout_s):
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        _pump(user32)
        try:
            row = event_queue.get(timeout=0.01)
        except queue.Empty:
            continue
        raw["producer_events"].append(row)
        if predicate(row):
            return row
    return None


def _spawn_horizon_observer(ctx, hwnd, generation, target_name, after_ns, trace):
    parent, child = ctx.Pipe(duplex=True)
    process = ctx.Process(target=_horizon_observer,
        args=(child, hwnd, generation, target_name, after_ns), daemon=True)
    process.start()
    child.close()
    process.join(2.0)
    receipt = parent.recv() if parent.poll(0.1) else None
    trace["horizon_observer_exitcode"] = process.exitcode
    trace["horizon_observer_pid"] = process.pid
    parent.close()
    process.close()
    return receipt


def _horizon_observer(connection, hwnd, generation, target_name, after_ns):
    try:
        delay = max(0, after_ns - time.perf_counter_ns()) / 1_000_000_000
        if delay:
            time.sleep(delay)
        backend = _new_backend(hwnd)
        before = backend.target_generation(target_name)
        state = backend._key_down_state(VK_F13, target_name)
        witness = list(backend._last_state_query_witness)
        after = backend.target_generation(target_name)
        connection.send({"pid": os.getpid(), "observed_ns": time.perf_counter_ns(),
            "target_generation_before": before, "target_generation_after": after,
            "f13_down": state, "neutral": before == generation == after and state is False,
            "witness": witness})
        backend.close()
    except BaseException as error:
        connection.send({"pid": os.getpid(), "error": repr(error),
                         "observed_ns": time.perf_counter_ns()})
    finally:
        connection.close()


def main():
    if os.name != "nt" or struct.calcsize("P") != 8:
        raise SystemExit("This packet requires 64-bit Windows")
    if RAW.exists():
        raise SystemExit("raw.json exists; refusing to rerun or overwrite")
    ctx = mp.get_context("spawn")
    trace = {}
    raw = {"packet": ROOT.name, "started_ns": time.perf_counter_ns(),
        "host": {"platform": platform.platform(), "python": sys.version,
                 "pointer_bits": struct.calcsize("P") * 8},
        "producer_events": [], "errors": [], "cleanup": {},
        "operation_id": uuid.uuid4().hex}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                            0, winreg.KEY_READ) as key:
            raw["low_level_hooks_timeout_hkcu"] = winreg.QueryValueEx(
                key, "LowLevelHooksTimeout")[0]
    except FileNotFoundError:
        raw["low_level_hooks_timeout_hkcu"] = None
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _configure_pump(user32)
    old_foreground = int(user32.GetForegroundWindow() or 0)
    raw["old_foreground_hwnd"] = old_foreground
    hwnd = None
    backend = None
    supervisor = None
    producer = None
    event_queue = None
    start_gate = None
    helper_connections = []
    input_authorized = False
    cancel_requested = False
    recovery_attempted = False
    try:
        hwnd = _make_fixture(user32)
        raw["fixture_hwnd"] = hwnd
        raw["fixture_pid"] = os.getpid()
        raw["foreground_after_setup"] = int(user32.GetForegroundWindow() or 0)
        if raw["foreground_after_setup"] != hwnd:
            raw["errors"].append({"stage": "fixture_not_foreground"})
            return 2
        backend = _new_backend(hwnd)
        generation = backend.target_generation("fixture")
        raw["target_generation"] = generation
        raw["target_process_identity"] = backend.process_identity("fixture")
        initial_state = backend._key_down_state(VK_F13, "fixture")
        raw["initial_f13_down"] = initial_state
        raw["initial_state_witness"] = list(backend._last_state_query_witness)
        if initial_state is not False:
            raw["errors"].append({"stage": "initial_f13_not_confirmed_up"})
            return 2

        owner = OperationOwner(clock_ns=time.perf_counter_ns,
            process_identity_reader=_process_identity)

        def helper_factory(role):
            receive, send = ctx.Pipe(duplex=True)
            native = ctx.Process(target=_helper_server,
                args=(send, role, hwnd, generation), daemon=True,
                name="native-f13-" + role)
            wrapped = TimedProcess(native, trace, role)
            helper_connections.append((wrapped, receive, send))
            return wrapped, TraceConnection(receive, trace, role)

        supervisor = OperationCancellationSupervisor(owner,
            recovery_process_factory=lambda: helper_factory("recovery"),
            observer_process_factory=lambda: helper_factory("observer"),
            process_identity_reader=_process_identity,
            clock_ns=time.perf_counter_ns, terminate_grace_s=0.1,
            kill_grace_s=0.1, poll_interval_s=0.002, startup_timeout_s=3.0)
        raw["prestarted_helpers"] = [
            {"name": name, "pid": helper["process"].pid,
             "identity": helper["identity"], "ready": helper["available"]}
            for name, helper in supervisor._helpers.items()]
        operation_deadline = time.perf_counter_ns() + 10_000_000_000
        owner.admit(raw["operation_id"], generation, operation_deadline,
                    ["key:VK_F13"], start_gate_required=True)
        event_queue = ctx.Queue()
        start_gate = ctx.Event()
        native = ctx.Process(target=_producer_child,
            args=(start_gate, event_queue, hwnd, generation), daemon=True,
            name="native-f13-producer")
        producer = TimedProcess(native, trace, "producer")
        producer.start()
        raw["producer_pid"] = producer.pid
        raw["producer_identity"] = _process_identity(producer)
        ready = _wait_queue(event_queue, raw, user32,
            lambda row: row.get("kind") in ("hook_ready", "hook_setup_error"), 3.0)
        if not ready or ready.get("kind") != "hook_ready":
            raw["errors"].append({"stage": "producer_hook_not_ready", "receipt": ready})
            return 2
        raw["producer_hook_ready"] = ready
        if not owner.producer_started(raw["operation_id"], generation, producer,
                                      process_identity=raw["producer_identity"]):
            raw["errors"].append({"stage": "producer_registration_refused"})
            return 2
        if not owner.authorize_producer_start(raw["operation_id"], generation,
                                               producer, start_gate.set):
            raw["errors"].append({"stage": "producer_gate_refused"})
            return 2
        input_authorized = True
        raw["start_gate_opened_ns"] = time.perf_counter_ns()
        hook_entry = _wait_queue(event_queue, raw, user32,
            lambda row: row.get("kind") in ("hook_entry", "send_down_return",
                                             "hook_setup_error", "generation_mismatch"), 1.5)
        raw["cancellation_trigger"] = hook_entry
        if not hook_entry or hook_entry.get("kind") != "hook_entry":
            raw["errors"].append({"stage": "hook_callback_entry_not_observed"})

        cancel_started = time.perf_counter_ns()
        cleanup_deadline = cancel_started + CANCEL_DEADLINE_NS
        raw["cancel_started_ns"] = cancel_started
        cancel_requested = True
        response = supervisor.cancel(raw["operation_id"], generation,
                                     cleanup_deadline_ns=cleanup_deadline)
        raw["cancel_returned_ns"] = time.perf_counter_ns()
        raw["cancel_response"] = response
        raw["cancel_response_ms"] = (raw["cancel_returned_ns"] - cancel_started) / 1e6
        wait_deadline = time.monotonic() + 3.0
        result = owner.result(raw["operation_id"])
        while result["status"] not in ("recovered", "unknown") and time.monotonic() < wait_deadline:
            _pump(user32)
            time.sleep(0.002)
            result = owner.result(raw["operation_id"])
        raw["owner_terminal"] = result
        raw["recovery_finished_observed_ns"] = time.perf_counter_ns()
        raw["timed_process_trace"] = dict(trace)
        raw["helper_trace"] = dict(trace)
        # Drain only already-queued producer records; never wait for or revive it.
        while True:
            try:
                raw["producer_events"].append(event_queue.get_nowait())
            except queue.Empty:
                break

        helper = supervisor._helpers.get("recovery")
        recovery_attempted = bool(trace.get("recovery_requests"))
        raw["recovery_attempted"] = recovery_attempted
        if (result.get("status") == "recovered" and result.get("release_confirmed") is True
                and result.get("cleanup_deadline_ns")):
            # The supervisor's independently spawned observer receipt is retained
            # in the operation owner only as a verified terminal state. The
            # follow-up observer below checks again after the fixed horizon.
            raw["immediate_readback"] = {
                "status": "owner accepted matching independent observer receipt",
                "release_confirmed": result.get("release_confirmed"),
                "recovery_id": result.get("recovery_id")}
        if result.get("recovery_id"):
            horizon_trace = {}
            observer_receipt = _spawn_horizon_observer(ctx, hwnd, generation,
                "fixture", raw["recovery_finished_observed_ns"] + 1_500_000_000,
                horizon_trace)
            raw["horizon_observer"] = observer_receipt
            raw["horizon_observer_trace"] = horizon_trace
        raw["supervisor_closed_ns"] = time.perf_counter_ns()
        raw["task_success"] = result.get("task_success")
        raw["replay_allowed"] = result.get("replay_allowed")
        raw["target_generation_after"] = backend.target_generation("fixture")
    except BaseException as error:
        raw["errors"].append({"stage": "runner_exception", "error": repr(error)})
    finally:
        if input_authorized and not cancel_requested and supervisor is not None:
            try:
                cancel_requested = True
                cleanup_deadline = time.perf_counter_ns() + CANCEL_DEADLINE_NS
                raw["cleanup"]["cancel_requested_ns"] = time.perf_counter_ns()
                supervisor.cancel(raw["operation_id"], generation,
                    cleanup_deadline_ns=cleanup_deadline)
                end = time.monotonic() + 3.0
                while time.monotonic() < end:
                    _pump(user32)
                    status = owner.result(raw["operation_id"])["status"]
                    if status in ("recovered", "unknown"):
                        break
                    time.sleep(0.002)
                raw["cleanup"]["owner_status"] = owner.result(raw["operation_id"])
            except BaseException as error:
                raw["errors"].append({"stage": "cleanup_cancel", "error": repr(error)})
        if supervisor is not None:
            try:
                supervisor.close()
                raw["cleanup"]["supervisor_closed"] = True
            except BaseException as error:
                raw["cleanup"]["supervisor_closed"] = False
                raw["errors"].append({"stage": "supervisor_close", "error": repr(error)})
            worker = getattr(supervisor, "_thread", None)
            raw["cleanup"]["supervisor_thread_exited"] = (
                worker is None or not worker.is_alive())
        if producer is not None:
            try:
                if producer.is_alive():
                    producer.terminate()
                    producer.join(0.2)
                    if producer.is_alive():
                        producer.kill()
                        producer.join(0.2)
                raw["cleanup"]["producer_retired"] = (
                    producer.is_alive() is False and type(producer.exitcode) is int)
                trace.setdefault("producer_exit_observed_ns", time.perf_counter_ns())
                trace["producer_final_exitcode"] = producer.exitcode
                raw["timed_process_trace"] = dict(trace)
            except BaseException as error:
                raw["cleanup"]["producer_retired"] = False
                raw["errors"].append({"stage": "producer_cleanup", "error": repr(error)})
        recovery_attempted = recovery_attempted or bool(trace.get("recovery_requests"))
        if (input_authorized and backend is not None
                and raw["cleanup"].get("producer_retired") is True
                and raw["cleanup"].get("supervisor_thread_exited") is True):
            try:
                state = backend._key_down_state(VK_F13, "fixture")
                raw["cleanup"]["post_supervisor_f13_down"] = state
                if state is not False:
                    raw["cleanup"]["emergency_release_attempted"] = True
                    emergency = INPUT(type=INPUT_KEYBOARD)
                    emergency.ki = KEYBDINPUT(VK_F13, 0, KEYEVENTF_KEYUP, 0, 0)
                    backend._send(emergency)
                    raw["cleanup"]["emergency_release_returned_ns"] = time.perf_counter_ns()
                    raw["cleanup"]["post_emergency_f13_down"] = backend._key_down_state(
                        VK_F13, "fixture")
                else:
                    raw["cleanup"]["emergency_release_attempted"] = False
            except BaseException as error:
                raw["errors"].append({"stage": "emergency_release", "error": repr(error)})
        for _process, _receive, send in helper_connections:
            try:
                send.close()
            except BaseException:
                pass
        raw["helper_trace"] = dict(trace)
        if event_queue is not None:
            try:
                event_queue.close()
                event_queue.join_thread()
            except BaseException:
                pass
        if backend is not None:
            try:
                raw["cleanup"]["backend_close"] = backend.close()
            except BaseException as error:
                raw["errors"].append({"stage": "backend_close", "error": repr(error)})
        if hwnd:
            try:
                raw["cleanup"]["fixture_destroyed"] = bool(user32.DestroyWindow(hwnd))
            except BaseException as error:
                raw["errors"].append({"stage": "fixture_destroy", "error": repr(error)})
        if old_foreground and user32.IsWindow(old_foreground):
            user32.SetForegroundWindow(old_foreground)
            raw["cleanup"]["prior_foreground_restored"] = (
                int(user32.GetForegroundWindow() or 0) == old_foreground)
        else:
            raw["cleanup"]["prior_foreground_restored"] = None
        raw["finished_ns"] = time.perf_counter_ns()
        raw["host"].update({"windows_build": platform.version(),
                            "machine": platform.machine()})
        with RAW.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(raw, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps(raw, indent=2, sort_keys=True))
    return 0 if not raw["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
