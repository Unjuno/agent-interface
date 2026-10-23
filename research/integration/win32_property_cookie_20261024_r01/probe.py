"""One-shot, no-input cross-process Win32 window-property feasibility probe."""
from __future__ import annotations

import ctypes
import datetime as dt
import hashlib
import json
import multiprocessing as mp
import os
import platform
import secrets
import sys
import uuid
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from runtime.backends.win32_v1.backend import Win32Backend

RAW = ROOT / "raw.json"
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
if RAW.exists():
    raise SystemExit("raw.json already exists; refusing to repeat frozen probe")
if sys.platform != "win32":
    raise SystemExit("native Win32 probe requires Windows")


def fixture_child(connection):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
        wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    module = kernel32.GetModuleHandleW(None)
    hwnd = None

    def create(label):
        created = user32.CreateWindowExW(
            0, "STATIC", f"codex-property-cookie-{label}", 0,
            0, 0, 1, 1, None, None, module, None)
        if not created:
            raise ctypes.WinError(ctypes.get_last_error())
        return created

    try:
        hwnd = create("first")
        connection.send({"event": "ready", "pid": os.getpid(),
                         "thread_id": int(kernel32.GetCurrentThreadId()),
                         "hwnd": int(hwnd)})
        while True:
            command = connection.recv()
            if command == "destroy":
                before = bool(user32.IsWindow(hwnd))
                ok = bool(user32.DestroyWindow(hwnd)) if before else False
                after = bool(user32.IsWindow(hwnd))
                connection.send({"event": "destroyed", "before": before,
                                 "destroy_succeeded": ok, "after": after,
                                 "hwnd": int(hwnd)})
                hwnd = None
            elif command == "recreate":
                hwnd = create("second")
                connection.send({"event": "recreated", "pid": os.getpid(),
                                 "thread_id": int(kernel32.GetCurrentThreadId()),
                                 "hwnd": int(hwnd)})
            elif command == "exit":
                if hwnd and user32.IsWindow(hwnd):
                    user32.DestroyWindow(hwnd)
                hwnd = None
                connection.send({"event": "exited"})
                return
    except BaseException as exc:
        try:
            connection.send({"event": "error", "type": type(exc).__name__,
                             "error": str(exc)})
        except Exception:
            pass
        raise
    finally:
        if hwnd and user32.IsWindow(hwnd):
            user32.DestroyWindow(hwnd)
        connection.close()


def receive(connection, expected):
    if not connection.poll(10):
        raise TimeoutError(f"child did not send {expected} within 10 seconds")
    event = connection.recv()
    if event.get("event") != expected:
        raise RuntimeError(f"expected child event {expected}, got {event!r}")
    return event


def main():
    record = {
        "schema": "win32-cross-process-window-property-receipt-v1",
        "attempt_id": CONDITIONS["attempt_id"],
        "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "input_sent": False,
        "window_activated": False,
        "status": "RUNNING",
        "events": [],
    }
    context = mp.get_context("spawn")
    parent, child_connection = context.Pipe()
    process = context.Process(target=fixture_child, args=(child_connection,), daemon=False)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.HANDLE]
    user32.SetPropW.restype = wintypes.BOOL
    user32.GetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.GetPropW.restype = wintypes.HANDLE
    user32.RemovePropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.RemovePropW.restype = wintypes.HANDLE
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    backend = object.__new__(Win32Backend)
    backend.user32, backend.kernel32 = user32, kernel32
    backend.advapi32, backend.gdi32 = advapi32, gdi32
    backend.targets = {"probe": 0}
    Win32Backend._configure_api(backend)
    started = False
    try:
        process.start()
        started = True
        record["child_process_pid"] = process.pid
        child_connection.close()
        first = receive(parent, "ready")
        record["events"].append(first)
        if first["pid"] != process.pid:
            raise RuntimeError("child window PID did not match spawned process")
        backend.targets["probe"] = first["hwnd"]
        record["first_identity"] = backend._window_owner_identity_for_hwnd(first["hwnd"])
        if record["first_identity"]["pid"] != first["pid"]:
            raise RuntimeError("production identity did not match window owner")

        property_name = f"Codex.TargetIncarnation.{uuid.uuid4()}"
        token = secrets.randbits(63) or 1
        record["property_name"], record["property_token"] = property_name, token
        ctypes.set_last_error(0)
        record["set_property_succeeded"] = bool(
            user32.SetPropW(first["hwnd"], property_name, wintypes.HANDLE(token)))
        record["set_last_error"] = ctypes.get_last_error()
        if not record["set_property_succeeded"]:
            record["status"] = "PROPERTY_COOKIE_UNAVAILABLE_FOR_THIS_TARGET"
        else:
            read = user32.GetPropW(first["hwnd"], property_name)
            record["first_readback"] = int(read or 0)
            record["first_readback_matches"] = record["first_readback"] == token
            if not record["first_readback_matches"]:
                raise RuntimeError("property readback did not match the set token")
            parent.send("destroy")
            destroyed = receive(parent, "destroyed")
            record["events"].append(destroyed)
            record["destroyed_handle_is_window"] = bool(user32.IsWindow(first["hwnd"]))
            stale_value = user32.GetPropW(first["hwnd"], property_name)
            record["stale_handle_property_value"] = int(stale_value or 0)
            parent.send("recreate")
            second = receive(parent, "recreated")
            record["events"].append(second)
            record["second_identity"] = backend._window_owner_identity_for_hwnd(second["hwnd"])
            record["same_pid"] = first["pid"] == second["pid"]
            record["same_thread"] = first["thread_id"] == second["thread_id"]
            record["same_creation_identity"] = record["first_identity"] == record["second_identity"]
            record["same_hwnd"] = first["hwnd"] == second["hwnd"]
            second_value = user32.GetPropW(second["hwnd"], property_name)
            record["second_handle_property_value"] = int(second_value or 0)
            if record["same_hwnd"] and record["second_handle_property_value"] == token:
                record["status"] = "PROPERTY_COOKIE_ALIAS_COUNTEREXAMPLE"
            elif record["same_hwnd"] and record["second_handle_property_value"] == 0:
                record["status"] = "REUSED_HWND_COOKIE_CLEARED"
            elif record["second_handle_property_value"] == 0:
                record["status"] = "CROSS_PROCESS_PROPERTY_WORKS_NO_REUSE_OBSERVED"
            else:
                raise RuntimeError("new window carried an unexpected property value")

        if user32.IsWindow(first["hwnd"]):
            current = user32.GetPropW(first["hwnd"], property_name)
            if int(current or 0) == token:
                removed = user32.RemovePropW(first["hwnd"], property_name)
                record["cleanup_remove_property_value"] = int(removed or 0)
        parent.send("exit")
        record["events"].append(receive(parent, "exited"))
        process.join(2)
        record["child_exit_code"] = process.exitcode
        record["child_still_alive_after_join"] = process.is_alive()
        if process.is_alive() or process.exitcode != 0:
            raise RuntimeError("owned fixture child did not exit cleanly")
    except BaseException as exc:
        record["status"] = "HOLD_UNKNOWN"
        record["error_type"], record["error"] = type(exc).__name__, str(exc)
    finally:
        if started and process.is_alive():
            process.terminate()
            process.join(1)
            record["owned_child_terminated_for_cleanup"] = True
            record["child_exit_code"] = process.exitcode
        if started:
            try:
                process.close()
            except Exception:
                pass
        parent.close()
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        encoded = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        RAW.write_bytes(encoded)
        record["raw_sha256"] = hashlib.sha256(encoded).hexdigest()
    print(json.dumps(record, indent=2, sort_keys=True))
    if record["status"] in ("RUNNING", "HOLD_UNKNOWN"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
