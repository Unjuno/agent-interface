"""One-shot Xvfb test of current V39 per-key release-batch telemetry."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
import types

HERE = Path(__file__).resolve().parent
SOURCE = HERE
BATCHES = [[("a", True), ("a", False)],
           [("a", True), ("a", False)],
           [("a", True), ("space", True), ("space", False), ("a", False)]]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shim_imports():
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor
    release_v1 = types.ModuleType("doom_typed_release_backend_v1")
    release_v1.Backend = object
    release_v1.suite = object()
    sys.modules["doom_typed_release_backend_v1"] = release_v1
    coast = types.ModuleType("doom_typed_coast_backend_v1")
    coast.Backend = object
    coast.suite = object()
    sys.modules["doom_typed_coast_backend_v1"] = coast
    owner_v11 = types.ModuleType("input_owner_v11")
    owner_v11.InputOwner = object
    sys.modules["input_owner_v11"] = owner_v11
    parent = types.ModuleType("doom_typed_release_backend_v2")

    class EmptyOwner:
        def close(self):
            return None

    class Parent:
        def __init__(self, session, out, emit, signal_readers):
            self.session, self.out, self.emit = session, out, emit
            self.signal_readers = signal_readers
            self.owner = EmptyOwner()
            self.held = set()
            self.lease = None
            self._input_event_context = None

        def execute(self, step, cancel, identifier, index):
            if self._input_event_context is not None:
                raise RuntimeError("nested fixture execution")
            self._input_event_context = (identifier, index)
            try:
                for key, down in step["actions"]:
                    if cancel.is_set():
                        raise RuntimeError("cancelled before fixture edge")
                    self.raw(key, down)
            finally:
                self._input_event_context = None
            return "fixture_program_complete"

    parent.Backend = Parent
    parent.suite = object()
    sys.modules["doom_typed_release_backend_v2"] = parent


class Lease:
    def __init__(self, focus, surface, geometry, active_window_atom):
        self.deadline = time.perf_counter_ns() + 30_000_000_000
        self.expected_focus = focus
        self.expected_surface = surface
        self.expected_geometry = geometry
        self.expected_surface = surface
        self.active_window_atom = active_window_atom
        self.surface_observation = {"window": surface, "geometry": geometry,
                                    "title": "A06 synthetic X client", "visible": True}
        self.expected_visual_context = {"window": surface, "title": "A06 synthetic X client"}
        self.intent_token = "v39-perkey-xvfb-a06"
        self.cancel = threading.Event()
        self.focus_invalid = False
        self._interruption = None

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("lease cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired")

    def interruption_snapshot(self):
        return self._interruption

    def record_interruption(self, row):
        self._interruption = row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":128")
    args = parser.parse_args()
    out = args.out
    if out.exists():
        raise SystemExit("output exists; refusing to overwrite first outcome")
    out.mkdir(parents=True)
    raw = {"schema": "map01-v39-xvfb-per-key-release-raw-a06-v1",
           "status": "STOP", "actions": [], "client_events": [],
           "post_batch_keymaps": [], "keymap_queries": [], "ignored_events": [],
           "emitted_rows": [], "errors": [], "cleanup": {},
           "scope": "V39 release-batch backend and owner on isolated Xvfb; no game/model/physical input"}
    queries = []
    rows = []
    batches = []
    raw["keymap_queries"] = queries
    raw["emitted_rows"] = rows
    raw["batches"] = batches
    xvfb = observer = backend = None
    owner = None
    original_query_keymap = None
    try:
        freeze = json.loads((HERE.parent / "FREEZE.json").read_text())
        for name, digest in freeze["source_sha256"].items():
            path = SOURCE / name
            if sha(path) != digest:
                raise ValueError("frozen source SHA mismatch: " + name)
        from Xlib import X, Xatom, XK, display

        original_query_keymap = display.Display.query_keymap
        observer_id = [None]
        queries.clear()

        def traced_query_keymap(connection):
            started = time.perf_counter_ns()
            bitmap = original_query_keymap(connection)
            queries.append({"display_object_id": id(connection),
                            "role": "observer" if id(connection) == observer_id[0] else "owner_or_other",
                            "started_ns": started,
                            "returned_ns": time.perf_counter_ns()})
            return bitmap

        display.Display.query_keymap = traced_query_keymap
        xvfb = subprocess.Popen(
            ["Xvfb", args.display, "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-noreset", "-ac"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)
        raw["xvfb_pid"] = xvfb.pid
        deadline = time.monotonic() + 5
        last_error = None
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited: " + xvfb.stderr.read().decode("utf-8", "replace"))
            try:
                observer = display.Display(args.display)
                break
            except Exception as error:
                last_error = repr(error)
                time.sleep(.05)
        if observer is None:
            raise TimeoutError("Xvfb connection failed: " + str(last_error))
        observer_id[0] = id(observer)
        window = observer.screen().root.create_window(
            20, 20, 320, 200, 0, observer.screen().root_depth,
            X.InputOutput, X.CopyFromParent,
            event_mask=X.KeyPressMask | X.KeyReleaseMask)
        window.map()
        active_atom = observer.intern_atom("_NET_ACTIVE_WINDOW")
        utf8_atom = observer.intern_atom("UTF8_STRING")
        title_atom = observer.intern_atom("_NET_WM_NAME")
        window.change_property(title_atom, utf8_atom, 8, b"A06 synthetic X client")
        observer.screen().root.change_property(active_atom, Xatom.WINDOW, 32, [window.id])
        observer.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        observer.sync()
        for _ in range(100):
            focus = observer.get_input_focus().focus
            if getattr(focus, "id", focus) == window.id:
                break
            time.sleep(.01)
        else:
            raise RuntimeError("focused Xvfb client setup failed")
        while observer.pending_events():
            observer.next_event()
        keycodes = {key: int(observer.keysym_to_keycode(XK.string_to_keysym(key)))
                    for key in ("a", "space")}
        if not all(keycodes.values()):
            raise RuntimeError("required keys have no X keycode")
        raw.update({"client_window": int(window.id), "keycodes": keycodes,
                    "display": args.display})

        shim_imports()
        from doom_owner_thread_release_batch_backend_v1 import Backend

        class Session:
            name = args.display

        backend = Backend(Session(), out, rows.append, {})
        owner = backend.owner
        lease = Lease(int(window.id), int(window.id), [20, 20, 320, 200], int(active_atom))
        backend.lease = lease
        started = time.perf_counter_ns()
        expected_events = []
        batches.clear()
        batch_index = 0
        for cycle in range(10):
            for batch in BATCHES:
                batch_started = time.perf_counter_ns()
                backend.execute({"actions": batch}, lease.cancel,
                                "v39-perkey-xvfb-a06", batch_index)
                batch_ended = time.perf_counter_ns()
                batch_row = {"cycle": cycle, "batch": batch_index,
                             "actions": [{"key": key, "down": down}
                                         for key, down in batch],
                             "started_ns": batch_started,
                             "ended_ns": batch_ended}
                batches.append(batch_row)
                for edge, (key, down) in enumerate(batch):
                    expected_type = X.KeyPress if down else X.KeyRelease
                    event_deadline = time.monotonic() + 1.0
                    while True:
                        if observer.pending_events():
                            event = observer.next_event()
                        else:
                            remaining = event_deadline - time.monotonic()
                            ready, _, _ = select.select(
                                [observer.fileno()], [], [], max(0, remaining))
                            if not ready:
                                raise TimeoutError(f"client edge timeout cycle={cycle} batch={batch_index} edge={edge}")
                            event = observer.next_event()
                        event_type = int(event.type)
                        if event_type in (X.KeyPress, X.KeyRelease):
                            break
                        raw["ignored_events"].append({
                            "cycle": cycle, "batch": batch_index,
                            "edge_waiting_for": edge, "event_type": event_type,
                            "event_class": type(event).__name__,
                            "observed_ns": time.perf_counter_ns()})
                    expected = {"cycle": cycle, "batch": batch_index,
                                "edge": edge, "key": key, "down": down,
                                "event_type": int(expected_type),
                                "keycode": keycodes[key], "window": int(window.id)}
                    actual = {"event_type": int(event.type),
                              "event_name": "KeyPress" if event.type == X.KeyPress else
                                            "KeyRelease" if event.type == X.KeyRelease else
                                            f"type-{event.type}",
                              "keycode": int(event.detail),
                              "window": int(event.window.id),
                              "server_time_ms": int(event.time),
                              "dispatch_ns": time.perf_counter_ns()}
                    if (actual["event_type"] != expected_type or
                            actual["keycode"] != keycodes[key] or
                            actual["window"] != window.id):
                        raise ValueError("X client event mismatch: " + json.dumps({"expected": expected, "actual": actual}))
                    expected_events.append(expected)
                    raw["client_events"].append({**expected, **actual})
                bitmap = observer.query_keymap()
                states = {key: bool(bitmap[keycodes[key] // 8] & (1 << (keycodes[key] % 8)))
                          for key in keycodes}
                raw["post_batch_keymaps"].append({
                    "cycle": cycle, "batch": batch_index,
                    "sampled_ns": time.perf_counter_ns(), "states": states,
                    "empty_after_batch": not any(states.values())})
                batch_index += 1
        ended = time.perf_counter_ns()
        backend_rows = list(rows)
        transition_inner = getattr(owner, "_inner", None)
        inner = getattr(transition_inner, "_inner", None)
        if inner is None:
            raise RuntimeError("owner wrapper chain changed")
        owner.close()
        raw["emitted_rows"] = backend_rows
        raw["execute_started_ns"] = started
        raw["execute_ended_ns"] = ended
        raw["client_event_count"] = len(expected_events)
        raw["backend_row_counts"] = {
            name: sum(row.get("event") == name for row in backend_rows)
            for name in ("input_admission", "input_release_transition")}
        raw["owner_keyup_records"] = [row for row in inner.records
                                       if row.get("event") == "owner_explicit_keyup"]
        raw["owner_close_records"] = [row for row in inner.records
                                      if row.get("event") == "owner_release"]
        raw["cleanup_events"] = [row for row in raw["owner_close_records"]]
        raw["cleanup"].update({"owner_closed": inner.closed,
                               "owner_stopped": inner.stopped.is_set(),
                               "owner_thread_alive": inner.thread.is_alive(),
                               "owner_keycodes_after_close":
                                   raw["owner_close_records"][-1].get("keys_down")
                                   if raw["owner_close_records"] else None})
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as error:
        raw["errors"].append(f"{type(error).__name__}: {error}")
        raw["status"] = "CANDIDATE_ERROR"
    finally:
        raw["emitted_rows"] = rows
        raw["batches"] = batches
        raw["keymap_queries"] = queries
        if owner is not None:
            try:
                transition_inner = getattr(owner, "_inner", None)
                inner = getattr(transition_inner, "_inner", None)
                if inner is not None and not inner.closed:
                    owner.close()
                if inner is not None:
                    raw["cleanup"].update({"owner_closed": inner.closed,
                                           "owner_stopped": inner.stopped.is_set(),
                                           "owner_thread_alive": inner.thread.is_alive()})
                    raw["owner_keyup_records"] = [row for row in inner.records
                        if row.get("event") == "owner_explicit_keyup"]
                    raw["owner_close_records"] = [row for row in inner.records
                        if row.get("event") == "owner_release"]
                    if raw["owner_close_records"]:
                        raw["cleanup"]["owner_keycodes_after_close"] = (
                            raw["owner_close_records"][-1].get("keys_down"))
                    raw["cleanup_events"] = [row for row in raw["owner_close_records"]]
            except BaseException as error:
                raw["cleanup"]["owner_close_error"] = f"{type(error).__name__}: {error}"
        if observer is not None:
            try:
                observer.close()
            except BaseException as error:
                raw["cleanup"]["observer_close_error"] = f"{type(error).__name__}: {error}"
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as error:
                raw["cleanup"]["xvfb_terminate_error"] = f"{type(error).__name__}: {error}"
                try:
                    xvfb.kill()
                    xvfb.wait(timeout=5)
                except BaseException as kill_error:
                    raw["cleanup"]["xvfb_kill_error"] = f"{type(kill_error).__name__}: {kill_error}"
        if original_query_keymap is not None:
            try:
                from Xlib import display
                display.Display.query_keymap = original_query_keymap
            except BaseException:
                pass
        (out / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": raw["status"], "errors": raw["errors"],
                      "client_event_count": raw.get("client_event_count"),
                      "backend_row_counts": raw.get("backend_row_counts")}))


if __name__ == "__main__":
    main()
