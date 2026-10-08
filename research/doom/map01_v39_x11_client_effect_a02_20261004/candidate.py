"""One-shot Xvfb client event and minimal state-effect construction."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time
import types
import uuid

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "dependencies" / "input_owner_v10.py"


class Lease:
    def __init__(self, focus: int, token: str):
        self.expected_focus = focus
        self.intent_token = token
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("finite construction lease expired")


def load_owner():
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor
    spec = importlib.util.spec_from_file_location("a02_input_owner_v10", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen InputOwner v10")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.InputOwner


def keymap_sample(observer, keycode: int, occurrence: str, stage: str) -> dict:
    started = time.perf_counter_ns()
    values = observer.query_keymap()
    finished = time.perf_counter_ns()
    bitmap = bytes(values)
    down = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
    return {
        "occurrence_id": occurrence,
        "stage": stage,
        "sample_started_ns": started,
        "sample_finished_ns": finished,
        "bitmap_length": len(bitmap),
        "bitmap_hex": bitmap.hex(),
        "keycode": keycode,
        "key_down": down,
        "source": "independent Xlib Display.query_keymap",
        "physical_key_up_claimed": False,
    }


def wait_key_event(app_display, window_id: int, keycode: int, event_type: int,
                   timeout: float = 2.0) -> dict:
    from Xlib import X
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if app_display.pending_events():
            event = app_display.next_event()
        else:
            remaining = deadline - time.monotonic()
            ready, _, _ = select.select([app_display.fileno()], [], [], remaining)
            if not ready:
                break
            event = app_display.next_event()
        if event.type not in (X.KeyPress, X.KeyRelease):
            continue
        event_window = getattr(event, "event", None)
        event_window_id = event_window.id if hasattr(event_window, "id") else event_window
        if event.type == event_type and event.detail == keycode and event_window_id == window_id:
            return {
                "event_type": event.type,
                "keycode": event.detail,
                "window_id": event_window_id,
                "server_time_ms": event.time,
                "send_event": bool(event.send_event),
                "received_ns": time.perf_counter_ns(),
            }
    raise TimeoutError(f"client did not receive X event type={event_type} keycode={keycode}")


def run(out: Path) -> dict:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=False)
    from Xlib import X, XK, display

    with tempfile.TemporaryDirectory(prefix="v39-x11-event-a02-") as temporary:
        auth = Path(temporary) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        server = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-ac"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )
        observer = app_display = owner = None
        raw = None
        try:
            ready, _, _ = select.select([server.stdout], [], [], 5)
            if not ready:
                raise RuntimeError("private Xvfb did not allocate a display within 5 s")
            number = server.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("Xvfb returned malformed display number")
            display_name = ":" + number
            observer = display.Display(display_name)
            app_display = display.Display(display_name)
            screen = app_display.screen()
            window = screen.root.create_window(
                20, 20, 320, 120, 0, screen.root_depth, X.InputOutput,
                X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask,
            )
            window.map()
            app_display.sync()
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            app_display.sync()
            observer.sync()
            focus = observer.get_input_focus().focus
            focus_id = focus.id if hasattr(focus, "id") else focus
            if focus_id != window.id:
                raise RuntimeError("event sink did not obtain X input focus")
            code = observer.keysym_to_keycode(XK.string_to_keysym("w"))
            if type(code) is not int or code <= 0:
                raise RuntimeError("Xvfb has no keycode for W")
            owner = load_owner()(display_name)
            initial_state = owner.call("input_state")
            cycles = []
            app_counter = 0

            for index in range(2):
                occurrence = uuid.uuid4().hex
                lease = Lease(window.id, "a02:" + occurrence)
                pre = keymap_sample(observer, code, occurrence, "pre_down")
                down_started = time.perf_counter_ns()
                admission = owner.call("down", lease, "w")
                down_returned = time.perf_counter_ns()
                owner_after_down = owner.call("input_state")
                post_down = keymap_sample(observer, code, occurrence, "post_down")
                press = wait_key_event(app_display, window.id, code, X.KeyPress)
                app_counter += 1
                counter_after_press = app_counter

                up_started = time.perf_counter_ns()
                up_result = owner.call("up", lease, "w")
                up_returned = time.perf_counter_ns()
                release_result = owner.call("release", lease)
                release_returned = time.perf_counter_ns()
                release_event = wait_key_event(app_display, window.id, code, X.KeyRelease)
                post_up = keymap_sample(observer, code, occurrence, "post_up")
                owner_after_up = owner.call("input_state")
                cycles.append({
                    "occurrence_id": occurrence,
                    "key": "w",
                    "keycode": code,
                    "intent_token": lease.intent_token,
                    "owner_id": owner.owner_id,
                    "pre_down": pre,
                    "admission": admission,
                    "down_started_ns": down_started,
                    "down_returned_ns": down_returned,
                    "owner_after_down": owner_after_down,
                    "post_down": post_down,
                    "client_keypress": press,
                    "app_counter_after_press": counter_after_press,
                    "up_started_ns": up_started,
                    "up_returned_ns": up_returned,
                    "up_result": up_result,
                    "owner_release_result": release_result,
                    "owner_release_returned_ns": release_returned,
                    "client_keyrelease": release_event,
                    "post_up": post_up,
                    "owner_after_up": owner_after_up,
                })

            owner.close()
            records = list(owner.records)
            owner = None
            raw = {
                "schema": "v39-x11-client-effect-a02-v1",
                "display_number": int(number),
                "window_id": window.id,
                "keycode": code,
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "initial_owner_state": initial_state,
                "cycles": cycles,
                "app_counter_final": app_counter,
                "owner_records": records,
                "xvfb_running_before_stop": None,
                "xvfb_returncode_after_stop": None,
                "xvfb_stderr": None,
                "cleanup_errors": [],
                "scope": "focused minimal Xlib client event delivery and counter only",
            }
        finally:
            cleanup_errors = []
            if owner is not None:
                try:
                    owner.close()
                except BaseException as exc:
                    cleanup_errors.append("owner_close: " + repr(exc))
            if app_display is not None:
                try:
                    app_display.close()
                except BaseException as exc:
                    cleanup_errors.append("app_close: " + repr(exc))
            if observer is not None:
                try:
                    observer.close()
                except BaseException as exc:
                    cleanup_errors.append("observer_close: " + repr(exc))
            running = server.poll() is None
            if running:
                server.terminate()
            try:
                _, stderr = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                _, stderr = server.communicate(timeout=3)
                cleanup_errors.append("Xvfb required forced kill")
            if raw is not None:
                raw["xvfb_running_before_stop"] = running
                raw["xvfb_returncode_after_stop"] = server.returncode
                raw["xvfb_stderr"] = stderr
                raw["cleanup_errors"] = cleanup_errors

    if raw is None:
        raise RuntimeError("candidate produced no raw record")
    (out / "raw.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({"candidate_exit": 0, "cycles": len(result["cycles"]),
                      "client_counter": result["app_counter_final"],
                      "source_sha256": result["source_sha256"]}, sort_keys=True))
