from __future__ import annotations

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


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def wait_for(predicate, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        item = predicate()
        if item:
            return item
        time.sleep(0.01)
    raise TimeoutError("bounded fixture wait expired")


def main() -> int:
    out = Path(sys.argv[1]).resolve()
    app_script = Path(sys.argv[2]).resolve()
    observer_script = Path(sys.argv[3]).resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=True)
    tkout = out / "tk"
    app_log = tkout / "app_events.jsonl"
    obs_log = out / "observer_events.jsonl"
    actions_log = out / "actions.jsonl"
    plan_file = out / "actions.json"
    epoch = "t3-" + uuid.uuid4().hex
    keycode = 0
    xdisplay = app = observer = None
    release_attempted = False
    terminal_neutral = None
    error = None

    def log(phase, **extra):
        with actions_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"phase": phase, "mono_ns": time.monotonic_ns(), **extra}, sort_keys=True) + "\n")

    ids = {kind: f"{epoch}:{kind.lower()}" for kind in ("KeyPress", "KeyRelease")}
    plan_file.write_text(json.dumps({"by_kind": {kind: {"seq": i, "actuation_id": act} for i, (kind, act) in enumerate(ids.items(), 1)}}, sort_keys=True))
    try:
        app = subprocess.Popen([sys.executable, str(app_script), str(tkout), str(plan_file)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        state_file = tkout / "state.json"
        state = wait_for(lambda: json.loads(state_file.read_text()) if state_file.exists() else None)
        state = wait_for(lambda: (s if (s := (json.loads(state_file.read_text()) if state_file.exists() else {})).get("focus_widget") else None))
        observer = subprocess.Popen([sys.executable, str(observer_script), str(state["entry_xid"]), epoch, str(obs_log), str(plan_file)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        ready_line = wait_for(lambda: observer.stdout.readline().strip() if select.select([observer.stdout], [], [], 0)[0] else None)
        ready = json.loads(ready_line)
        if ready.get("ready") is not True or ready.get("epoch") != epoch:
            raise RuntimeError("OBSERVER_BOOTSTRAP_NOT_READY")
        xdisplay = display.Display()
        keycode = xdisplay.keysym_to_keycode(XK.XK_Shift_L)
        if not keycode:
            raise RuntimeError("SHIFT_KEYCODE_MISSING")
        log("press_dispatch", actuation_id=ids["KeyPress"], keycode=keycode)
        xtest.fake_input(xdisplay, X.KeyPress, detail=keycode)
        xdisplay.sync()
        press_rows = wait_for(lambda: (a, b) if (a := next((r for r in rows(app_log) if r.get("actuation_id") == ids["KeyPress"]), None)) and (b := next((r for r in rows(obs_log) if r.get("actuation_id") == ids["KeyPress"]), None)) else None)
        log("press_pair_observed", app_event_id=press_rows[0].get("event_id"), observer_event_id=press_rows[1].get("event_id"))
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        log("candidate_error", error=error)
    finally:
        # Always send the matching release on the isolated X server, even if press evidence is missing.
        if xdisplay is not None and keycode:
            try:
                log("release_dispatch_cleanup", actuation_id=ids["KeyRelease"], keycode=keycode)
                xtest.fake_input(xdisplay, X.KeyRelease, detail=keycode)
                xdisplay.sync()
                release_attempted = True
                try:
                    wait_for(lambda: (a, b) if (a := next((r for r in rows(app_log) if r.get("actuation_id") == ids["KeyRelease"]), None)) and (b := next((r for r in rows(obs_log) if r.get("actuation_id") == ids["KeyRelease"]), None)) else None, timeout=2.0)
                except Exception as exc:
                    log("release_pair_missing", error=type(exc).__name__)
                km = bytes(xdisplay.query_keymap())
                terminal_neutral = not bool(km[keycode >> 3] & (1 << (keycode & 7)))
                log("terminal_keymap", shift_down=not terminal_neutral)
            except Exception as exc:
                log("cleanup_error", error=type(exc).__name__, message=str(exc))
        if observer is not None and observer.poll() is None:
            try:
                observer.stdin.write("stop\n"); observer.stdin.flush(); observer.wait(timeout=2)
            except Exception:
                observer.terminate(); observer.wait(timeout=2)
        if app is not None and app.poll() is None:
            app.terminate()
            try:
                app.wait(timeout=2)
            except subprocess.TimeoutExpired:
                app.kill(); app.wait(timeout=2)
        if xdisplay is not None:
            xdisplay.close()
    result = {"schema": "blackstart-source-bound-t3-run-v1", "epoch": epoch, "keycode": keycode,
              "app_rows": rows(app_log), "observer_rows": rows(obs_log), "driver_rows": rows(actions_log),
              "release_attempted": release_attempted, "terminal_neutral": terminal_neutral, "error": error,
              "app_returncode": app.returncode if app else None, "observer_returncode": observer.returncode if observer else None}
    (out / "run.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if release_attempted and terminal_neutral is True and error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
