"""One-shot Xvfb diagnostic for Xlib-buffered events vs fd readiness.

Scope: private Xvfb and synthetic XTEST only. No game, model, desktop window,
physical input, task effect, or live allocation.
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import Xlib
from Xlib import X, XK, display
from Xlib.ext import xtest


HERE = Path(__file__).resolve().parent
DISPLAY_NAME = ":189"
KEYSYM = "a"
TIMEOUT_SECONDS = 0.1


def wait_display(server):
    deadline = time.monotonic() + 5.0
    last_error = None
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Xvfb exited: " + server.stderr.read().decode("utf-8", "replace"))
        try:
            return display.Display(DISPLAY_NAME)
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(0.05)
    raise TimeoutError("Xvfb startup timeout: " + str(last_error))


def drain(conn):
    drained = []
    while conn.pending_events():
        event = conn.next_event()
        drained.append(int(event.type))
    return drained


def collect_one(conn, expected_type, expected_keycode, expected_window):
    ready, _, _ = select.select([conn.fileno()], [], [], TIMEOUT_SECONDS)
    pending = conn.pending_events()
    found = []
    while conn.pending_events():
        event = conn.next_event()
        record = {"type": int(event.type), "window": int(getattr(event, "window", 0).id)
                  if hasattr(getattr(event, "window", None), "id") else None,
                  "detail": int(getattr(event, "detail", -1))}
        found.append(record)
    matched = any(row["type"] == expected_type and row["detail"] == expected_keycode
                  and row["window"] == expected_window for row in found)
    return {"fd_select_ready": bool(ready), "xlib_pending_before_drain": pending,
            "events": found, "expected_type": expected_type,
            "expected_keycode": expected_keycode, "expected_window": expected_window,
            "expected_event_found": matched}


def run_case(label, query_mode):
    event_conn = display.Display(DISPLAY_NAME)
    driver = display.Display(DISPLAY_NAME)
    query_conn = event_conn if query_mode == "same" else (
        display.Display(DISPLAY_NAME) if query_mode == "separate" else None
    )
    try:
        screen = event_conn.screen()
        window = screen.root.create_window(
            20, 20, 180, 90, 0, screen.root_depth, X.InputOutput,
            X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        event_conn.sync()
        event_conn.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        event_conn.sync()
        if event_conn.get_input_focus().focus.id != window.id:
            raise RuntimeError(label + ": focus mismatch")
        setup_events = drain(event_conn)
        keycode = event_conn.keysym_to_keycode(XK.string_to_keysym(KEYSYM))
        if not keycode:
            raise RuntimeError(label + ": keycode unavailable")

        xtest.fake_input(driver, X.KeyPress, keycode)
        driver.sync()
        keymap_down = None
        if query_conn is not None:
            bitmap = query_conn.query_keymap()
            keymap_down = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
        press = collect_one(event_conn, X.KeyPress, keycode, int(window.id))

        xtest.fake_input(driver, X.KeyRelease, keycode)
        driver.sync()
        keymap_up = None
        if query_conn is not None:
            bitmap = query_conn.query_keymap()
            keymap_up = not bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
        release = collect_one(event_conn, X.KeyRelease, keycode, int(window.id))
        return {"case": label, "query_mode": query_mode, "setup_events_drained": setup_events,
                "keymap_down_seen": keymap_down, "press": press,
                "keymap_up_seen": keymap_up, "release": release}
    finally:
        if query_conn is not None and query_conn is not event_conn:
            query_conn.close()
        driver.close()
        event_conn.close()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    actual_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if actual_hash != freeze["probe_sha256"]:
        raise SystemExit("probe hash mismatch")
    server = subprocess.Popen(
        ["Xvfb", DISPLAY_NAME, "-screen", "0", "640x480x24", "-nolisten", "tcp", "-noreset", "-ac"],
        env={**os.environ, "DISPLAY": DISPLAY_NAME}, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    result = {"schema": "xvfb-xlib-select-buffering-a03-v1", "status": "STOP",
              "source_sha256": actual_hash, "display": DISPLAY_NAME,
              "scope": "private Xvfb; synthetic XTEST only; no game/model/physical input/task effect",
              "python": sys.version.split()[0],
              "python_xlib": getattr(Xlib, "__version__", "unknown"),
              "cases": [], "error": None}
    try:
        bootstrap = wait_display(server)
        bootstrap.close()
        result["xvfb_version"] = subprocess.run(
            ["Xvfb", "-version"], capture_output=True, text=True, check=False
        ).stderr.strip().splitlines()[:2]
        result["cases"] = [
            run_case("select-first", None),
            run_case("same-connection-query-first", "same"),
            run_case("separate-query-connection-first", "separate"),
        ]
        result["status"] = "PASS_METHOD_SCOPED"
    except Exception as exc:
        result["error"] = repr(exc)
    finally:
        try:
            server.terminate()
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        result["xvfb_exit"] = server.returncode
        result["xvfb_stopped"] = server.poll() is not None
    checks = []
    for case in result["cases"]:
        checks.extend([case["press"]["expected_event_found"], case["release"]["expected_event_found"]])
    if result["error"] is not None or not all(checks) or len(checks) != 6 or not result["xvfb_stopped"]:
        result["status"] = "FAIL_DIAGNOSTIC_CONTRACT"
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
