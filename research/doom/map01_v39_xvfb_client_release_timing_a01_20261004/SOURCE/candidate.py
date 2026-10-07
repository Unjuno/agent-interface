#!/usr/bin/env python3
"""Measure Xvfb client event receipt relative to direct and owner XTEST calls."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import select
import subprocess
import sys
import threading
import time
from pathlib import Path
from importlib.metadata import version


def load_owner(path: Path):
    import types
    module = types.ModuleType("executor_v3")
    module.Cancelled = type("Cancelled", (Exception,), {})
    module.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = module
    spec = importlib.util.spec_from_file_location("frozen_input_owner_v10", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen input owner")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded.InputOwner


class Lease:
    def __init__(self, focus: int):
        self.expected_focus = focus
        self.intent_token = "xvfb-event-timing-a01"
        self.deadline = time.perf_counter_ns() + 30_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("finite Xvfb construction lease expired")


class EventReceiver:
    def __init__(self, conn, window_id: int, keycode: int):
        self.conn, self.window_id, self.keycode = conn, window_id, keycode
        self.rows: list[dict] = []
        self.condition = threading.Condition()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name="x-event-receiver")

    def start(self):
        self.thread.start()

    def _run(self):
        from Xlib import X
        while not self.stop.is_set():
            if not self.conn.pending_events():
                ready, _, _ = select.select([self.conn.fileno()], [], [], 0.05)
                if not ready:
                    continue
            event = self.conn.next_event()
            if event.type not in (X.KeyPress, X.KeyRelease):
                continue
            window = getattr(event, "window", None)
            window_id = window.id if hasattr(window, "id") else window
            if event.detail != self.keycode:
                continue
            row = {
                "type": int(event.type),
                "keycode": int(event.detail),
                "window_id": int(window_id),
                "server_time_ms": int(event.time),
                "send_event": bool(getattr(event, "send_event", False)),
                "received_ns": time.perf_counter_ns(),
            }
            with self.condition:
                self.rows.append(row)
                self.condition.notify_all()

    def wait(self, event_type: int, ordinal: int, timeout_s: float = 2.0):
        deadline = time.monotonic() + timeout_s
        with self.condition:
            while True:
                matching = [row for row in self.rows if row["type"] == event_type]
                if len(matching) >= ordinal:
                    return matching[ordinal - 1]
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"event type {event_type} #{ordinal} not received")
                self.condition.wait(remaining)

    def close(self):
        self.stop.set()
        self.thread.join(timeout=2)
        return not self.thread.is_alive()


def key_down(bitmap, code):
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=30)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    from Xlib import X, XK, display
    from Xlib.ext import xtest

    raw = {
        "schema": "map01-v39-xvfb-client-release-timing-a01-v1",
        "status": "RUNNING",
        "started_ns": time.perf_counter_ns(),
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "cycles_requested": args.cycles,
        "environment": {
            "python": sys.version,
            "python_xlib": version("python-xlib"),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "display": ":117",
        },
        "trials": [],
    }
    xvfb = None
    observer = sender = window = owner = receiver = None
    try:
        if args.cycles != 30:
            raise ValueError("frozen cycle count must be exactly 30")
        env = dict(os.environ, DISPLAY=":117")
        xvfb = subprocess.Popen(
            ["Xvfb", ":117", "-screen", "0", "640x480x24", "-nolisten", "tcp", "-ac"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 3
        while True:
            if xvfb.poll() is not None:
                raise RuntimeError(f"Xvfb exited during startup: {xvfb.returncode}")
            try:
                observer = display.Display(":117")
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Xvfb display startup timed out")
                time.sleep(0.02)
        sender = display.Display(":117")
        screen = observer.screen()
        window = screen.root.create_window(
            0, 0, 200, 100, 0, X.CopyFromParent, X.InputOutput,
            X.CopyFromParent, background_pixel=0,
            event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        observer.sync()
        keycode = observer.keysym_to_keycode(XK.string_to_keysym("a"))
        if not keycode:
            raise RuntimeError("Xvfb keymap has no keycode for 'a'")
        receiver = EventReceiver(observer, window.id, keycode)
        receiver.start()
        Owner = load_owner(args.source)
        owner = Owner(":117")
        lease = Lease(window.id)
        raw["xvfb_pid"] = xvfb.pid
        raw["target_window_id"] = window.id
        raw["keycode"] = keycode
        raw["owner_id"] = owner.owner_id

        for cycle in range(args.cycles):
            for route in ("direct_xtest", "input_owner_v10"):
                before = len(receiver.rows)
                press_before = sum(row["type"] == X.KeyPress for row in receiver.rows)
                release_before = sum(row["type"] == X.KeyRelease for row in receiver.rows)
                bitmap_before = sender.query_keymap()
                if key_down(bitmap_before, keycode):
                    raise RuntimeError("key was already down before trial")
                press_start = time.perf_counter_ns()
                if route == "direct_xtest":
                    xtest.fake_input(sender, X.KeyPress, keycode)
                    sender.sync()
                    press_ack = time.perf_counter_ns()
                    press_return = press_ack
                else:
                    admission = owner.call("down", lease, "a")
                    press_ack = int(admission["input_ack_ns"])
                    press_return = time.perf_counter_ns()
                press_event = receiver.wait(X.KeyPress, press_before + 1)
                down_after_press = key_down(sender.query_keymap(), keycode)

                release_start = time.perf_counter_ns()
                if route == "direct_xtest":
                    xtest.fake_input(sender, X.KeyRelease, keycode)
                    sender.sync()
                    release_return = time.perf_counter_ns()
                else:
                    owner.call("up", lease, "a")
                    release_return = time.perf_counter_ns()
                release_event = receiver.wait(X.KeyRelease, release_before + 1)
                down_after_release = key_down(sender.query_keymap(), keycode)
                if len(receiver.rows) != before + 2:
                    raise RuntimeError("unexpected event count within one trial")
                raw["trials"].append({
                    "cycle": cycle,
                    "route": route,
                    "press_start_ns": press_start,
                    "press_ack_ns": press_ack,
                    "press_return_ns": press_return,
                    "release_start_ns": release_start,
                    "release_return_ns": release_return,
                    "press_event": press_event,
                    "release_event": release_event,
                    "key_down_before": False,
                    "key_down_after_press": down_after_press,
                    "key_down_after_release": down_after_release,
                    "press_receive_minus_ack_ns": press_event["received_ns"] - press_ack,
                    "release_receive_minus_return_ns": release_event["received_ns"] - release_return,
                    "server_event_delta_ms": (release_event["server_time_ms"] - press_event["server_time_ms"]) & 0xFFFFFFFF,
                })
        owner.close()
        owner_records = list(owner.records)
        raw["owner_close"] = owner_records[-1] if owner_records else None
        raw["owner_records"] = owner_records
        raw["owner_closed"] = owner.closed
        owner = None
        if receiver is not None:
            raw["receiver_stopped"] = receiver.close()
            receiver = None
        if window is not None:
            window.destroy()
            observer.sync()
        sender.close(); sender = None
        observer.close(); observer = None
        xvfb.terminate()
        stdout, stderr = xvfb.communicate(timeout=5)
        raw["xvfb_exit"] = xvfb.returncode
        raw["xvfb_stdout"] = stdout.decode("utf-8", "replace")
        raw["xvfb_stderr"] = stderr.decode("utf-8", "replace")
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["status"] = "CANDIDATE_ERROR"
        raw["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        raw["finished_ns"] = time.perf_counter_ns()
        if receiver is not None:
            raw["receiver_stopped"] = receiver.close()
        if owner is not None:
            try:
                owner.close()
                raw["owner_cleanup_error"] = None
                raw["owner_records"] = owner.records
            except BaseException as exc:
                raw["owner_cleanup_error"] = {"type": type(exc).__name__, "message": str(exc)}
        for conn in (sender, observer):
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
        if xvfb is not None and xvfb.poll() is None:
            xvfb.terminate()
            try:
                stdout, stderr = xvfb.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                stdout, stderr = xvfb.communicate()
            raw["xvfb_exit"] = xvfb.returncode
            raw["xvfb_stdout"] = stdout.decode("utf-8", "replace")
            raw["xvfb_stderr"] = stderr.decode("utf-8", "replace")
        (args.out / "raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(raw["status"])
    if raw["status"] != "CANDIDATE_COMPLETE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
