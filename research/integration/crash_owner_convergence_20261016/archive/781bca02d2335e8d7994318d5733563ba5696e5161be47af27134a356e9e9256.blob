#!/usr/bin/env python3
"""One-arm isolated Xvfb probe: kill session parent, retain owner service."""

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
from Xlib.ext import xtest


def now():
    return time.monotonic_ns()


def key_is_down(dpy, keycode):
    bits = dpy.query_keymap()
    return bool(bits[keycode // 8] & (1 << (keycode % 8)))


def write_receipt(path, data):
    encoded = (json.dumps(data, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, encoded)
        os.fsync(fd)
    finally:
        os.close(fd)


def owner_service(sock_path, receipt_path, session_pid):
    dpy = display.Display()
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(sock_path)
    listener.listen(1)
    conn, _ = listener.accept()
    stream = conn.makefile("rwb", buffering=0)
    command = json.loads(stream.readline())
    keycode = command["keycode"]
    xtest.fake_input(dpy, X.KeyPress, detail=keycode)
    dpy.sync()
    down = key_is_down(dpy, keycode)
    stream.write((json.dumps({"event": "held", "at_ns": now(),
                              "keymap_down": down}) + "\n").encode())

    while conn.recv(1):
        pass
    eof_ns = now()
    ppid_at_eof = os.getppid()
    release_started_ns = now()
    xtest.fake_input(dpy, X.KeyRelease, detail=keycode)
    dpy.sync()
    up = not key_is_down(dpy, keycode)
    release_finished_ns = now()
    receipt = {
        "schema": "v39-session-parent-crash-owner-receipt-a05-v1",
        "pid": os.getpid(), "session_pid_at_start": session_pid,
        "ppid_at_eof": ppid_at_eof, "eof_ns": eof_ns,
        "release_started_ns": release_started_ns,
        "release_finished_ns": release_finished_ns,
        "keys_down_before_release": [keycode] if down else [],
        "keys_down_after_release": [] if up else [keycode],
        "keymap_up": up, "receipt_fsynced": True,
    }
    write_receipt(receipt_path, receipt)
    stream.close()
    conn.close()
    listener.close()
    dpy.close()
    return 0 if up else 3


def session_child(sock_path, receipt_path):
    owner = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "owner", sock_path,
         receipt_path, str(os.getpid())],
        start_new_session=True,
        close_fds=True,
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
    keycode = display.Display().keysym_to_keycode(0x61)
    stream.write((json.dumps({"op": "hold", "keycode": keycode}) + "\n").encode())
    ack = json.loads(stream.readline())
    print(json.dumps({"event": "session_held", "owner_pid": owner.pid,
                      "session_pid": os.getpid(), "keycode": keycode,
                      "owner_ack": ack}), flush=True)
    while True:
        time.sleep(1)


def wait_event(observer, event_type, timeout=3):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        while observer.pending_events():
            event = observer.next_event()
            if event.type == event_type:
                return event_record(event)
        time.sleep(0.002)
    return None


def event_record(event, observed_ns=None):
    """Project python-xlib key events to stable scalar evidence."""
    return {"type": event.type, "keycode": event.detail,
            "observed_ns": now() if observed_ns is None else observed_ns,
            "window": event.window.id}


def run_probe():
    # Become a Linux child subreaper so the detached owner can be waited after
    # its session parent is killed; no owner cleanup is delegated to the test.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_CHILD_SUBREAPER) failed")

    display_num = 160 + os.getpid() % 70
    display_name = f":{display_num}"
    xvfb = subprocess.Popen(
        ["Xvfb", display_name, "-screen", "0", "800x600x24",
         "-nolisten", "tcp", "-ac"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    temp = tempfile.TemporaryDirectory(prefix="v39-a05-")
    root = Path(temp.name)
    sock_path = str(root / "owner.sock")
    receipt_path = str(root / "owner-receipt.json")
    env = dict(os.environ, DISPLAY=display_name)
    session = None
    owner_pid = None
    forced_kill = False
    raw = {
        "schema": "v39-session-parent-crash-owner-xvfb-a05-raw-v1",
        "display": display_name, "scope": "isolated Xvfb and session/owner process tree",
        "session": {}, "owner": {}, "observer": {}, "xvfb": {},
    }
    ctrl = None
    observer = None
    window = None
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                ctrl = display.Display(display_name)
                break
            except Exception:
                if xvfb.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Xvfb did not become ready")
                time.sleep(0.02)
        observer = display.Display(display_name)
        screen = ctrl.screen()
        window = screen.root.create_window(
            0, 0, 320, 240, 0, X.CopyFromParent, X.InputOutput,
            X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        ctrl.sync()
        observer_window = observer.create_resource_object("window", window.id)
        observer_window.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
        observer.sync()
        while observer.pending_events():
            observer.next_event()

        session = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "session", sock_path,
             receipt_path], env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )
        owner_started = json.loads(session.stdout.readline())
        held = json.loads(session.stdout.readline())
        owner_pid = owner_started["owner_pid"]
        keycode = held["keycode"]
        press = wait_event(observer, X.KeyPress)
        down_before = key_is_down(observer, keycode)
        if not press or not down_before or not held["owner_ack"].get("keymap_down"):
            raise RuntimeError("held key not independently verified before kill")

        kill_requested_ns = now()
        session.kill()
        session_returncode = session.wait(timeout=3)
        session_dead_ns = now()
        release = wait_event(observer, X.KeyRelease, timeout=5)

        receipt_deadline = time.monotonic() + 5
        while not Path(receipt_path).exists() and time.monotonic() < receipt_deadline:
            time.sleep(0.01)
        if Path(receipt_path).exists():
            owner = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        else:
            owner = {"pid": owner_pid}
        owner["returncode"] = None
        owner["forced_kill"] = False
        owner_deadline = time.monotonic() + 5
        owner_returncode = None
        while time.monotonic() < owner_deadline:
            try:
                waited_pid, status = os.waitpid(owner_pid, os.WNOHANG)
                if waited_pid:
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
        owner["returncode"] = owner_returncode
        owner["forced_kill"] = forced_kill
        keymap_up_after = not key_is_down(observer, keycode)
        raw["session"] = {
            "pid": session.pid, "returncode": session_returncode,
            "killed_by_sigkill": session_returncode == -signal.SIGKILL,
            "kill_requested_ns": kill_requested_ns, "dead_ns": session_dead_ns,
        }
        raw["owner"] = owner
        raw["observer"] = {
            "key_press_ns": press["observed_ns"] if press else 0,
            "key_release_ns": release["observed_ns"] if release else 0,
            "keymap_down_before_kill": down_before,
            "keymap_up_after_release": keymap_up_after,
        }
    finally:
        if session is not None and session.poll() is None:
            session.kill()
            session.wait()
        if owner_pid is not None and not Path(receipt_path).exists():
            try:
                os.kill(owner_pid, signal.SIGKILL)
                forced_kill = True
            except ProcessLookupError:
                pass
        if window is not None:
            window.destroy()
        if observer is not None:
            observer.close()
        if ctrl is not None:
            ctrl.close()
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
        return owner_service(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    if len(sys.argv) > 1 and sys.argv[1] == "session":
        session_child(sys.argv[2], sys.argv[3])
        return 0
    raw = run_probe()
    output = Path(__file__).with_name("results") / "A01" / "RAW.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_path": str(output), "raw": raw}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
