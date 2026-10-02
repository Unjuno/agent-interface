"""One-shot private-Xvfb test of autorepeat delivery across focus transfer."""
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
IMAGE = "sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6"


def tick():
    return time.monotonic_ns()


def wid(value):
    return value.id if hasattr(value, "id") else int(value)


def keymap(observer, code, label, phase, expected_focus):
    bitmap = bytes(observer.query_keymap())
    if len(bitmap) != 32:
        raise RuntimeError("XQueryKeymap did not return 32 bytes")
    actual_focus = wid(observer.get_input_focus().focus)
    return {"label": label, "phase": phase, "observed_ns": tick(),
            "focus_window_id": actual_focus,
            "expected_focus_window_id": expected_focus, "keycode": code,
            "key_down": bool(bitmap[code // 8] & (1 << (code % 8))),
            "bitmap_hex": bitmap.hex()}


def drain(app, events, phase):
    while app.pending_events():
        event = app.next_event()
        win = getattr(event, "window", None)
        events.append({"phase": phase, "received_ns": tick(),
                       "type": int(event.type),
                       "detail": int(getattr(event, "detail", 0)),
                       "window_id": wid(win) if win is not None else None})


def observe(app, events, phase, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        drain(app, events, phase)
        remaining = deadline - time.monotonic()
        if remaining > 0:
            select.select([app.fileno()], [], [], min(0.01, remaining))
    drain(app, events, phase)


def main():
    from Xlib import X, display
    from Xlib.ext import xtest

    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    candidate_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    if freeze.get("candidate_sha256") != candidate_hash:
        raise RuntimeError("candidate hash differs from frozen source")
    if freeze.get("fixture_sha256") != fixture_hash:
        raise RuntimeError("fixture hash differs from frozen source")
    if freeze.get("image_digest") != IMAGE:
        raise RuntimeError("image digest differs from frozen identity")

    raw = None
    proc = None
    display_number = ""
    with tempfile.TemporaryDirectory(prefix="issue59-held-repeat-") as temp:
        auth = Path(temp) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        argv = ["Xvfb", *fixture["xvfb_args"]]
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        try:
            ready, _, _ = select.select([proc.stdout], [], [], 5.0)
            if not ready:
                raise RuntimeError("Xvfb display allocation timed out")
            display_number = proc.stdout.readline().strip()
            if not display_number.isdecimal():
                raise RuntimeError("Xvfb returned invalid display number")
            name = ":" + display_number
            observer, app, driver = (display.Display(name) for _ in range(3))
            root = app.screen().root
            code = observer.keysym_to_keycode(ord("w"))
            if not code:
                raise RuntimeError("W keycode unavailable")
            a = root.create_window(10, 10, 160, 100, 0,
                X.CopyFromParent, X.InputOutput, X.CopyFromParent,
                event_mask=X.KeyPressMask | X.KeyReleaseMask | X.FocusChangeMask)
            b = root.create_window(210, 10, 160, 100, 0,
                X.CopyFromParent, X.InputOutput, X.CopyFromParent,
                event_mask=X.KeyPressMask | X.KeyReleaseMask | X.FocusChangeMask)
            a.set_wm_name(fixture["window_a_name"])
            b.set_wm_name(fixture["window_b_name"])
            a.map(); b.map(); app.sync()
            aid, bid = a.id, b.id
            events, samples, actions = [], [], []

            def act(phase, operation, window=None, event_type=None):
                start = tick()
                if operation == "focus":
                    window.set_input_focus(X.RevertToParent, X.CurrentTime)
                    app.sync()
                else:
                    xtest.fake_input(driver, event_type, code)
                    driver.sync()
                actions.append({"phase": phase, "operation": operation,
                    "event_type": event_type, "keycode": code,
                    "window_id": wid(window) if window is not None else None,
                    "started_ns": start, "sync_returned_ns": tick()})

            def focus(window, phase):
                act(phase, "focus", window=window)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    if wid(observer.get_input_focus().focus) == window.id:
                        return
                    select.select([], [], [], 0.005)
                raise RuntimeError("focus did not reach requested window")

            ctrl = observer.get_keyboard_control()
            repeat = {"global_auto_repeat": int(ctrl.global_auto_repeat),
                      "auto_repeats_hex": bytes(ctrl.auto_repeats).hex()}

            # Positive control: prove Xvfb's default repeat stream is observable.
            focus(a, "positive")
            samples.append(keymap(observer, code, "positive_pre", "positive", aid))
            act("positive", "press", event_type=X.KeyPress)
            observe(app, events, "positive_held", fixture["hold_seconds"])
            samples.append(keymap(observer, code, "positive_held", "positive", aid))
            act("positive", "release", event_type=X.KeyRelease)
            observe(app, events, "positive_release", 0.05)
            samples.append(keymap(observer, code, "positive_post", "positive", aid))

            # Transfer focus while the same server-global key remains down.
            focus(a, "transfer")
            samples.append(keymap(observer, code, "transfer_pre", "transfer", aid))
            act("transfer", "press", event_type=X.KeyPress)
            observe(app, events, "transfer_a_held", 0.05)
            a_initial = any(e["phase"] == "transfer_a_held" and
                e["type"] == X.KeyPress and e["window_id"] == aid and
                e["detail"] == code for e in events)
            samples.append(keymap(observer, code, "transfer_a_held", "transfer", aid))
            focus(b, "transfer")
            b_focus_sample = keymap(observer, code, "transfer_b_held", "transfer", bid)
            samples.append(b_focus_sample)
            observe(app, events, "transfer_b_held", fixture["hold_seconds"])
            transfer_observe_end_ns = tick()
            samples.append(keymap(observer, code, "transfer_b_end", "transfer", bid))
            act("transfer", "release", event_type=X.KeyRelease)
            release_action_ns = actions[-1]["sync_returned_ns"]
            observe(app, events, "transfer_release", 0.05)
            samples.append(keymap(observer, code, "transfer_post", "transfer", bid))

            raw = {"schema": "issue59-x11-held-repeat-raw-v1",
                "allocation_id": fixture["allocation_id"],
                "main_sha": fixture["main_sha"], "image_digest": IMAGE,
                "candidate_sha256": candidate_hash,
                "fixture_sha256": fixture_hash,
                "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
                "candidate_invocations": 1, "retries": 0,
                "xvfb_argv": argv, "xvfb_tcp_enabled": False,
                "display_number": int(display_number), "xvfb_pid": proc.pid,
                "window_a_id": aid, "window_b_id": bid, "key_name": "W",
                "keycode": code, "repeat_control": repeat,
                "hold_seconds": fixture["hold_seconds"],
                "transfer_b_start_ns": b_focus_sample["observed_ns"],
                "transfer_observe_end_ns": transfer_observe_end_ns,
                "transfer_release_action_ns": release_action_ns,
                "a_received_initial_transfer_press": a_initial,
                "samples": samples, "actions": actions, "events": events,
                "scope": "private Xvfb/XTEST protocol delivery only"}
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
            else:
                socket_removed = lock_removed = False
    raw["xvfb_exit_code"] = xvfb_exit
    raw["xvfb_socket_removed"] = socket_removed
    raw["xvfb_lock_removed"] = lock_removed
    raw["xvfb_stderr"] = stderr
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"allocation_id": raw["allocation_id"],
        "a_initial_press": a_initial,
        "a_transfer_repeats": sum(e["phase"] == "transfer_a_held" and
            e["type"] == 2 and e["window_id"] == aid and e["detail"] == code
            for e in events),
        "b_transfer_keypresses": sum(e["phase"] == "transfer_b_held" and
            e["type"] == 2 and e["window_id"] == bid and e["detail"] == code
            for e in events), "xvfb_exit_code": xvfb_exit,
        "socket_removed": socket_removed, "lock_removed": lock_removed},
        sort_keys=True))


if __name__ == "__main__":
    main()
