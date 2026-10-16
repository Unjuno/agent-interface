#!/usr/bin/env python3
"""Isolated crash test using the production InputOwner V4/V3/V10/V12 stack."""

import ctypes
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time

from Xlib import X, display

RESEARCH = Path(__file__).resolve().parents[2]
LIVE_CONTROL = RESEARCH / "live_control"
sys.path.insert(0, str(LIVE_CONTROL))

from input_transition_owner_v4 import InputOwner
from lease import Lease


def now():
    return time.perf_counter_ns()


def key_is_down(dpy, keycode):
    bitmap = dpy.query_keymap()
    return bool(bitmap[keycode // 8] & (1 << (keycode % 8)))


def decode_down_request(request):
    fields = {"schema", "op", "key", "deadline_ns", "intent_token", "expected_focus"}
    if type(request) is not dict or set(request) != fields:
        raise ValueError("exact request fields required")
    if request["schema"] != "input-owner-rpc-v1" or request["op"] != "down":
        raise ValueError("unsupported input-owner RPC operation")
    if request["key"] != "a":
        raise ValueError("key not allowlisted")
    if type(request["deadline_ns"]) is not int or request["deadline_ns"] <= now():
        raise ValueError("deadline expired")
    token = request["intent_token"]
    if not isinstance(token, str) or not token or len(token) > 128:
        raise ValueError("valid intent token required")
    focus = request["expected_focus"]
    if type(focus) is not int or focus <= 1:
        raise ValueError("observed focus window required")
    lease = Lease(request["deadline_ns"])
    lease.intent_token = token
    lease.expected_focus = focus
    return lease, request["key"]


def write_json_fsynced(path, value):
    data = (json.dumps(value, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def owner_service(display_name, sock_path, receipt_path, session_pid):
    owner = InputOwner(display_name)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(sock_path)
    listener.listen(1)
    conn, _ = listener.accept()
    stream = conn.makefile("rwb", buffering=0)
    request = json.loads(stream.readline())
    lease, key = decode_down_request(request)
    admitted = owner.call("down", lease, key)
    stream.write((json.dumps({"event": "admitted", "owner_id": owner.owner_id,
                              "admitted": admitted, "at_ns": now()}) + "\n").encode())
    while conn.recv(1):
        pass
    eof_ns = now()
    ppid_at_eof = os.getppid()
    close_started_ns = now()
    close_error = None
    try:
        owner.close()
    except BaseException as exc:
        close_error = {"type": type(exc).__name__, "message": str(exc)[:300]}
    close_finished_ns = now()
    records = owner.records
    release_records = [r for r in records if isinstance(r, dict)
                       and r.get("event") == "owner_release"]
    receipt = {
        "schema": "v39-v15-inputowner-process-receipt-a06-v1",
        "pid": os.getpid(), "session_pid_at_start": session_pid,
        "ppid_at_eof": ppid_at_eof, "eof_ns": eof_ns,
        "close_started_ns": close_started_ns, "close_finished_ns": close_finished_ns,
        "owner_id": owner.owner_id, "intent_token": lease.intent_token,
        "expected_focus": lease.expected_focus, "admitted": admitted,
        "owner_records": records, "release_record_count": len(release_records),
        "release_record": release_records[-1] if release_records else None,
        "close_error": close_error, "thread_stopped": owner._inner.stopped.is_set(),
        "receipt_fsynced": True,
    }
    write_json_fsynced(receipt_path, receipt)
    stream.close()
    conn.close()
    listener.close()
    clean = (close_error is None and len(release_records) == 1
             and release_records[0].get("verified") is True
             and release_records[0].get("keys_down") == []
             and release_records[0].get("buttons_down") == []
             and owner._inner.stopped.is_set())
    return 0 if clean else 4


def session_child(display_name, sock_path, receipt_path, focus_id):
    env = dict(os.environ, DISPLAY=display_name)
    owner = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "owner", display_name,
         sock_path, receipt_path, str(os.getpid())],
        env=env, start_new_session=True, close_fds=True,
    )
    print(json.dumps({"event": "owner_started", "owner_pid": owner.pid,
                      "session_pid": os.getpid()}), flush=True)
    deadline = time.monotonic() + 5
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while True:
        try:
            conn.connect(sock_path)
            break
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
    stream = conn.makefile("rwb", buffering=0)
    request = {
        "schema": "input-owner-rpc-v1", "op": "down", "key": "a",
        "deadline_ns": now() + 20_000_000_000,
        "intent_token": "a06-session-kill-intent",
        "expected_focus": int(focus_id),
    }
    stream.write((json.dumps(request) + "\n").encode())
    ack = json.loads(stream.readline())
    print(json.dumps({"event": "held", "owner_pid": owner.pid,
                      "session_pid": os.getpid(), "request": request,
                      "owner_ack": ack}), flush=True)
    while True:
        time.sleep(1)


def wait_event(dpy, event_type, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        while dpy.pending_events():
            event = dpy.next_event()
            if event.type == event_type:
                return {"type": event.type, "keycode": event.detail,
                        "observed_ns": now(), "window": event.window.id}
        time.sleep(0.002)
    return None


def run_probe(arm_id="A01"):
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER failed")
    display_name = f":{170 + os.getpid() % 60}"
    xvfb = subprocess.Popen(["Xvfb", display_name, "-screen", "0", "800x600x24",
                             "-nolisten", "tcp", "-ac"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    temp = tempfile.TemporaryDirectory(prefix="v39-a06-")
    root = Path(temp.name)
    sock_path, receipt_path = str(root / "owner.sock"), str(root / "receipt.json")
    control = observer = window = session = None
    owner_pid = None
    forced_kill = False
    raw = {"schema": "v39-v15-inputowner-process-xvfb-a06-raw-v1",
           "arm": arm_id,
           "display": display_name, "session": {}, "owner": {},
           "observer": {}, "xvfb": {}}
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                control = display.Display(display_name)
                break
            except Exception:
                if xvfb.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Xvfb startup failed")
                time.sleep(0.02)
        observer = display.Display(display_name)
        window = control.screen().root.create_window(
            0, 0, 320, 240, 0, X.CopyFromParent, X.InputOutput,
            X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        control.sync()
        observed = observer.create_resource_object("window", window.id)
        observed.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
        observer.sync()
        while observer.pending_events():
            observer.next_event()
        session = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "session", display_name,
             sock_path, receipt_path, str(window.id)],
            env=dict(os.environ, DISPLAY=display_name), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1)
        started = json.loads(session.stdout.readline())
        held = json.loads(session.stdout.readline())
        owner_pid = started["owner_pid"]
        keycode = held["owner_ack"]["admitted"]["keycode"]
        press = wait_event(observer, X.KeyPress)
        down = key_is_down(observer, keycode)
        if not press or not down:
            raise RuntimeError("current InputOwner key-down not independently verified")
        kill_requested_ns = now()
        session.kill()
        session_returncode = session.wait(timeout=3)
        wait_return_ns = now()
        release = wait_event(observer, X.KeyRelease, timeout=5)
        until = time.monotonic() + 5
        while not Path(receipt_path).exists() and time.monotonic() < until:
            time.sleep(0.01)
        receipt = (json.loads(Path(receipt_path).read_text(encoding="utf-8"))
                   if Path(receipt_path).exists() else {"pid": owner_pid})
        owner_returncode = None
        until = time.monotonic() + 5
        while time.monotonic() < until:
            try:
                pid, status = os.waitpid(owner_pid, os.WNOHANG)
                if pid:
                    owner_returncode = os.waitstatus_to_exitcode(status)
                    break
            except ChildProcessError:
                break
            time.sleep(0.01)
        if owner_returncode is None:
            forced_kill = True
            try:
                os.kill(owner_pid, signal.SIGKILL)
                _, status = os.waitpid(owner_pid, 0)
                owner_returncode = os.waitstatus_to_exitcode(status)
            except ProcessLookupError:
                owner_returncode = 0
        receipt["returncode"] = owner_returncode
        receipt["forced_kill"] = forced_kill
        raw.update({
            "session": {"pid": session.pid, "returncode": session_returncode,
                        "killed_by_sigkill": session_returncode == -signal.SIGKILL,
                        "kill_requested_ns": kill_requested_ns,
                        "wait_return_ns": wait_return_ns},
            "owner": receipt,
            "observer": {"key_press_ns": press["observed_ns"] if press else 0,
                         "key_release_ns": release["observed_ns"] if release else 0,
                         "keymap_down_before_kill": down,
                         "keymap_up_after_release": not key_is_down(observer, keycode)},
            "xvfb": {},
        })
    finally:
        if session is not None and session.poll() is None:
            session.kill()
            session.wait()
        if session is not None and session.stderr is not None:
            diagnostic = session.stderr.read()
            if diagnostic:
                runner = Path(__file__).with_name("RUNNER")
                runner.mkdir(exist_ok=True)
                (runner / f"{arm_id}-session-stderr.txt").write_text(
                    diagnostic, encoding="utf-8")
        if owner_pid is not None and not Path(receipt_path).exists():
            try:
                os.kill(owner_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if window is not None:
            window.destroy()
        if observer is not None:
            observer.close()
        if control is not None:
            control.close()
        xvfb.terminate()
        try:
            raw["xvfb"]["returncode"] = xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            raw["xvfb"]["returncode"] = xvfb.wait()
        temp.cleanup()
    return raw


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "owner":
        return owner_service(*sys.argv[2:5], int(sys.argv[5]))
    if len(sys.argv) > 1 and sys.argv[1] == "session":
        session_child(*sys.argv[2:6])
        return 0
    arm_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--arm" else "A01"
    raw = run_probe(arm_id)
    out = Path(__file__).with_name("results") / arm_id / "RAW.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"raw_path": str(out), "raw": raw}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
