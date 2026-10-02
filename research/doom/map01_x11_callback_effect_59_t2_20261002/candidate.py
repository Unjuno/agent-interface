"""One-shot Xvfb app-callback counter experiment for Issue #59."""
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


def sample(observer, code, label, phase, focus_id):
    bitmap = bytes(observer.query_keymap())
    if len(bitmap) != 32:
        raise RuntimeError("XQueryKeymap did not return 32 bytes")
    actual_focus = wid(observer.get_input_focus().focus)
    return {"label": label, "phase": phase, "observed_ns": tick(),
            "focus_window_id": actual_focus,
            "expected_focus_window_id": focus_id, "keycode": code,
            "key_down": bool(bitmap[code // 8] & (1 << (code % 8))),
            "bitmap_hex": bitmap.hex()}


def main():
    from Xlib import X, display
    from Xlib.ext import xtest

    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    candidate_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    if freeze.get("candidate_sha256") != candidate_hash or freeze.get("fixture_sha256") != fixture_hash:
        raise RuntimeError("candidate/fixture differs from frozen source hashes")
    if freeze.get("image_digest") != IMAGE:
        raise RuntimeError("frozen image digest mismatch")

    proc = None
    display_number = ""
    with tempfile.TemporaryDirectory(prefix="issue59-callback-effect-") as temp:
        auth = Path(temp) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        argv = ["Xvfb", *fixture["xvfb_args"]]
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        try:
            ready, _, _ = select.select([proc.stdout], [], [], 5.0)
            if not ready:
                raise RuntimeError("private Xvfb display allocation timed out")
            display_number = proc.stdout.readline().strip()
            if not display_number.isdecimal():
                raise RuntimeError("Xvfb returned invalid display number")
            name = ":" + display_number
            observer, app, driver = (display.Display(name) for _ in range(3))
            root = app.screen().root
            code = observer.keysym_to_keycode(ord("w"))
            if not code:
                raise RuntimeError("W keycode unavailable")
            mask = X.KeyPressMask | X.KeyReleaseMask | X.FocusChangeMask
            a = root.create_window(10, 10, 160, 100, 0,
                X.CopyFromParent, X.InputOutput, X.CopyFromParent, event_mask=mask)
            b = root.create_window(210, 10, 160, 100, 0,
                X.CopyFromParent, X.InputOutput, X.CopyFromParent, event_mask=mask)
            a.set_wm_name(fixture["window_a_name"])
            b.set_wm_name(fixture["window_b_name"])
            a.map(); b.map(); app.sync()
            aid, bid = a.id, b.id
            effects = {aid: 0, bid: 0}
            events, effect_rows, samples, actions = [], [], [], []

            def drain(phase):
                while app.pending_events():
                    event = app.next_event()
                    target = getattr(event, "window", None)
                    target_id = wid(target) if target is not None else None
                    row = {"event_id": len(events), "phase": phase,
                        "received_ns": tick(), "type": int(event.type),
                        "detail": int(getattr(event, "detail", 0)),
                        "window_id": target_id}
                    events.append(row)
                    # This is the explicitly defined client-side effect handler.
                    if event.type == X.KeyPress and event.detail == code and target_id in effects:
                        bitmap = bytes(observer.query_keymap())
                        current_focus = wid(observer.get_input_focus().focus)
                        before = effects[target_id]
                        effects[target_id] += 1
                        effect_rows.append({"effect_id": len(effect_rows),
                            "event_id": row["event_id"], "phase": phase,
                            "event_received_ns": row["received_ns"],
                            "effect_ns": tick(), "window_id": target_id,
                            "keycode": code, "effect_name": fixture["effect_name"],
                            "before": before, "after": effects[target_id],
                            "focus_window_id": current_focus,
                            "key_down": bool(bitmap[code // 8] & (1 << (code % 8))),
                            "bitmap_hex": bitmap.hex()})

            def observe(phase, seconds):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    drain(phase)
                    left = deadline - time.monotonic()
                    if left > 0:
                        select.select([app.fileno()], [], [], min(0.01, left))
                drain(phase)

            def action(phase, operation, window=None, event_type=None):
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
                action(phase, "focus", window=window)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    if wid(observer.get_input_focus().focus) == window.id:
                        return
                    select.select([], [], [], 0.005)
                raise RuntimeError("focus did not reach target window")

            repeat = observer.get_keyboard_control()
            repeat_state = {"global_auto_repeat": int(repeat.global_auto_repeat),
                            "auto_repeats_hex": bytes(repeat.auto_repeats).hex()}

            # Stable-focus positive control: real callback counter increments.
            focus(a, "positive")
            samples.append(sample(observer, code, "positive_pre", "positive", aid))
            action("positive", "press", event_type=X.KeyPress)
            observe("positive_held", fixture["hold_seconds"])
            samples.append(sample(observer, code, "positive_held", "positive", aid))
            action("positive", "release", event_type=X.KeyRelease)
            observe("positive_release", 0.05)
            samples.append(sample(observer, code, "positive_post", "positive", aid))

            # Focus transfer while global key state remains down.
            focus(a, "transfer")
            samples.append(sample(observer, code, "transfer_pre", "transfer", aid))
            action("transfer", "press", event_type=X.KeyPress)
            observe("transfer_a_held", 0.05)
            a_initial = any(e["phase"] == "transfer_a_held" and e["type"] == X.KeyPress and
                e["window_id"] == aid and e["detail"] == code for e in events)
            samples.append(sample(observer, code, "transfer_a_held", "transfer", aid))
            focus(b, "transfer")
            b_start = sample(observer, code, "transfer_b_held", "transfer", bid)
            samples.append(b_start)
            observe("transfer_b_held", fixture["hold_seconds"])
            b_end_ns = tick()
            samples.append(sample(observer, code, "transfer_b_end", "transfer", bid))
            action("transfer", "release", event_type=X.KeyRelease)
            release_ns = actions[-1]["sync_returned_ns"]
            observe("transfer_release", 0.05)
            samples.append(sample(observer, code, "transfer_post", "transfer", bid))
            effects_snapshot = {str(k): v for k, v in effects.items()}
            observer.close(); app.close(); driver.close()
        finally:
            if proc.poll() is None:
                proc.terminate(); proc.wait(timeout=3)
            xvfb_exit = proc.returncode
            stderr = proc.stderr.read() if proc.stderr else ""
            if display_number.isdecimal():
                socket_removed = not (Path("/tmp/.X11-unix") / ("X" + display_number)).exists()
                lock_removed = not (Path("/tmp") / (".X" + display_number + "-lock")).exists()
            else:
                socket_removed = lock_removed = False

    raw = {"schema": "issue59-x11-callback-effect-raw-v1",
        "allocation_id": fixture["allocation_id"], "main_sha": fixture["main_sha"],
        "image_digest": IMAGE, "candidate_sha256": candidate_hash,
        "fixture_sha256": fixture_hash,
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "candidate_invocations": 1, "retries": 0, "xvfb_argv": argv,
        "xvfb_tcp_enabled": False, "xvfb_exit_code": xvfb_exit,
        "xvfb_socket_removed": socket_removed, "xvfb_lock_removed": lock_removed,
        "xvfb_stderr": stderr, "window_a_id": aid, "window_b_id": bid,
        "key_name": "W", "keycode": code, "repeat_control": repeat_state,
        "hold_seconds": fixture["hold_seconds"], "samples": samples,
        "actions": actions, "events": events, "callback_effects": effect_rows,
        "effects_final": effects_snapshot, "a_received_initial_transfer_press": a_initial,
        "transfer_b_start_ns": b_start["observed_ns"],
        "transfer_b_end_ns": b_end_ns, "transfer_release_action_ns": release_ns,
        "effect_name": fixture["effect_name"],
        "effect_semantics": "in-memory per-window movement_tick_counter += 1 for every delivered W KeyPress",
        "scope": "private Xvfb/XTEST and minimal client callback state only"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": raw["allocation_id"],
        "positive_a_callbacks": sum(e["phase"] == "positive_held" and e["window_id"] == aid for e in effect_rows),
        "transfer_a_callbacks": sum(e["phase"] == "transfer_a_held" and e["window_id"] == aid for e in effect_rows),
        "transfer_b_callbacks": sum(e["phase"] == "transfer_b_held" and e["window_id"] == bid for e in effect_rows),
        "effects_final": effects_snapshot, "xvfb_exit_code": xvfb_exit,
        "socket_removed": socket_removed, "lock_removed": lock_removed}, sort_keys=True))


if __name__ == "__main__":
    main()
