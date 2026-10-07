"""One-shot deterministic post-sample cancellation boundary probe."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time
import types

HERE = Path(__file__).resolve().parent
SOURCES = {
    "main_v10": HERE / "dependencies" / "input_owner_v10.py",
    "pr7440_v12": HERE / "dependencies" / "input_owner_v12.py",
}


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        return None

    def close(self):
        return None


class CancelAtNextSample:
    """Arm after dequeue; sample False, then flip the event before returning."""
    def __init__(self):
        self.state = False
        self.armed = False
        self.fired = False
        self.arm_ns = None
        self.sample_false_ns = None
        self.cancel_visible_ns = None
        self.sample_ready = threading.Event()
        self.visible = threading.Event()
        self.setter_thread = None

    def arm_after_dequeue(self):
        self.armed = True
        self.arm_ns = time.perf_counter_ns()
        self.setter_thread = threading.Thread(target=self._set_after_sample,
                                              name="c03-canceller", daemon=True)
        self.setter_thread.start()

    def _set_after_sample(self):
        if not self.sample_ready.wait(1):
            return
        self.state = True
        self.cancel_visible_ns = time.perf_counter_ns()
        self.visible.set()

    def set(self):
        self.state = True
        self.cancel_visible_ns = time.perf_counter_ns()

    def is_set(self):
        sampled = self.state
        if self.armed and not self.fired:
            self.fired = True
            self.sample_false_ns = time.perf_counter_ns()
            self.sample_ready.set()
            if not self.visible.wait(1):
                raise RuntimeError("canceller missed the post-sample synchronization window")
            return sampled
        return sampled


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = CancelAtNextSample()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interruptions = []

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("fixture lease unexpectedly expired")

    def record_interruption(self, receipt):
        self.interruptions.append(receipt)


def load_owner(path, dequeued, lease_slot, cancel_mode):
    module_names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                    "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "owner_under_test")
    saved = {name: sys.modules.get(name) for name in module_names}
    xlib = types.ModuleType("Xlib")
    constants = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                      Button1Mask=256, AnyPropertyType=0)
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    displays = []

    def make_display(name):
        result = FakeDisplay(name)
        displays.append(result)
        return result

    display.Display = make_display
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(connection, event, code):
        now = time.perf_counter_ns()
        connection.events.append({"event": event, "keycode": code, "at_ns": now})
        if event == constants.KeyPress:
            connection.down.add(code)
        elif event == constants.KeyRelease:
            connection.down.discard(code)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.X, xlib.XK, xlib.display, xlib.error, xlib.ext = constants, xk, display, error, ext
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                        "Xlib.XK": xk, "Xlib.display": display, "Xlib.error": error,
                        "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
                        "executor_v3": executor})

    factory = queue.Queue

    def controlled_queue(*args, **kwargs):
        result = factory(*args, **kwargs)
        original_get = result.get

        def get(*get_args, **get_kwargs):
            item = original_get(*get_args, **get_kwargs)
            if item[0] == "release":
                dequeued.set()
                dequeued.timestamp_ns = time.perf_counter_ns()
                if cancel_mode == "before_release_dispatch":
                    lease_slot[0].cancel.set()
                elif cancel_mode == "after_cause_sample":
                    lease_slot[0].cancel.arm_after_dequeue()
            return item

        result.get = get
        return result

    queue.Queue = controlled_queue
    try:
        spec = importlib.util.spec_from_file_location("owner_under_test", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["owner_under_test"] = module
        spec.loader.exec_module(module)
        owner = module.InputOwner(":fake")
    finally:
        queue.Queue = factory
    return owner, displays, constants, saved


def restore_modules(saved):
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def exercise(label, source, cancel_mode):
    dequeued = threading.Event()
    lease_slot = [None]
    owner, displays, constants, saved = load_owner(source, dequeued, lease_slot, cancel_mode)
    lease = Lease()
    lease_slot[0] = lease
    try:
        owner.call("down", lease, "W")
        receipt = owner.call("release", lease)
        if not dequeued.wait(1):
            raise RuntimeError("release was not dequeued within 1 s")
        if lease.cancel.setter_thread is not None:
            lease.cancel.setter_thread.join(timeout=1)
        owner_receipt = lease.interruptions[-1]
        return {
            "source": label,
            "key_events": displays[0].events,
            "owner_receipt": owner_receipt,
            "release_reply_verified": receipt.get("verified") is True,
            "cancel_sample_false_ns": lease.cancel.sample_false_ns,
            "cancel_visible_ns": lease.cancel.cancel_visible_ns,
            "cancel_armed_after_dequeue_ns": lease.cancel.arm_ns,
            "dequeued_ns": getattr(dequeued, "timestamp_ns", None),
            "cancel_state_after_release": lease.cancel.state,
            "canceller_thread_finished": (
                lease.cancel.setter_thread is None or not lease.cancel.setter_thread.is_alive()),
        }
    finally:
        owner.close()
        restore_modules(saved)


def main():
    outputs = [exercise("main_v10_dequeue_cancel", SOURCES["main_v10"],
                        "before_release_dispatch"),
               exercise("pr7440_v12_post_sample_cancel", SOURCES["pr7440_v12"],
                        "after_cause_sample"),
               exercise("pr7440_v12_ordinary_control", SOURCES["pr7440_v12"], "none")]
    report = {"schema": "map01-v39-cancel-release-cause-c03-raw-v1",
              "cases": outputs,
              "source_sha256": {label: hashlib.sha256(path.read_bytes()).hexdigest()
                                for label, path in SOURCES.items()},
              "python": sys.version,
              "platform": sys.platform}
    (HERE / "candidate.raw.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
