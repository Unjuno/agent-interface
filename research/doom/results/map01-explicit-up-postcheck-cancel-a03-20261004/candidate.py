from __future__ import annotations
import json, pathlib, sys, threading, time, types

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "source_snapshot" / "research" / "live_control"
sys.path.insert(0, str(SOURCE))

# Minimal fake Xlib surface for the keyboard-only branch in the frozen owner.
X = types.ModuleType("Xlib.X")
for name, value in {"AnyPropertyType": 0, "IsViewable": 2, "Button1Mask": 256,
                    "KeyRelease": 3, "KeyPress": 2, "ButtonRelease": 5,
                    "ButtonPress": 4, "MotionNotify": 6}.items():
    setattr(X, name, value)
XK = types.ModuleType("Xlib.XK")
XK.string_to_keysym = lambda value: 119 if value == "w" else 0
error = types.ModuleType("Xlib.error")
error.BadWindow = type("BadWindow", (Exception,), {})
error.BadDrawable = type("BadDrawable", (Exception,), {})

class Root:
    id = 1
    def query_pointer(self): return types.SimpleNamespace(mask=0)
class Screen:
    def __init__(self): self.root = Root()
class FakeDisplay:
    def __init__(self, _name):
        self.events = []
        self.keys_down = set()
        self._screen = Screen()
        FakeDisplay.last = self
    def get_input_focus(self): return types.SimpleNamespace(focus=types.SimpleNamespace(id=42))
    def keysym_to_keycode(self, _keysym): return 30
    def screen(self): return self._screen
    def query_keymap(self):
        bitmap = bytearray(32)
        for keycode in self.keys_down: bitmap[keycode // 8] |= 1 << (keycode % 8)
        return bytes(bitmap)
    def sync(self): pass
    def close(self): pass

display = types.ModuleType("Xlib.display")
display.Display = FakeDisplay
xtest = types.ModuleType("Xlib.ext.xtest")
active = {"cancel": None, "display": None, "keyrelease": []}
def fake_input(d, event, detail=None, **kwargs):
    if event == X.KeyPress: d.keys_down.add(detail)
    if event == X.KeyRelease:
        token = active["cancel"]
        active["keyrelease"].append({
            "event": "KeyRelease", "keycode": detail,
            "cancel_set_at_side_effect": token.is_set(),
            "side_effect_ns": time.perf_counter_ns(),
        })
        d.keys_down.discard(detail)
    d.events.append({"event": event, "detail": detail, "kwargs": kwargs})
xtest.fake_input = fake_input
ext = types.ModuleType("Xlib.ext"); ext.xtest = xtest
xlib = types.ModuleType("Xlib"); xlib.X = X; xlib.XK = XK; xlib.display = display; xlib.error = error; xlib.ext = ext
sys.modules.update({"Xlib": xlib, "Xlib.X": X, "Xlib.XK": XK,
                    "Xlib.display": display, "Xlib.error": error,
                    "Xlib.ext": ext, "Xlib.ext.xtest": xtest})

from input_owner_v12 import InputOwner as OwnerV12
from input_transition_owner_v4 import InputOwner as TransitionOwnerV4

class CancelFlag:
    def __init__(self): self._event = threading.Event(); self.set_ns = None; self.samples = []
    def set(self):
        if self.set_ns is None: self.set_ns = time.perf_counter_ns()
        self._event.set()
    def is_set(self):
        value = self._event.is_set()
        self.samples.append({"thread_id": threading.get_ident(), "value": value,
                             "sample_ns": time.perf_counter_ns()})
        return value

class Lease:
    def __init__(self):
        self.cancel = CancelFlag()
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.expected_focus = 42
        self.focus_invalid = False
        self.intent_token = "explicit-up-postcheck-a01"
    def check(self):
        if time.perf_counter_ns() >= self.deadline: raise RuntimeError("expired")

lease = Lease()
active["cancel"] = lease.cancel
owner = TransitionOwnerV4("fake-display", _owner_cls=OwnerV12)
owner_v12 = owner._inner
original_get = owner_v12.requests.get
hook = {"set_ns": None, "queue_dequeue_ns": None}
def controlled_get(block=True, timeout=None):
    request = original_get(block=block, timeout=timeout)
    if request[0] == "up" and hook["set_ns"] is None:
        hook["queue_dequeue_ns"] = time.perf_counter_ns()
        lease.cancel.set()
        hook["set_ns"] = lease.cancel.set_ns
    return request
owner_v12.requests.get = controlled_get

result = {"hypothesis_id": "EXPLICIT-UP-POSTCHECK-CANCEL-A03-20261004",
          "frozen_merge_tree": "71b723028a2db51a7f14a6db653d7f3789fa988b",
          "host_runtime": "macOS 27.0.1 / Python 3.14.5",
          "candidate_started_ns": time.perf_counter_ns(), "candidate_exit": None}
try:
    result["down_result"] = owner.call("down", lease, "w")
    result["up_transition"] = owner.call("up", lease, "w")
    result["owner_thread_id"] = owner_v12.thread.ident
    result["cancel_set_ns"] = lease.cancel.set_ns
    result["cancel_samples"] = lease.cancel.samples
    result["queue_dequeue_ns"] = hook["queue_dequeue_ns"]
    result["fake_keyrelease"] = list(active["keyrelease"])
    result["owner_state_after_up"] = owner.call("input_state")
    bitmap = FakeDisplay.last.query_keymap()
    result["keycode_30_down_after_up"] = bool(bitmap[30 // 8] & (1 << (30 % 8)))
    result["owner_records_before_close"] = list(owner_v12.records)
    result["candidate_exit"] = 0
except BaseException as exc:
    result["candidate_exit"] = 1
    result["candidate_exception"] = repr(exc)
finally:
    try:
        owner.close()
    except BaseException as exc:
        result["close_exception"] = repr(exc)
    result["owner_records_after_close"] = list(owner_v12.records)
    result["owner_thread_stopped"] = owner_v12.stopped.is_set()
    result["candidate_finished_ns"] = time.perf_counter_ns()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
if result["candidate_exit"]:
    raise SystemExit(1)
