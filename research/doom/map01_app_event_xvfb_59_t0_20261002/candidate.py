"""One-shot XTEST contrast: server-global key state vs app event delivery."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = ROOT / "fixture.json"
FREEZE_PATH = ROOT / "FREEZE.json"
OUT = Path(os.environ.get("OUT", "/tmp/formal-01-raw.json"))
EXPECTED_IMAGE = "sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6"


def now_ns():
    return time.monotonic_ns()


def window_id(value):
    return value.id if hasattr(value, "id") else int(value)


def wait_for_focus(observer, expected, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        actual = window_id(observer.get_input_focus().focus)
        if actual == expected:
            return actual
        select.select([], [], [], 0.005)
    raise RuntimeError(f"focus did not reach expected window {expected}")


def drain_events(app, scenario, rows):
    while app.pending_events():
        event = app.next_event()
        win = getattr(event, "window", None)
        rows.append({
            "scenario": scenario,
            "received_ns": now_ns(),
            "type": int(event.type),
            "detail": int(getattr(event, "detail", 0)),
            "window_id": window_id(win) if win is not None else None,
        })


def wait_for_event(app, scenario, rows, wanted_type, wanted_window, keycode,
                   timeout=2.0):
    from Xlib import X
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        drain_events(app, scenario, rows)
        if any(row["scenario"] == scenario and row["type"] == wanted_type
               and row["window_id"] == wanted_window
               and row["detail"] == keycode for row in rows):
            return True
        ready, _, _ = select.select([app.fileno()], [], [], 0.01)
        if ready:
            continue
    drain_events(app, scenario, rows)
    return any(row["scenario"] == scenario and row["type"] == wanted_type
               and row["window_id"] == wanted_window
               and row["detail"] == keycode for row in rows)


def sample(observer, scenario, label, focused_window, keycode):
    bitmap = observer.query_keymap()
    if isinstance(bitmap, list):
        bitmap = bytes(bitmap)
    else:
        bitmap = bytes(bitmap)
    if len(bitmap) != 32:
        raise RuntimeError(f"XQueryKeymap returned {len(bitmap)} bytes")
    down = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
    actual_focus = window_id(observer.get_input_focus().focus)
    return {
        "scenario": scenario,
        "label": label,
        "observed_ns": now_ns(),
        "focus_window_id": actual_focus,
        "expected_focus_window_id": focused_window,
        "keycode": keycode,
        "key_down": down,
        "bitmap_hex": bitmap.hex(),
    }


def action_log(actions, scenario, action, driver, keycode=None, window=None,
               event_type=None):
    started = now_ns()
    if action == "fake_key":
        from Xlib.ext import xtest
        xtest.fake_input(driver, event_type, keycode)
        driver.sync()
    elif action == "set_focus":
        from Xlib import X
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        driver.sync()
    finished = now_ns()
    actions.append({"scenario": scenario, "ordinal": len(actions) + 1,
                    "action": action,
                    "event_type": event_type,
                    "keycode": keycode,
                    "window_id": window_id(window) if window is not None else None,
                    "started_ns": started, "sync_returned_ns": finished})


def main():
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    source_hashes = {
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
    }
    if any(freeze.get(key) != value for key, value in source_hashes.items()):
        raise RuntimeError("candidate/fixture differs from frozen source hashes")
    image_digest = os.environ.get("IMAGE_DIGEST", "")
    if image_digest != EXPECTED_IMAGE:
        raise RuntimeError("container image digest is absent or differs from freeze")

    from Xlib import X, display
    from Xlib.ext import xtest

    raw = None
    stderr = ""
    xvfb_exit = None
    socket_removed = False
    lock_removed = False
    keycode = None
    proc = None
    display_number = ""
    with tempfile.TemporaryDirectory(prefix="issue59-app-event-") as temp:
        auth = Path(temp) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        argv = ["Xvfb", *fixture["xvfb_args"]]
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        try:
            ready, _, _ = select.select([proc.stdout], [], [], 5.0)
            if not ready:
                raise RuntimeError("private Xvfb did not allocate a display in 5s")
            display_number = proc.stdout.readline().strip()
            if not display_number.isdecimal():
                raise RuntimeError("private Xvfb returned an invalid display number")
            display_name = ":" + display_number
            observer = display.Display(display_name)
            app = display.Display(display_name)
            driver = display.Display(display_name)
            root = app.screen().root
            keycode = observer.keysym_to_keycode(ord("w"))
            if not keycode:
                raise RuntimeError("private Xvfb has no keycode for lowercase W")

            a = root.create_window(10, 10, 160, 100, 0,
                                   X.CopyFromParent, X.InputOutput,
                                   X.CopyFromParent,
                                   event_mask=(X.KeyPressMask | X.KeyReleaseMask |
                                               X.FocusChangeMask))
            b = root.create_window(210, 10, 160, 100, 0,
                                   X.CopyFromParent, X.InputOutput,
                                   X.CopyFromParent,
                                   event_mask=(X.KeyPressMask | X.KeyReleaseMask |
                                               X.FocusChangeMask))
            a.set_wm_name(fixture["window_a_name"])
            b.set_wm_name(fixture["window_b_name"])
            a.map(); b.map(); app.sync()
            aid, bid = a.id, b.id
            all_events = []
            samples = []
            actions = []
            event_checks = {}

            # Positive control: the target remains focused for the whole pulse.
            scenario = "stable_focus_positive_control"
            action_log(actions, scenario, "set_focus", app, window=a)
            wait_for_focus(observer, aid)
            samples.append(sample(observer, scenario, "pre_down", aid, keycode))
            action_log(actions, scenario, "fake_key", driver, keycode=keycode,
                       event_type=X.KeyPress)
            event_checks["a_positive_keypress"] = wait_for_event(
                app, scenario, all_events, X.KeyPress, aid, keycode)
            samples.append(sample(observer, scenario, "post_down", aid, keycode))
            action_log(actions, scenario, "fake_key", driver, keycode=keycode,
                       event_type=X.KeyRelease)
            event_checks["a_positive_keyrelease"] = wait_for_event(
                app, scenario, all_events, X.KeyRelease, aid, keycode)
            samples.append(sample(observer, scenario, "post_up", aid, keycode))
            drain_events(app, scenario, all_events)

            # Contrast: transfer focus during one still-down server key interval.
            scenario = "focus_transfer_while_key_down"
            action_log(actions, scenario, "set_focus", app, window=a)
            wait_for_focus(observer, aid)
            samples.append(sample(observer, scenario, "pre_down", aid, keycode))
            action_log(actions, scenario, "fake_key", driver, keycode=keycode,
                       event_type=X.KeyPress)
            event_checks["a_transfer_keypress"] = wait_for_event(
                app, scenario, all_events, X.KeyPress, aid, keycode)
            samples.append(sample(observer, scenario, "post_down_a_focused",
                                  aid, keycode))
            action_log(actions, scenario, "set_focus", app, window=b)
            wait_for_focus(observer, bid)
            samples.append(sample(observer, scenario, "still_down_b_focused",
                                  bid, keycode))
            # Give the app connection one bounded turn to receive any B press.
            ready, _, _ = select.select([app.fileno()], [], [], 0.05)
            if ready:
                drain_events(app, scenario, all_events)
            b_presses_before_release = [row for row in all_events
                if row["scenario"] == scenario and row["type"] == X.KeyPress
                and row["window_id"] == bid and row["detail"] == keycode]
            action_log(actions, scenario, "fake_key", driver, keycode=keycode,
                       event_type=X.KeyRelease)
            event_checks["b_transfer_keyrelease"] = wait_for_event(
                app, scenario, all_events, X.KeyRelease, bid, keycode)
            samples.append(sample(observer, scenario, "post_up_b_focused",
                                  bid, keycode))
            drain_events(app, scenario, all_events)

            raw = {
                "schema": "issue59-x11-app-delivery-raw-v1",
                "allocation_id": fixture["allocation_id"],
                "source_main_sha": fixture["main_sha"],
                "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                "candidate_sha256": source_hashes["candidate_sha256"],
                "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
                "image_digest": image_digest,
                "candidate_invocations": 1,
                "retries": 0,
                "xvfb_argv": argv,
                "xvfb_tcp_enabled": False,
                "display_number": int(display_number),
                "xvfb_pid": proc.pid,
                "key_name": "W",
                "keycode": keycode,
                "window_a_id": aid,
                "window_b_id": bid,
                "event_checks": event_checks,
                "actions": actions,
                "b_keypress_count_while_down": len(b_presses_before_release),
                "samples": samples,
                "application_events": all_events,
                "scope": "private Xvfb + XTEST virtual protocol; no physical input or semantic app effect",
            }
            observer.close(); app.close(); driver.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
            xvfb_exit = proc.returncode
            stderr = proc.stderr.read() if proc.stderr else ""
            if display_number.isdecimal():
                socket_removed = not (Path("/tmp/.X11-unix") /
                                      ("X" + display_number)).exists()
                lock_removed = not (Path("/tmp") /
                                    (".X" + display_number + "-lock")).exists()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()

    if raw is None:
        raise RuntimeError("candidate ended without a complete raw record")
    raw.update({"xvfb_exit_code_after_controlled_terminate": xvfb_exit,
                "xvfb_socket_removed": socket_removed,
                "xvfb_lock_removed": lock_removed,
                "xvfb_stderr_fatal": "Fatal server error" in stderr,
                "xvfb_stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"schema": raw["schema"], "allocation_id": raw["allocation_id"],
                      "samples": len(raw["samples"]),
                      "events": len(raw["application_events"]),
                      "raw_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()},
                     sort_keys=True))


if __name__ == "__main__":
    main()
