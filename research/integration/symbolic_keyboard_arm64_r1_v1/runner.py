#!/usr/bin/env python3
"""One fresh, private Xvfb/XKB/XTEST mapping-boundary case."""
import argparse
import hashlib
import json
import os
import re
import secrets
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

from Xlib import X, XK, display
from Xlib.ext import xtest

POLICIES = ["RAW_RETAINED_MAP", "SNAPSHOT_REFUSE_ON_CHANGE", "CURRENT_FRESH_MAP"]


def command(argv, env=None, timeout=5):
    p = subprocess.run(argv, env=env, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError({"argv": argv, "returncode": p.returncode,
                            "stdout": p.stdout.decode("utf-8", "replace"),
                            "stderr": p.stderr.decode("utf-8", "replace")})
    return p.stdout


def server_map_digest(env):
    return hashlib.sha256(command(["xkbcomp", "-xkb", env["DISPLAY"], "-"], env)).hexdigest()


def z_code(d):
    return int(d.keysym_to_keycode(XK.string_to_keysym("z")))


def state(d):
    keymap = list(d.query_keymap())
    pointer = int(d.screen().root.query_pointer().mask)
    return {"keymap": keymap, "pointer_mask": pointer,
            "neutral": not any(keymap) and not (pointer & 0x1f00),
            "monotonic_ns": time.monotonic_ns()}


def receive_one(observer, window, display_name, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not observer.pending_events():
            select.select([observer.fileno()], [], [], max(0.0, deadline - time.monotonic()))
        while observer.pending_events():
            ev = observer.next_event()
            if ev.type in (X.KeyPress, X.KeyRelease):
                fresh = display.Display(display_name)
                try:
                    sym = fresh.keycode_to_keysym(ev.detail, 0)
                    symbol = XK.keysym_to_string(sym) or f"0x{sym:x}"
                finally:
                    fresh.close()
                return {"type": "KeyPress" if ev.type == X.KeyPress else "KeyRelease",
                        "type_code": int(ev.type), "detail": int(ev.detail),
                        "state": int(ev.state), "keysym_current": symbol,
                        "window": int(getattr(ev, "event", window.id)),
                        "monotonic_ns": time.monotonic_ns()}
    return None


def emit(emitter, observer, display_name, window, ctrl_code, target_code):
    emitted, observed, states = [], [], []
    for code in (ctrl_code, target_code):
        xtest.fake_input(emitter, X.KeyPress, code)
        emitter.sync()
        emitted.append({"type": "KeyPress", "detail": int(code), "monotonic_ns": time.monotonic_ns()})
        observed.append(receive_one(observer, window, display_name))
        monitor = display.Display(display_name)
        try:
            down = list(monitor.query_keymap())
            states.append({"after_request": len(emitted) - 1, "request": "KeyPress",
                           "detail": int(code), "target_down": bool(down[code // 8] & (1 << (code % 8))),
                           "control_down": bool(down[ctrl_code // 8] & (1 << (ctrl_code % 8)))})
        finally:
            monitor.close()
    for code in (target_code, ctrl_code):
        xtest.fake_input(emitter, X.KeyRelease, code)
        emitter.sync()
        emitted.append({"type": "KeyRelease", "detail": int(code), "monotonic_ns": time.monotonic_ns()})
        observed.append(receive_one(observer, window, display_name))
        monitor = display.Display(display_name)
        try:
            down = list(monitor.query_keymap())
            states.append({"after_request": len(emitted) - 1, "request": "KeyRelease",
                           "detail": int(code), "target_down": bool(down[code // 8] & (1 << (code % 8))),
                           "control_down": bool(down[ctrl_code // 8] & (1 << (ctrl_code % 8)))})
        finally:
            monitor.close()
    return emitted, observed, states


def parse_xev(path):
    text = path.read_text(errors="replace") if path.exists() else ""
    events = []
    for block in re.split(r"(?=Key(?:Press|Release) event,)", text):
        kind = re.match(r"(KeyPress|KeyRelease) event,", block)
        if not kind:
            continue
        code = re.search(r"keycode (\d+)", block)
        state_match = re.search(r"state 0x([0-9a-fA-F]+)", block)
        sym = re.search(r"keysym 0x([0-9a-fA-F]+), ([^,)]+)", block)
        if code and state_match:
            events.append({"type": kind.group(1), "detail": int(code.group(1)),
                           "state": int(state_match.group(1), 16),
                           "keysym": None if not sym else sym.group(2),
                           "keysym_hex": None if not sym else int(sym.group(1), 16)})
    return events


def execute(spec, out):
    out.mkdir(parents=True, exist_ok=True)
    if (out / "ROW.json").exists():
        raise RuntimeError("output_row_already_exists")
    row = {"spec": spec, "error": None, "source_commit": os.environ.get("SOURCE_COMMIT"),
           "image_id": os.environ.get("IMAGE_ID"), "started_monotonic_ns": time.monotonic_ns()}
    display_number = 240 + os.getpid() % 300
    display_name = f":{display_number}"
    socket = Path(f"/tmp/.X11-unix/X{display_number}")
    auth = Path(f"/tmp/xauth-{secrets.token_hex(8)}")
    cookie = secrets.token_hex(16)
    xvfb = server = observer = window = fresh = xev = None
    xev_out = xev_err = None
    try:
        if socket.exists():
            raise RuntimeError("display_socket_collision")
        command(["xauth", "-f", str(auth), "add", display_name, ".", cookie])
        os.chmod(auth, 0o600)
        xvfb_log = open(out / "xvfb.log", "wb")
        xvfb = subprocess.Popen(["Xvfb", display_name, "-screen", "0", "640x360x24",
                                 "-nolisten", "tcp", "-auth", str(auth), "-noreset"],
                                stdout=xvfb_log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        env = dict(os.environ, DISPLAY=display_name, XAUTHORITY=str(auth))
        os.environ.update({"DISPLAY": display_name, "XAUTHORITY": str(auth)})
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and not socket.exists():
            if xvfb.poll() is not None:
                raise RuntimeError("xvfb_exited_before_socket")
            time.sleep(0.01)
        if not socket.exists():
            raise TimeoutError("xvfb_socket_timeout")
        row["server_map_us"] = server_map_digest(env)
        command(["setxkbmap", "-layout", "us"], env)
        server = display.Display(display_name)
        root = server.screen().root
        window = root.create_window(5, 5, 320, 120, 0, X.CopyFromParent, X.InputOutput,
                                    X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        window.map(); window.set_input_focus(X.RevertToParent, X.CurrentTime); server.sync()
        server_us = server_map_digest(env)
        retained_code = z_code(server)
        retained_map_digest = server_us
        ctrl_code = int(server.keysym_to_keycode(XK.string_to_keysym("Control_L")))
        observer = display.Display(display_name)
        observed_window = observer.create_resource_object("window", window.id)
        observed_window.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
        observer.sync()

        command(["setxkbmap", "-layout", "de"], env)
        server_de = server_map_digest(env)
        fresh = display.Display(display_name)
        fresh_code = z_code(fresh)
        xev_out = open(out / "xev.stdout", "w")
        xev_err = open(out / "xev.stderr", "w")
        xev = subprocess.Popen(["stdbuf", "-oL", "xev", "-id", hex(int(window.id)), "-event", "keyboard"],
                               env=env, stdout=xev_out, stderr=xev_err, text=True,
                               start_new_session=True)
        time.sleep(0.15)
        if xev.poll() is not None:
            raise RuntimeError("xev_observer_exited_before_input")
        decision = "EMIT"
        target_code = retained_code
        emitter = server
        if spec["policy"] == "SNAPSHOT_REFUSE_ON_CHANGE":
            decision = "REFUSE_STALE_MAP" if retained_map_digest != server_de else "EMIT"
            target_code = retained_code
        elif spec["policy"] == "CURRENT_FRESH_MAP":
            target_code = fresh_code
            emitter = fresh
        elif spec["policy"] != "RAW_RETAINED_MAP":
            raise RuntimeError("unknown_policy")

        row.update({"mapping": {"server_us_sha256": server_us,
                                 "server_de_sha256": server_de,
                                 "retained_z_keycode": retained_code,
                                 "fresh_z_keycode": fresh_code,
                                 "control_keycode": ctrl_code,
                                 "server_changed": server_us != server_de,
                                 "retained_map_stale": retained_map_digest != server_de},
                    "decision": decision, "emission_requests": [], "server_events": [],
                    "key_state_after_request": []})
        if decision == "EMIT":
            row["emission_requests"], row["server_events"], row["key_state_after_request"] = emit(
                emitter, observer, display_name, window, ctrl_code, target_code)
        time.sleep(0.1)
        row["terminal_state"] = state(fresh)
        row["app_fixture"] = "bare Xlib window; no toolkit or task semantics"
        row["process_receipts"] = {"xvfb_pid": xvfb.pid, "xvfb_alive_before_cleanup": xvfb.poll() is None,
                                   "xev_pid": xev.pid, "xev_alive_before_cleanup": xev.poll() is None}
        if xev.poll() is None:
            os.kill(xev.pid, signal.SIGTERM)
        xev.wait(timeout=3)
        row["process_receipts"]["xev_exit"] = xev.returncode
        xev_out.flush(); xev_err.flush()
        row["server_events"] = parse_xev(out / "xev.stdout")
        if fresh is not None:
            fresh.close()
            fresh = None
    except Exception as exc:
        row["error"] = repr(exc)
    finally:
        if window is not None and server is not None:
            try: window.destroy(); server.sync()
            except Exception: pass
        if xev is not None and xev.poll() is None:
            try: xev.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try: os.killpg(xev.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: xev.wait(timeout=2)
                except subprocess.TimeoutExpired: xev.kill(); xev.wait()
        if xev_out is not None: xev_out.close()
        if xev_err is not None: xev_err.close()
        for conn in (observer, server, fresh):
            if conn is not None:
                try: conn.close()
                except Exception: pass
        if window is not None:
            try: window.destroy()
            except Exception: pass
        if xvfb is not None and xvfb.poll() is None:
            try:
                os.killpg(xvfb.pid, signal.SIGTERM)
                xvfb.wait(timeout=3)
            except Exception:
                try: os.killpg(xvfb.pid, signal.SIGKILL)
                except Exception: pass
                xvfb.wait()
        if xvfb is not None:
            row.setdefault("process_receipts", {})["xvfb_exit"] = xvfb.returncode
            row["process_receipts"]["xvfb_reaped"] = xvfb.poll() is not None
        if xev is not None:
            row.setdefault("process_receipts", {})["xev_exit"] = xev.returncode
            row["process_receipts"]["xev_reaped"] = xev.poll() is not None
        row["server_events"] = parse_xev(out / "xev.stdout")
        row["socket_absent_after_cleanup"] = not socket.exists()
        try: auth.unlink()
        except FileNotFoundError: pass
        row["auth_file_absent_after_cleanup"] = not auth.exists()
        row["finished_monotonic_ns"] = time.monotonic_ns()
        (out / "ROW.json").write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"index": spec["index"], "policy": spec["policy"],
                      "decision": row.get("decision"), "error": row["error"]}, sort_keys=True))
    if row["error"] is not None:
        raise SystemExit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=int, required=True)
    p.add_argument("--schedule", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    schedule = json.loads(Path(args.schedule).read_text())
    if len(schedule) != 6 or args.index not in range(6):
        raise SystemExit("schedule_contract_error")
    execute(schedule[args.index], Path(args.out))


if __name__ == "__main__":
    main()
