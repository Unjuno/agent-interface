#!/usr/bin/env python3
"""One-shot fake-X composition probe of current V39/V15 explicit key release."""
from __future__ import annotations

import json
import pathlib
import sys
import threading
import time
import types

ROOT = pathlib.Path("/src")
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]

X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                          ButtonRelease=5, MotionNotify=6, Button1Mask=256,
                          AnyPropertyType=0, IsViewable=2)
active_display = None
drop_key_release = False


class Focus:
    id = 41


class Pointer:
    mask = 0
    root_x = 10
    root_y = 10


class Root:
    def query_pointer(self):
        return Pointer()


class Screen:
    root = Root()


class FakeDisplay:
    def __init__(self, _name):
        global active_display
        active_display = self
        self.down = set()
        self.closed = False

    def get_input_focus(self):
        return types.SimpleNamespace(focus=Focus())

    def keysym_to_keycode(self, _sym):
        return 38

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return Screen()

    def sync(self):
        pass

    def close(self):
        self.closed = True


def fake_input(display, event, code, **_kwargs):
    global drop_key_release
    if event == X.KeyPress:
        display.down.add(code)
    elif event == X.KeyRelease:
        if drop_key_release:
            drop_key_release = False
        else:
            display.down.discard(code)


def install_xlib():
    xlib = types.ModuleType("Xlib")
    xlib.X = X
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda _key: 1)
    xlib.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                      BadDrawable=type("BadDrawable", (Exception,), {}))
    display = types.ModuleType("Xlib.display")
    display.Display = FakeDisplay
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.display, xlib.ext = display, ext
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                        "Xlib.XK": types.ModuleType("Xlib.XK"),
                        "Xlib.error": types.ModuleType("Xlib.error"),
                        "Xlib.display": display, "Xlib.ext": ext,
                        "Xlib.ext.xtest": xtest})


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()
        self.intent_token = "v15-loss-probe"
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        pass

    def interruption_snapshot(self):
        return None

    def record_interruption(self, _row):
        pass


class DummyOwner:
    def __init__(self, _display_name=None):
        pass

    def close(self):
        pass


class ControllerBackend:
    """Test-only action-loop double; production execute/raw methods remain loaded."""
    def __init__(self, session, _out, emit, _signal_readers):
        self.owner = DummyOwner()
        self.lease = Lease()
        self.held = set()
        self.emit = emit
        self.session = session
        self._input_event_context = None

    def execute(self, step, _cancel, _identifier, _index):
        for key, down in step["actions"]:
            self.raw(key, down)
        return {"executed": len(step["actions"])}

    def release_all(self):
        return self.owner.call("release", self.lease)


class Session:
    name = "FAKE"


def install_production_backend_imports():
    # Isolate the real V2/V15 selected backend from ViZDoom/session setup. The
    # base backend supplies only the action loop above; all selected release
    # composition methods and V4→V3→V12 owner code are imported from source.
    base = types.ModuleType("doom_typed_release_backend_v1")
    base.Backend = ControllerBackend
    base.suite = object()
    sys.modules["doom_typed_release_backend_v1"] = base
    v11 = types.ModuleType("input_owner_v11")
    v11.InputOwner = DummyOwner
    sys.modules["input_owner_v11"] = v11


def run_case(drop):
    global drop_key_release
    drop_key_release = drop
    from doom_owner_thread_release_batch_backend_v1 import Backend

    emitted = []
    backend = Backend(Session(), None, emitted.append, {})
    try:
        result = backend.execute({"actions": [("F8", True), ("F8", False)]},
                                 None, "lost-up-case" if drop else "normal-case", 0)
        server_down = sorted(active_display.down)
        release_rows = [r for r in emitted if r.get("event") == "input_release_transition"]
        batch = release_rows[0] if len(release_rows) == 1 else None
        close_error = None
        try:
            backend.owner.close()
        except Exception as exc:  # first terminal result is raw evidence
            close_error = f"{type(exc).__name__}: {exc}"
        owner_records = list(backend.owner.records)
        terminal_rows = [r for r in owner_records if r.get("event") == "owner_release"]
        resource_observation = {}
        for rel in ("/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/memory.max",
                    "/sys/fs/cgroup/memory.swap.max", "/sys/fs/cgroup/cgroup.controllers"):
            path = pathlib.Path(rel)
            try:
                resource_observation[rel] = path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                resource_observation[rel] = f"unavailable:{type(exc).__name__}"
        return {
            "injected_keyrelease_loss": drop,
            "backend_result": result,
            "events": emitted,
            "server_keycodes_down_after_batch": server_down,
            "release_row": batch,
            "terminal_close_error": close_error,
            "terminal_owner_release_rows": terminal_rows,
            "terminal_cleanup_recovered": not active_display.down,
            "container_resource_observation": resource_observation,
        }
    finally:
        try:
            backend.owner.close()
        except Exception:
            pass


def main():
    install_xlib()
    install_production_backend_imports()
    # Import the selected backend here, after test-only controller dependencies
    # are pinned; actual V15/V4/V3/V12 implementation files are unmodified.
    results = [run_case(False), run_case(True)]
    out = pathlib.Path("/out/candidate.json")
    out.write_text(json.dumps({"schema": "v39-v15-keyup-loss-a03-raw-v1",
                               "source_base": "018934cdf45fcabffcc4efe25b5c7b3d59bd459f",
                               "claims": {"real_x11": False, "gui": False,
                                          "doom": False, "model": False,
                                          "physical_keyboard": False,
                                          "application_effect": False},
                               "cases": results}, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"raw": str(out), "cases": len(results),
                      "loss_server_down": results[1]["server_keycodes_down_after_batch"]}))


if __name__ == "__main__":
    main()
