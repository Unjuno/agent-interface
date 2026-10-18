"""Deterministically compare #7429 owner V12 with the additive cause recheck."""
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import types

HERE = Path(__file__).resolve().parent
LIVE = HERE.parents[2] / "live_control"
BASE = "0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2"
OWNER_PATH = LIVE / "input_owner_v12.py"


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self): return types.SimpleNamespace(focus=41)
    def keysym_to_keycode(self, _keysym): return 38
    def screen(self): return types.SimpleNamespace(root=self.root)
    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down: bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)
    def sync(self): pass
    def close(self): pass


class CancelAtNextSample:
    def __init__(self):
        self.state = False
        self.armed = False
        self.fired = False
        self.sampled_ns = None
        self.visible_ns = None
        self.sample_ready = threading.Event()
        self.visible = threading.Event()
        self.setter = None

    def arm(self):
        self.armed = True
        self.setter = threading.Thread(target=self._set_after_sample, daemon=True)
        self.setter.start()

    def _set_after_sample(self):
        if not self.sample_ready.wait(1): return
        self.state = True
        self.visible_ns = time.perf_counter_ns()
        self.visible.set()

    def is_set(self):
        sampled = self.state
        if self.armed and not self.fired:
            self.fired = True
            self.sampled_ns = time.perf_counter_ns()
            self.sample_ready.set()
            if not self.visible.wait(1):
                raise RuntimeError("canceller missed synchronized post-sample boundary")
            return sampled
        return sampled

    def set(self): self.state = True


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.intent_token = "intent-a01"
        self.cancel = CancelAtNextSample()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interruptions = []

    def check(self):
        if time.perf_counter_ns() >= self.deadline: raise RuntimeError("fixture lease expired")
    def record_interruption(self, receipt): self.interruptions.append(receipt)


def fake_modules():
    names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
             "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
             "input_owner_v11", "owner_under_test")
    saved = {name: sys.modules.get(name) for name in names}
    constants = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                      Button1Mask=256, AnyPropertyType=0,
                                      IsViewable=2)
    xlib = types.ModuleType("Xlib")
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    displays = []
    def make_display(name):
        result = FakeDisplay(name); displays.append(result); return result
    display.Display = make_display
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    def fake_input(connection, event, code):
        connection.events.append((event, code))
        if event == constants.KeyPress: connection.down.add(code)
        if event == constants.KeyRelease: connection.down.discard(code)
    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.X, xlib.XK, xlib.display, xlib.error, xlib.ext = constants, xk, display, error, ext
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                        "Xlib.XK": xk, "Xlib.display": display,
                        "Xlib.error": error, "Xlib.ext": ext,
                        "Xlib.ext.xtest": xtest, "executor_v3": executor})
    return names, saved, constants, displays


def load_class(source_bytes):
    module = types.ModuleType("owner_under_test")
    module.__file__ = str(OWNER_PATH)
    sys.modules["owner_under_test"] = module
    exec(compile(source_bytes, str(OWNER_PATH), "exec"), module.__dict__)
    return module.InputOwner, module


def exercise(source_bytes, race):
    names, saved, constants, displays = fake_modules()
    dequeue = threading.Event()
    lease_box = [None]
    factory = queue.Queue
    def controlled_queue(*args, **kwargs):
        result = factory(*args, **kwargs)
        original_get = result.get
        def get(*get_args, **get_kwargs):
            item = original_get(*get_args, **get_kwargs)
            if item[0] == "release":
                dequeue.set()
                if race: lease_box[0].cancel.arm()
            return item
        result.get = get
        return result
    queue.Queue = controlled_queue
    try:
        cls, module = load_class(source_bytes)
        owner = cls(":fake")
    finally:
        queue.Queue = factory
    lease = Lease(); lease_box[0] = lease
    try:
        owner.call("down", lease, "W")
        reply = owner.call("release", lease)
        if not dequeue.wait(1): raise RuntimeError("release request was not dequeued")
        if lease.cancel.setter is not None: lease.cancel.setter.join(1)
        record = lease.interruptions[-1]
        return {"reason": record["reason"], "verified": record["verified"],
                "keys_down": record["keys_down"], "buttons_down": record["buttons_down"],
                "physical_events": displays[0].events,
                "release_reply_verified": reply.get("verified") is True,
                "cancel_sampled_ns": lease.cancel.sampled_ns,
                "cancel_visible_ns": lease.cancel.visible_ns,
                "setter_finished": lease.cancel.setter is None or not lease.cancel.setter.is_alive(),
                "parent_owner_module": cls.__bases__[0].__module__,
                "owner_class": cls.__module__ + "." + cls.__name__}
    finally:
        owner.close()
        for name in names:
            sys.modules.pop(name, None)
        for name, mod in saved.items():
            if mod is not None: sys.modules[name] = mod


def exercise_telemetry(source_bytes):
    names, saved, constants, displays = fake_modules()
    cls, module = load_class(source_bytes)
    owner = cls(":fake")
    lease = Lease()
    try:
        owner.call("down", lease, "W")
        receipt = owner.call("up", lease, "W")
        return {"event": receipt.get("event"),
                "interval": receipt.get("release_transition_interval_ns"),
                "intent_token": receipt.get("intent_token"),
                "grants_input_authority": receipt.get("grants_input_authority"),
                "parent_owner_module": cls.__bases__[0].__module__,
                "physical_events": displays[0].events}
    finally:
        owner.close()
        for name in names: sys.modules.pop(name, None)
        for name, mod in saved.items():
            if mod is not None: sys.modules[name] = mod


def main():
    base_bytes = subprocess.check_output(
        ["git", "show", f"{BASE}:research/live_control/input_owner_v12.py"])
    candidate_bytes = OWNER_PATH.read_bytes()
    outputs = {
        "parent_forced_post_sample_cancel": exercise(base_bytes, True),
        "candidate_forced_post_sample_cancel": exercise(candidate_bytes, True),
        "candidate_ordinary_release": exercise(candidate_bytes, False),
        "candidate_explicit_up_telemetry": exercise_telemetry(candidate_bytes),
    }
    result = {"schema": "owner-telemetry-cancel-cause-a01-v1",
              "base_commit": BASE,
              "base_owner_sha256": hashlib.sha256(base_bytes).hexdigest(),
              "candidate_owner_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
              "python": sys.version, "platform": sys.platform, "cases": outputs}
    (HERE / "RAW.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
