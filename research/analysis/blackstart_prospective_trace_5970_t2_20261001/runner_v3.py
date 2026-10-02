#!/usr/bin/env python3
"""Corrected one-shot X11/Tk driver: reads app log under its actual tk/ path."""
import argparse
import json
import os
import select
import subprocess
import sys
import time
import uuid
from pathlib import Path

from Xlib import X, XK, display
from Xlib.ext import xtest


def append(path, record):
    with path.open("a", encoding="utf-8", buffering=1) as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.01)
    raise TimeoutError("timed out waiting for isolated fixture state")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--observer", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP: run output directory is not empty")
    out.mkdir(parents=True, exist_ok=True)
    tk_out = out / "tk"
    app_path = tk_out / "app_events.jsonl"
    observer_path = out / "observer_events.jsonl"
    actions_path = out / "actions.jsonl"
    app = observer = xdisplay = None
    driver_seq = 0

    def log(phase, actuation_id=None, **fields):
        nonlocal driver_seq
        driver_seq += 1
        append(actions_path, {"driver_seq": driver_seq, "phase": phase, "actuation_id": actuation_id, "mono_ns": time.monotonic_ns(), **fields})

    try:
        app = subprocess.Popen([sys.executable, str(args.app), str(tk_out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, bufsize=1)
        state_path = tk_out / "state.json"
        wait_for(lambda: json.loads(state_path.read_text()) if state_path.exists() else None)
        app_state = wait_for(lambda: (json.loads(state_path.read_text()) if state_path.exists() else {}).get("focus_widget") and json.loads(state_path.read_text()))
        epoch = "t2c-" + uuid.uuid4().hex
        observer = subprocess.Popen([sys.executable, str(args.observer), str(app_state["entry_xid"]), epoch, str(observer_path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        ready_line = wait_for(lambda: observer.stdout.readline().strip() if select.select([observer.stdout], [], [], 0)[0] else None)
        ready = json.loads(ready_line)
        if ready.get("ready") is not True or ready.get("epoch") != epoch:
            raise RuntimeError("observer epoch/bootstrap mismatch")
        xdisplay = display.Display()
        keycode = xdisplay.keysym_to_keycode(XK.XK_Shift_L)
        if keycode == 0:
            raise RuntimeError("Shift_L keycode unavailable")
        actions = []
        for ordinal, event_kind in enumerate(("KeyPress", "KeyRelease"), start=1):
            action_id = f"{epoch}:shift-{ordinal}"
            log("arm_request", action_id, event_kind=event_kind, keycode=keycode)
            message = f"arm:{action_id}\n"
            app.stdin.write(message)
            app.stdin.flush()
            observer.stdin.write(message)
            observer.stdin.flush()
            app_ack = wait_for(lambda: next((r for r in read_rows(app_path) if r.get("kind") == "arm_ack" and r.get("actuation_id") == action_id), None))
            observer_ack = wait_for(lambda: next((r for r in read_rows(observer_path) if r.get("kind") == "arm_ack" and r.get("actuation_id") == action_id), None))
            log("both_armed", action_id, consumers=["app", "observer"])
            log("dispatch_request", action_id, event_kind=event_kind, keycode=keycode)
            xtest.fake_input(xdisplay, X.KeyPress if event_kind == "KeyPress" else X.KeyRelease, detail=keycode)
            xdisplay.sync()
            log("dispatch_sync_complete", action_id, event_kind=event_kind, keycode=keycode)
            app_event = wait_for(lambda: next((r for r in read_rows(app_path) if r.get("source") == "app" and r.get("actuation_id") == action_id), None))
            obs_event = wait_for(lambda: next((r for r in read_rows(observer_path) if r.get("source") == "observer" and r.get("actuation_id") == action_id), None))
            actions.append({"actuation_id": action_id, "event_kind": event_kind, "keycode": keycode, "app_ack_seen": bool(app_ack), "observer_ack_seen": bool(observer_ack), "app_event_seen": bool(app_event), "observer_event_seen": bool(obs_event)})
        keymap = bytes(xdisplay.query_keymap())
        terminal_down = bool(keymap[keycode >> 3] & (1 << (keycode & 7)))
        log("terminal_keymap", None, keycode=keycode, shift_down=terminal_down)
        xdisplay.close()
        xdisplay = None
        observer.stdin.write("stop\n")
        observer.stdin.flush()
        observer.wait(timeout=3)
        app.stdin.write("stop\n")
        app.stdin.flush()
        app.stdin.close()
        app.wait(timeout=3)
        result = {"schema": "blackstart-prospective-x11-trace-run-v3", "status": "RUN_COMPLETE" if len(actions) == 2 and all(a["app_event_seen"] and a["observer_event_seen"] for a in actions) and terminal_down is False else "RUN_INCOMPLETE", "display": os.environ.get("DISPLAY"), "epoch": epoch, "entry_xid": app_state["entry_xid"], "keycode": keycode, "actions": actions, "terminal_shift_down": terminal_down, "app_returncode": app.returncode, "observer_returncode": observer.returncode}
        (out / "run.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0 if result["status"] == "RUN_COMPLETE" and app.returncode == 0 and observer.returncode == 0 else 2
    except Exception as exc:
        log("runner_exception", None, error=type(exc).__name__, message=str(exc))
        (out / "run.raw.json").write_text(json.dumps({"schema": "blackstart-prospective-x11-trace-run-v3", "status": "STOP", "error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2
    finally:
        if xdisplay is not None:
            xdisplay.close()
        for proc in (observer, app):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
