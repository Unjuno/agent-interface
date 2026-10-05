"""One-shot fake-Xlib probe of V39 batch cleanup and incremental custody."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]
HERE = Path(__file__).resolve().parent
RAW = HERE / "results" / "A06" / "RAW.jsonl"

if RAW.exists():
    raise SystemExit("STOP_RAW_ALREADY_EXISTS")
RAW.parent.mkdir(parents=True, exist_ok=True)
RAW.touch(exist_ok=False)

active = {"case": None, "drop_code": None, "dropped": False}
displays = []
events = []

def record(name, **fields):
    events.append({"case": active["case"], "event": name,
                   "time_ns": time.perf_counter_ns(), **fields})

class FakeRoot:
    id = 1
    def query_pointer(self):
        record("query_pointer")
        return types.SimpleNamespace(mask=0, root_x=0, root_y=0, child=None)
    def get_geometry(self):
        return types.SimpleNamespace(width=1024, height=768)

class FakeDisplay:
    def __init__(self, name):
        self.name = name
        self.root = FakeRoot()
        self.keys = set()
        self.fail_query_next = False
        self.query_count = 0
        displays.append(self)
        record("display_open", display=name)
    def screen(self):
        return types.SimpleNamespace(root=self.root)
    def get_input_focus(self):
        return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
    def keysym_to_keycode(self, sym):
        return {"a": 38, "space": 65}.get(sym, 0)
    def sync(self):
        record("xsync")
    def query_keymap(self):
        self.query_count += 1
        if self.fail_query_next:
            self.fail_query_next = False
            record("query_keymap_unavailable", query_count=self.query_count)
            raise RuntimeError("injected post-batch query unavailable")
        record("query_keymap", keys=sorted(self.keys), query_count=self.query_count)
        bitmap = bytearray(32)
        for code in self.keys:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)
    def close(self):
        record("display_close")

X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                          ButtonRelease=5, Button1Mask=256,
                          AnyPropertyType=0, IsViewable=2)
XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
display = types.SimpleNamespace(Display=FakeDisplay)
error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                              BadDrawable=type("BadDrawable", (Exception,), {}))

def fake_input(d, event_type, detail):
    if event_type == X.KeyPress:
        d.keys.add(detail)
        record("key_down", keycode=detail)
    elif event_type == X.KeyRelease:
        if (detail == active["drop_code"] and not active["dropped"]):
            active["dropped"] = True
            record("key_up_dropped_once", keycode=detail)
            return
        d.keys.discard(detail)
        record("key_up", keycode=detail)
    else:
        record("button", keycode=detail)

xlib = types.ModuleType("Xlib")
xlib.X, xlib.XK, xlib.display, xlib.error = X, XK, display, error
xext = types.ModuleType("Xlib.ext")
xext.xtest = types.SimpleNamespace(fake_input=fake_input)
sys.modules.update({"Xlib": xlib, "Xlib.ext": xext})

owner_v10 = types.ModuleType("input_owner_v10")
owner_v10.InputOwner = type("UnusedV10", (), {})
sys.modules["input_owner_v10"] = owner_v10

base = types.ModuleType("doom_typed_release_backend_v2")
class FakeTypedBackendBase:
    def __init__(self, session, out, emit, signal_readers):
        self.owner = types.SimpleNamespace(close=lambda: None)
        self.held = set()
        self.emit = emit
        self._input_event_context = None
        self.lease = types.SimpleNamespace(
            intent_token="a06-probe", deadline=time.perf_counter_ns() + 60_000_000_000,
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
base.Backend = FakeTypedBackendBase
base.suite = object()
sys.modules["doom_typed_release_backend_v2"] = base

from doom_owner_thread_release_batch_backend_v1 import Backend

def persist(row):
    with RAW.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())

def run_case(name, *, drop_code=None, fail_cleanup_query=False):
    active.update(case=name, drop_code=drop_code, dropped=False)
    first_event = len(events)
    rows = []
    backend = Backend(types.SimpleNamespace(name="fake-x11-a06"), None, rows.append, {})
    owner = backend.owner
    display_for_case = displays[-1]
    backend.execute({"keys": ["a", "space"]}, None, name, 1)
    record("release_batch_returned", rows=len(rows))
    if fail_cleanup_query:
        display_for_case.fail_query_next = True
    close_error = None
    try:
        owner.close()
    except Exception as exc:
        close_error = type(exc).__name__
        record("owner_close_error", error=close_error)
    recs = getattr(owner, "records", [])
    case = {
        "case": name,
        "release_rows": rows,
        "owner_records": recs,
        "dropped_up_once": active["dropped"],
        "close_error": close_error,
        "fake_keys_after_close": sorted(display_for_case.keys),
        "events": events[first_event:],
    }
    case["disposition"] = "HOLD_QUERY_UNAVAILABLE" if fail_cleanup_query and close_error else "OBSERVED"
    persist(case)
    return case

results = [
    run_case("normal"),
    run_case("drop_explicit_space_once", drop_code=65),
    run_case("cleanup_query_unavailable_once", fail_cleanup_query=True),
]
print(json.dumps({"cases": [r["case"] for r in results], "raw": str(RAW)}, sort_keys=True))
