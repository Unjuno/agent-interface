"""One-shot inert trace through main's V15 release backend and V4/V3/V12 owner."""
from __future__ import annotations
import json
import sys
import threading
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]
OUT = Path(__file__).resolve().parent

class Recorder:
    def __init__(self):
        self.events = []
        self.lock = threading.Lock()
    def add(self, name, *, at_ns=None, **fields):
        with self.lock:
            self.events.append({"event": name, "time_ns": at_ns or time.perf_counter_ns(), **fields})

recorder = Recorder()

class FakeRoot:
    id = 1
    def query_pointer(self):
        recorder.add("query_pointer")
        return types.SimpleNamespace(mask=0, root_x=0, root_y=0, child=None)
    def get_geometry(self):
        return types.SimpleNamespace(width=1024, height=768)

class FakeDisplay:
    def __init__(self, name):
        self.name = name
        self.root = FakeRoot()
        self.keys = set()
        recorder.add("display_open", display=name)
    def screen(self):
        return types.SimpleNamespace(root=self.root)
    def get_input_focus(self):
        recorder.add("get_input_focus")
        return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
    def keysym_to_keycode(self, sym):
        return {"a": 38, "space": 65}.get(sym, 0)
    def sync(self):
        recorder.add("display_sync")
    def query_keymap(self):
        recorder.add("query_keymap", keys=sorted(self.keys))
        bitmap = bytearray(32)
        for code in self.keys:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)
    def close(self):
        recorder.add("display_close")

X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4, ButtonRelease=5,
                          Button1Mask=256, AnyPropertyType=0, IsViewable=2)
XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
display = types.SimpleNamespace(Display=FakeDisplay)
error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                              BadDrawable=type("BadDrawable", (Exception,), {}))
xtest = types.SimpleNamespace(fake_input=lambda d, event_type, detail: _fake_input(d, event_type, detail))
def _fake_input(d, event_type, detail):
    name = "key_down" if event_type == X.KeyPress else "key_up" if event_type == X.KeyRelease else "button"
    if event_type == X.KeyPress:
        d.keys.add(detail)
    elif event_type == X.KeyRelease:
        d.keys.discard(detail)
    recorder.add(name, keycode=detail, display_event_type=event_type)

xlib = types.ModuleType("Xlib")
xlib.X, xlib.XK, xlib.display, xlib.error = X, XK, display, error
xext = types.ModuleType("Xlib.ext")
xext.xtest = xtest
sys.modules.update({"Xlib": xlib, "Xlib.ext": xext})

# V3's default owner is intentionally never constructed: V4 passes the exact V12 class.
owner_v10 = types.ModuleType("input_owner_v10")
owner_v10.InputOwner = type("UnusedV10", (), {})
sys.modules["input_owner_v10"] = owner_v10

# The inherited typed backend only supplies the already-frozen step-to-raw-key loop.
base_module = types.ModuleType("doom_typed_release_backend_v2")
class DummyOwner:
    def close(self):
        recorder.add("inherited_empty_owner_close")
class FakeTypedBackendBase:
    def __init__(self, session, out, emit, signal_readers):
        self.owner = DummyOwner()
        self.held = set()
        self.emit = emit
        self._input_event_context = None
        self.lease = types.SimpleNamespace(
            intent_token="probe-lease", deadline=time.perf_counter_ns() + 60_000_000_000,
            expected_focus=42, expected_surface=None, expected_geometry=None,
            focus_invalid=False, cancel=threading.Event(), check=lambda: None)
    def execute(self, step, cancel, identifier, index):
        self._input_event_context = (identifier, index)
        try:
            for key in step["keys"]:
                self.raw(key, True)
            for key in step["keys"]:
                self.raw(key, False)
        finally:
            self._input_event_context = None
    def release_all(self):
        return self.owner.call("release", self.lease)
base_module.Backend = FakeTypedBackendBase
base_module.suite = object()
sys.modules["doom_typed_release_backend_v2"] = base_module

from doom_owner_thread_release_batch_backend_v1 import Backend

session = types.SimpleNamespace(name="fake-display-v39-closure")
rows = []
backend = Backend(session, None, rows.append, {})
owner = backend.owner
original_call = owner.call
def traced_call(operation, lease=None, key=None):
    if operation == "input_state":
        recorder.add("input_state_call_begin")
        result = original_call(operation, lease, key)
        recorder.add("input_state_sample_start", at_ns=result["sample_started_ns"])
        recorder.add("input_state_sample_finish", at_ns=result["sample_finished_ns"])
        recorder.add("input_state_call_return")
        return result
    return original_call(operation, lease, key)
owner.call = traced_call
backend.execute({"keys": ["a", "space"]}, None, "two-key-probe", 7)
release_rows = [row for row in rows if row.get("event") == "input_release_transition"]
# Stop the real production owner thread. Its cleanup keymap query occurs after the batch sample.
owner.close()
events = sorted(recorder.events, key=lambda event: event["time_ns"])
result = {
    "schema": "v39-selected-release-closure-trace-v1",
    "source_commit": "69dd261430cb1ed875f5a76411c4a2a54777c114",
    "scenario": "two distinct keys through production release-batch backend and V4/V3/V12 owner adapters with inert Xlib display and scripted typed-backend base",
    "events": events,
    "release_rows": release_rows,
    "physical_input": False,
    "live_game": False,
    "gui": False,
    "model_calls": 0,
}
(OUT / "TRACE.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"events": events, "release_rows": release_rows}, indent=2, sort_keys=True))
