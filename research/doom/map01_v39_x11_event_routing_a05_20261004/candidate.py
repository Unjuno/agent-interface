"""One-shot corrected Python-Xlib target-window routing check for A05."""
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
    spec = importlib.util.spec_from_file_location("a03_input_owner_v10", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen InputOwner v10")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.InputOwner


class EventSink:
    def __init__(self, connection, window_id: int, keycode: int):
        self.connection = connection
        self.window_id = window_id
        self.keycode = keycode
        self.counter = 0

    def collect(self, duration: float = 0.25) -> list[dict]:
        from Xlib import X
        deadline = time.monotonic() + duration
        events = []
        while time.monotonic() < deadline:
            if self.connection.pending_events():
                event = self.connection.next_event()
            else:
                remaining = deadline - time.monotonic()
                ready, _, _ = select.select([self.connection.fileno()], [], [], remaining)
                if not ready:
                    break
                event = self.connection.next_event()
            if event.type not in (X.KeyPress, X.KeyRelease):
                continue
            event_window = getattr(event, "window", None)
            event_window_id = event_window.id if hasattr(event_window, "id") else event_window
            target = event_window_id == self.window_id and event.detail == self.keycode
            row = {
                "event_type": event.type,
                "keycode": event.detail,
                "window_id": event_window_id,
                "server_time_ms": event.time,
                "send_event": bool(getattr(event, "send_event", False)),
                "received_ns": time.perf_counter_ns(),
                "target_match": target,
            }
            events.append(row)
            if target and event.type == X.KeyPress:
                self.counter += 1
        return events


def sample(observer, keycode: int, stage: str) -> dict:
    started = time.perf_counter_ns()
    values = observer.query_keymap()
    finished = time.perf_counter_ns()
    bitmap = bytes(values)
    return {
        "stage": stage,
        "sample_started_ns": started,
        "sample_finished_ns": finished,
        "bitmap_length": len(bitmap),
        "bitmap_hex": bitmap.hex(),
        "keycode": keycode,
        "key_down": bool(bitmap[keycode // 8] & (1 << (keycode % 8))),
        "source": "independent Xlib Display.query_keymap",
        "physical_key_up_claimed": False,
    }


def run(out: Path) -> dict:
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=False)
    from Xlib import X, XK, display
    from Xlib.ext import xtest

    raw = {
        "schema": "v39-x11-event-routing-a05-v1",
        "allocation_id": "MAP01-V39-X11-EVENT-ROUTING-A05-20261004-01",
        "candidate_invocations": 1,
        "candidate_complete": False,
        "failure": None,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "routes": {},
        "owner_records": [],
        "xvfb_running_before_stop": None,
        "xvfb_returncode_after_stop": None,
        "xvfb_stderr": None,
        "cleanup_errors": [],
    }
    observer = app_display = owner = server = None
    try:
        with tempfile.TemporaryDirectory(prefix="v39-x11-routing-a05-") as temporary:
            auth = Path(temporary) / "empty.Xauthority"
            auth.write_bytes(b"")
            env = dict(os.environ, XAUTHORITY=str(auth))
            server = subprocess.Popen(
                ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
                 "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env=env)
            ready, _, _ = select.select([server.stdout], [], [], 5)
            if not ready:
                raise TimeoutError("private Xvfb startup timeout")
            number = server.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("Xvfb displayfd malformed")
            display_name = ":" + number
            observer = display.Display(display_name)
            app_display = display.Display(display_name)
            screen = app_display.screen()
            window = screen.root.create_window(
                20, 20, 320, 120, 0, screen.root_depth, X.InputOutput,
                X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
            window.map()
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            app_display.sync()
            observer.sync()
            focus = observer.get_input_focus().focus
            focus_id = focus.id if hasattr(focus, "id") else focus
            keycode = observer.keysym_to_keycode(XK.string_to_keysym("w"))
            if focus_id != window.id or type(keycode) is not int or keycode <= 0:
                raise RuntimeError("focused sink or W keycode setup invalid")
            sink = EventSink(app_display, window.id, keycode)
            raw.update({"display_number": int(number), "window_id": window.id,
                        "keycode": keycode, "focus_id": focus_id})
            sink.collect(0.05)

            direct_id = uuid.uuid4().hex
            direct = {"occurrence_id": direct_id, "method": "direct XTEST control",
                      "counter_before": sink.counter}
            raw["routes"]["direct_xtest"] = direct
            direct["pre_down"] = sample(observer, keycode, "pre_down")
            direct["down_started_ns"] = time.perf_counter_ns()
            xtest.fake_input(observer, X.KeyPress, keycode)
            observer.sync()
            direct["down_returned_ns"] = time.perf_counter_ns()
            direct["post_down"] = sample(observer, keycode, "post_down")
            direct["client_events_after_down"] = sink.collect()
            direct["counter_after_down"] = sink.counter
            direct["up_started_ns"] = time.perf_counter_ns()
            xtest.fake_input(observer, X.KeyRelease, keycode)
            observer.sync()
            direct["up_returned_ns"] = time.perf_counter_ns()
            direct["client_events_after_up"] = sink.collect()
            direct["post_up"] = sample(observer, keycode, "post_up")
            direct["counter_after_up"] = sink.counter
            owner = load_owner()(display_name)
            owner_id = owner.owner_id
            owner_route_id = uuid.uuid4().hex
            lease = Lease(window.id, "a05:" + owner_route_id)
            owned = {"occurrence_id": owner_route_id, "intent_token": lease.intent_token,
                     "method": "InputOwner v10", "owner_id": owner_id,
                     "counter_before": sink.counter}
            raw["routes"]["input_owner_v10"] = owned
            owned["pre_down"] = sample(observer, keycode, "pre_down")
            owned["down_started_ns"] = time.perf_counter_ns()
            owned["admission"] = owner.call("down", lease, "w")
            owned["down_returned_ns"] = time.perf_counter_ns()
            owned["owner_after_down"] = owner.call("input_state")
            owned["post_down"] = sample(observer, keycode, "post_down")
            owned["client_events_after_down"] = sink.collect()
            owned["counter_after_down"] = sink.counter
            owned["up_started_ns"] = time.perf_counter_ns()
            owned["up_result"] = owner.call("up", lease, "w")
            owned["up_returned_ns"] = time.perf_counter_ns()
            owned["release_result"] = owner.call("release", lease)
            owned["release_returned_ns"] = time.perf_counter_ns()
            owned["client_events_after_up"] = sink.collect()
            owned["post_up"] = sample(observer, keycode, "post_up")
            owned["owner_after_up"] = owner.call("input_state")
            owned["counter_after_up"] = sink.counter
            owner.close()
            raw["owner_records"] = list(owner.records)
            owner = None
            raw["app_counter_final"] = sink.counter
            raw["candidate_complete"] = True
            raw["scope"] = "focused minimal Xlib client event routing control only"
    except BaseException as exc:
        raw["failure"] = repr(exc)
    finally:
        cleanup_errors = []
        if owner is not None:
            try:
                owner.close()
                raw["owner_records"] = list(owner.records)
            except BaseException as exc:
                cleanup_errors.append("owner_close: " + repr(exc))
        for name, connection in (("app", app_display), ("observer", observer)):
            if connection is not None:
                try:
                    connection.close()
                except BaseException as exc:
                    cleanup_errors.append(name + "_close: " + repr(exc))
        if server is not None:
            running = server.poll() is None
            if running:
                server.terminate()
            try:
                _, stderr = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                _, stderr = server.communicate(timeout=3)
                cleanup_errors.append("Xvfb required forced kill")
            raw["xvfb_running_before_stop"] = running
            raw["xvfb_returncode_after_stop"] = server.returncode
            raw["xvfb_stderr"] = stderr
        raw["cleanup_errors"] = cleanup_errors
        (out / "raw.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({"candidate_exit": 0 if result["candidate_complete"] else 1,
                      "failure": result["failure"],
                      "route_count": len(result["routes"])}, sort_keys=True))
    raise SystemExit(0 if result["candidate_complete"] else 1)
