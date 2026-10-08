#!/usr/bin/env python3
"""Run one isolated Shift press/release with two-source explicit provenance."""
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


def read_records(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line:
            rows.append(json.loads(line))
    return rows


def wait_for(predicate, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
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
    app_path = out / "app_events.jsonl"
    observer_path = out / "observer_events.jsonl"
    actions_path = out / "actions.jsonl"
    app = observer = None
    driver_seq = 0

    def action(phase, actuation_id=None, **fields):
        nonlocal driver_seq
        driver_seq += 1
        append(
            actions_path,
            {
                "driver_seq": driver_seq,
                "phase": phase,
                "actuation_id": actuation_id,
                "mono_ns": time.monotonic_ns(),
                **fields,
            },
        )

    try:
        app = subprocess.Popen(
            [sys.executable, str(args.app), str(out / "tk")],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        state_path = out / "tk" / "state.json"
        app_state = wait_for(lambda: json.loads(state_path.read_text()) if state_path.exists() else None)
        app_state = wait_for(
            lambda: (json.loads(state_path.read_text()) if state_path.exists() else {}).get("focus_widget")
            and json.loads(state_path.read_text())
        )
        epoch = "t2-" + uuid.uuid4().hex
        observer = subprocess.Popen(
            [sys.executable, str(args.observer), str(app_state["entry_xid"]), epoch, str(observer_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        ready = wait_for(
            lambda: observer.stdout.readline().strip() if select.select([observer.stdout], [], [], 0)[0] else None
        )
        ready_record = json.loads(ready)
        if not ready_record.get("ready") or ready_record.get("epoch") != epoch:
            raise RuntimeError("observer bootstrap identity mismatch")
        xdisplay = display.Display()
        keycode = xdisplay.keysym_to_keycode(XK.XK_Shift_L)
        if not keycode:
            raise RuntimeError("Shift_L keycode unavailable")
        actions = []

        for ordinal, event_kind in enumerate(("KeyPress", "KeyRelease"), start=1):
            actuation_id = f"{epoch}:shift-{ordinal}"
            action("arm_request", actuation_id, event_kind=event_kind, keycode=keycode)
            command = f"arm:{actuation_id}\n"
            app.stdin.write(command)
            app.stdin.flush()
            observer.stdin.write(command)
            observer.stdin.flush()
            app_ack = wait_for(
                lambda: next(
                    (r for r in read_records(app_path) if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id),
                    None,
                )
            )
            observer_ack = wait_for(
                lambda: next(
                    (r for r in read_records(observer_path) if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id),
                    None,
                )
            )
            action("both_armed", actuation_id, consumers=["app", "observer"])
            action("dispatch_request", actuation_id, event_kind=event_kind, keycode=keycode)
            xtest.fake_input(xdisplay, X.KeyPress if event_kind == "KeyPress" else X.KeyRelease, detail=keycode)
            xdisplay.sync()
            action("dispatch_sync_complete", actuation_id, event_kind=event_kind, keycode=keycode)
            app_event = wait_for(
                lambda: next(
                    (r for r in read_records(app_path) if r.get("source") == "app" and r.get("actuation_id") == actuation_id),
                    None,
                )
            )
            observer_event = wait_for(
                lambda: next(
                    (r for r in read_records(observer_path) if r.get("source") == "observer" and r.get("actuation_id") == actuation_id),
                    None,
                )
            )
            actions.append(
                {
                    "actuation_id": actuation_id,
                    "event_kind": event_kind,
                    "keycode": keycode,
                    "app_ack_seen": bool(app_ack),
                    "observer_ack_seen": bool(observer_ack),
                    "app_event_seen": bool(app_event),
                    "observer_event_seen": bool(observer_event),
                }
            )
        keymap = bytes(xdisplay.query_keymap())
        shift_down = bool(keymap[keycode >> 3] & (1 << (keycode & 7)))
        action("terminal_keymap", None, keycode=keycode, shift_down=shift_down)
        xdisplay.close()
        observer.stdin.write("stop\n")
        observer.stdin.flush()
        observer.wait(timeout=3)
        app.stdin.write("stop\n")
        app.stdin.flush()
        app.stdin.close()
        app.wait(timeout=3)
        result = {
            "schema": "blackstart-prospective-x11-trace-run-v1",
            "status": "RUN_COMPLETE" if all(a["app_event_seen"] and a["observer_event_seen"] for a in actions) and not shift_down else "RUN_INCOMPLETE",
            "display": os.environ.get("DISPLAY"),
            "epoch": epoch,
            "entry_xid": app_state["entry_xid"],
            "keycode": keycode,
            "actions": actions,
            "terminal_shift_down": shift_down,
            "app_returncode": app.returncode,
            "observer_returncode": observer.returncode,
        }
        (out / "run.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0 if result["status"] == "RUN_COMPLETE" else 2
    except Exception as exc:
        action("runner_exception", None, error=type(exc).__name__, message=str(exc))
        (out / "run.raw.json").write_text(
            json.dumps({"schema": "blackstart-prospective-x11-trace-run-v1", "status": "STOP", "error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 2
    finally:
        for proc in (observer, app):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
