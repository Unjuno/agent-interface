"""Isolated X11/Tk command/state/effect measurement, not the Agent Interface runtime."""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import selectors
import socket
import struct
import subprocess as sp
import sys
import tempfile
import time
import traceback
from Xlib import X, XK, display
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parent
SCHEDULES = ("NO_INPUT", "SINGLE_TAP", "DUPLICATE_DOWN", "TWO_TAPS", "LONG_HOLD")
SOURCES = ("study.py", "receiver.py", "audit.py", "test_audit.py", "PLAN.md", "ENVIRONMENT.json", "supervise.py")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open("x") as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write("\n")


def hashes():
    return {p: sha((ROOT / p).read_bytes()) for p in SOURCES}


def line_from(proc, timeout=3):
    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    data = bytearray()
    try:
        while b"\n" not in data:
            if not sel.select(max(0, deadline - time.monotonic())):
                raise TimeoutError("receiver readiness")
            char = os.read(proc.stdout.fileno(), 1)
            if not char:
                raise EOFError("receiver ended before ready")
            data.extend(char)
        return bytes(data)
    finally:
        sel.close()


def xkb_rate(name):
    lib = C.CDLL("libX11.so.6")
    lib.XOpenDisplay.argtypes = [C.c_char_p]
    lib.XOpenDisplay.restype = C.c_void_p
    lib.XCloseDisplay.argtypes = [C.c_void_p]
    lib.XSync.argtypes = [C.c_void_p, C.c_int]
    lib.XkbSetAutoRepeatRate.argtypes = [C.c_void_p, C.c_uint, C.c_uint, C.c_uint]
    lib.XkbGetAutoRepeatRate.argtypes = [C.c_void_p, C.c_uint,
                                        C.POINTER(C.c_uint), C.POINTER(C.c_uint)]
    d = lib.XOpenDisplay(name.encode())
    if not d:
        raise RuntimeError("native XOpenDisplay")
    try:
        set_ok = int(lib.XkbSetAutoRepeatRate(d, 0x100, 250, 50))
        lib.XSync(d, 0)
        delay, interval = C.c_uint(), C.c_uint()
        get_ok = int(lib.XkbGetAutoRepeatRate(d, 0x100, C.byref(delay), C.byref(interval)))
        return dict(set_ok=set_ok, get_ok=get_ok, delay_ms=delay.value, interval_ms=interval.value)
    finally:
        lib.XCloseDisplay(d)


def snapshot(d):
    t0 = time.monotonic_ns()
    keys = list(d.query_keymap())
    point = d.screen().root.query_pointer()
    focus = d.get_input_focus().focus
    return dict(start_ns=t0, end_ns=time.monotonic_ns(), keymap=keys,
                buttons=point.mask & (X.Button1Mask | X.Button2Mask | X.Button3Mask |
                                       X.Button4Mask | X.Button5Mask),
                focus=focus.id if hasattr(focus, "id") else int(focus))


def run_case(folder, env, index, repeat, schedule, letter, rep):
    folder.mkdir()
    row = dict(index=index, rep=rep, schedule=schedule, repeat=repeat, letter=letter,
               controller_pid=os.getpid(), start_ns=time.monotonic_ns(), commands=[], native=[])
    proc = None
    d = None
    ready_line = b""
    try:
        d = display.Display(env["DISPLAY"])
        code = d.keysym_to_keycode(XK.string_to_keysym(letter))
        if not code:
            raise RuntimeError("letter unavailable")
        row["keycode"] = code
        d.change_keyboard_control(key=code, auto_repeat_mode=X.AutoRepeatModeOn)
        d.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOn if repeat else X.AutoRepeatModeOff)
        d.sync()
        ctl = d.get_keyboard_control()
        row["repeat_readback"] = dict(global_mode=int(ctl.global_auto_repeat),
                                      auto_repeats=list(ctl.auto_repeats), led_mask=int(ctl.led_mask))
        row["initial"] = snapshot(d)
        if any(row["initial"]["keymap"]) or row["initial"]["buttons"]:
            raise RuntimeError("initial input not neutral")
        command = [sys.executable, "-B", str(ROOT / "receiver.py")]
        row["receiver_command"] = command
        proc = sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
                        env=env, cwd=folder, bufsize=0)
        row["receiver_pid"] = proc.pid
        ready_line = line_from(proc)
        ready = json.loads(ready_line)
        row["ready"] = ready
        if ready["kind"] != "ready" or ready["value"] != "":
            raise RuntimeError("bad receiver readiness")
        win = d.create_resource_object("window", ready["window"])
        # This independent connection records native delivery and a final server barrier.
        win.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask | X.PropertyChangeMask)
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        d.sync()
        row["focused"] = snapshot(d)
        if row["focused"]["focus"] != ready["window"]:
            raise RuntimeError("wrong receiver focus")

        def emit(kind):
            rec = dict(kind=kind, pre=snapshot(d))
            if rec["pre"]["focus"] != ready["window"]:
                raise RuntimeError("focus lost")
            rec["call_start_ns"] = time.monotonic_ns()
            # Same native emission primitive as the reviewed input_owner_v10 branch.
            xtest.fake_input(d, X.KeyPress if kind == "down" else X.KeyRelease, code)
            d.sync()
            rec["call_end_ns"] = time.monotonic_ns()
            rec["post"] = snapshot(d)
            row["commands"].append(rec)

        if schedule != "NO_INPUT":
            emit("down")
            time.sleep(.650 if schedule == "LONG_HOLD" else .040)
            if schedule == "DUPLICATE_DOWN":
                emit("down")
                time.sleep(.040)
            elif schedule == "TWO_TAPS":
                emit("up")
                time.sleep(.040)
                emit("down")
                time.sleep(.040)
            emit("up")
        else:
            time.sleep(.080)
        barrier = d.intern_atom("_ISSUE4032_BARRIER")
        win.change_property(barrier, 6, 32, [index + 1])
        d.sync()
        deadline = time.monotonic() + 2
        while True:
            if not d.pending_events():
                if time.monotonic() >= deadline:
                    raise TimeoutError("native barrier")
                time.sleep(.001)
                continue
            event = d.next_event()
            now = time.monotonic_ns()
            if event.type in (X.KeyPress, X.KeyRelease):
                row["native"].append(dict(kind="press" if event.type == X.KeyPress else "release",
                                          keycode=event.detail, x_time=event.time, state=event.state,
                                          window=event.window.id, observed_ns=now))
            elif event.type == X.PropertyNotify and event.atom == barrier:
                row["barrier"] = dict(atom=barrier, window=event.window.id, x_time=event.time,
                                       observed_ns=now, token=index + 1)
                break
        row["terminal"] = snapshot(d)
        tail, err = proc.communicate(b"finish\n", timeout=3)
        row["receiver_exit"] = proc.returncode
        row["receiver_stdout"] = (ready_line + tail).decode()
        row["receiver_stderr"] = err.decode()
        row["events"] = [json.loads(line) for line in row["receiver_stdout"].splitlines()]
        if proc.returncode or err:
            raise RuntimeError("receiver did not exit cleanly")
        row["disposition"] = "COMPLETE"
    except BaseException as exc:
        row["disposition"] = "STOP_CASE"
        row["error"] = repr(exc)
        row["traceback"] = traceback.format_exc()
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                tail, err = proc.communicate(timeout=2)
            except sp.TimeoutExpired:
                proc.kill()
                tail, err = proc.communicate(timeout=2)
            row.update(receiver_exit=proc.returncode, receiver_stdout=(ready_line + tail).decode(),
                       receiver_stderr=err.decode())
        if d is not None:
            try:
                # Common cleanup is after measured terminal and is not policy credit.
                for code in range(8, 256):
                    bitmap = d.query_keymap()
                    if bitmap[code // 8] & (1 << (code % 8)):
                        xtest.fake_input(d, X.KeyRelease, code)
                d.sync()
                row["cleanup"] = snapshot(d)
                d.close()
            except BaseException as exc:
                row["cleanup_error"] = repr(exc)
                row["disposition"] = "STOP_CASE"
        row["end_ns"] = time.monotonic_ns()
        write(folder / "row.json", row)
    return row


def run(out, batch, construction):
    out.mkdir(parents=True, exist_ok=False)
    metadata = dict(batch=batch, construction=construction, runner_pid=os.getpid(),
                    start_ns=time.monotonic_ns(), source_hashes=hashes(), rows=[])
    write(out / "CONSUMED.json", metadata)
    server = None
    errors = []
    try:
        if not construction:
            freeze = json.loads((ROOT / "FREEZE.json").read_text())
            if freeze["source_hashes"] != hashes():
                raise RuntimeError("source freeze mismatch")
        with tempfile.TemporaryDirectory(prefix="4032-private-") as home:
            # Existing displays are never opened. Xvfb owns the chosen unused display.
            number = next(n for n in range(431, 999) if not Path(f"/tmp/.X11-unix/X{n}").exists()
                          and not Path(f"/tmp/.X{n}-lock").exists())
            name = f":{number}"
            authority = Path(home) / "authority"
            cookie = os.urandom(16)
            address = socket.gethostname().encode()
            fields = (address, str(number).encode(), b"MIT-MAGIC-COOKIE-1", cookie)
            authority.write_bytes(struct.pack("!H", 256) + b"".join(struct.pack("!H", len(x)) + x for x in fields))
            authority.chmod(0o600)
            env = {"PATH":os.defpath, "HOME":home, "LANG":"C.UTF-8", "DISPLAY":name,
                   "XAUTHORITY":str(authority), "PYTHONNOUSERSITE":"1"}
            metadata["display"] = name
            server_command = ["/usr/bin/Xvfb", name, "-screen", "0", "400x160x24",
                              "-nolisten", "tcp", "-auth", str(authority), "-noreset"]
            metadata["server_command"] = server_command
            with (out / "server.stdout").open("xb") as stdout, (out / "server.stderr").open("xb") as stderr:
                server = sp.Popen(server_command, stdout=stdout, stderr=stderr, env=env)
                metadata["server_pid"] = server.pid
                deadline = time.monotonic() + 3
                while not Path(f"/tmp/.X11-unix/X{number}").exists():
                    if server.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Xvfb readiness")
                    time.sleep(.01)
                # ctypes uses environment for authentication; never use inherited credentials.
                old = {k: os.environ.get(k) for k in ("DISPLAY", "XAUTHORITY")}
                os.environ.update({k: env[k] for k in old})
                try:
                    metadata["repeat_rate"] = xkb_rate(name)
                    for j in range(10):
                        repeat = bool((j // 5 + batch) % 2)
                        schedule = SCHEDULES[(j % 5 + batch) % 5]
                        row = run_case(out / f"case-{j:02}", env, batch * 10 + j, repeat,
                                       schedule, "c" if construction else "a", batch)
                        metadata["rows"].append(row["index"])
                        if row["disposition"] != "COMPLETE":
                            raise RuntimeError(f"case {j} stopped")
                finally:
                    for k, v in old.items():
                        if v is None:
                            os.environ.pop(k, None)
                        else:
                            os.environ[k] = v
                server.terminate()
                metadata["server_exit"] = server.wait(timeout=3)
                metadata["socket_absent"] = not Path(f"/tmp/.X11-unix/X{number}").exists()
    except BaseException as exc:
        errors.append(dict(error=repr(exc), traceback=traceback.format_exc()))
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                metadata["server_exit"] = server.wait(timeout=3)
            except sp.TimeoutExpired:
                server.kill()
                metadata["server_exit"] = server.wait(timeout=3)
        metadata.update(errors=errors, end_ns=time.monotonic_ns(), source_hashes_after=hashes())
        metadata["disposition"] = "COMPLETE" if not errors else "STOP_BATCH"
        write(out / "BATCH.json", metadata)
    print(json.dumps({k: metadata[k] for k in ("batch", "rows", "errors", "disposition")}))
    return int(bool(errors))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    p.add_argument("--batch", type=int, choices=(0, 1), required=True)
    p.add_argument("--construction", action="store_true")
    args = p.parse_args()
    raise SystemExit(run(args.out.resolve(), args.batch, args.construction))
