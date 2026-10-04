"""One deterministic fake-Xlib boundary: cancellation during batch XSync."""
from __future__ import annotations

import importlib.util
import sys
import threading
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / "dependencies"
CANDIDATE = ROOT / "candidate/input_owner_v12_composed.py"
sys.path.insert(0, str(DEPS))

STATE = {
    "down": set(),
    "key_events": [],
    "sync_count": 0,
    "release_hook": None,
    "display": None,
}


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)


class FakeDisplay:
    def __init__(self, _name=None):
        self.root = FakeRoot()
        STATE["display"] = self

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, symbol):
        return symbol % 200 + 10

    def query_keymap(self):
        out = bytearray(32)
        for code in STATE["down"]:
            out[code // 8] |= 1 << (code % 8)
        return bytes(out)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def sync(self):
        STATE["sync_count"] += 1
        hook = STATE["release_hook"]
        if hook is not None:
            STATE["release_hook"] = None
            hook()

    def close(self):
        pass


def fake_input(_display, event, code, **_kwargs):
    STATE["key_events"].append([event, code])
    if event == 2:
        STATE["down"].add(code)
    elif event == 3:
        STATE["down"].discard(code)
    else:
        raise AssertionError(f"unexpected XTest event {event}")


def install_fake_xlib():
    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonPress=4, ButtonRelease=5,
        MotionNotify=6, Button1Mask=256, AnyPropertyType=0, IsViewable=2,
    )
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda value: ord(value[0]))
    xlib.display = types.SimpleNamespace(Display=FakeDisplay)
    xlib.error = types.SimpleNamespace(
        BadWindow=type("BadWindow", (Exception,), {}),
        BadDrawable=type("BadDrawable", (Exception,), {}),
    )
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.ext = ext
    sys.modules.update({"Xlib": xlib, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})


install_fake_xlib()
spec = importlib.util.spec_from_file_location("owner_under_test", CANDIDATE)
owner_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = owner_module
spec.loader.exec_module(owner_module)
InputOwner = owner_module.InputOwner


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.intent_token = "a01-intent"
        self.cancel = threading.Event()
        self.expected_focus = 41

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("expired")
        if self.cancel.is_set():
            raise RuntimeError("cancelled")


def reset_state():
    STATE["down"].clear()
    STATE["key_events"].clear()
    STATE["sync_count"] = 0
    STATE["release_hook"] = None
    STATE["display"] = None


def run_batch_cancel_during_sync():
    reset_state()
    owner, lease = InputOwner(":fake"), Lease()
    try:
        owner.call("down", lease, "W")
        owner.call("down", lease, "A")
        before = STATE["sync_count"]
        STATE["release_hook"] = lease.cancel.set
        receipt = owner.call("release", lease)
        after = STATE["sync_count"]
        return {
            "case": "batch_cancel_during_sync",
            "receipt": receipt,
            "release_sync_delta": after - before,
            "key_events": list(STATE["key_events"]),
            "final_down": sorted(STATE["down"]),
            "cancel_set": lease.cancel.is_set(),
        }
    finally:
        owner.close()


def run_explicit_up_cancel_during_sync():
    reset_state()
    owner, lease = InputOwner(":fake"), Lease()
    try:
        owner.call("down", lease, "W")
        STATE["release_hook"] = lease.cancel.set
        owner.call("up", lease, "W")
        receipts = [r for r in owner.records if r.get("event") == "owner_explicit_keyup"]
        return {
            "case": "explicit_up_cancel_during_sync",
            "receipt": receipts[0] if receipts else None,
            "key_events": list(STATE["key_events"]),
            "cancel_set": lease.cancel.is_set(),
        }
    finally:
        owner.close()


def run_scenarios():
    batch = run_batch_cancel_during_sync()
    explicit = run_explicit_up_cancel_during_sync()
    return {"schema": "batch-cancel-sync-composition-a01-raw-v1", "cases": [batch, explicit]}
