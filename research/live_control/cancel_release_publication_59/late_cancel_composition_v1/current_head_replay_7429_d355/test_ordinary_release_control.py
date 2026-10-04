"""Compose ExecutorV12 publication with the real owner release handler."""
import importlib.util
import json
import queue
import sys
import threading
import time
import types
import unittest
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))
sys.path[0:0] = [
    str(LIVE / "dependencies" / "main"),
    str(LIVE / "dependencies" / "pr7429"),
    str(LIVE / "dependencies" / "pr7440"),
]

# Import the production executor stack before installing the fake Xlib modules.
import executor_v12
import executor_v3


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
        pass

    def close(self):
        pass


class DeferredOwnerVisibility:
    """Expose cancel to Executor immediately, but to owner only at dispatch."""
    def __init__(self, owner_thread):
        self.owner_thread = owner_thread
        self.pending = threading.Event()
        self.dispatched = threading.Event()

    def set(self):
        self.pending.set()
        if threading.get_ident() == self.owner_thread:
            self.dispatched.set()

    def is_set(self):
        if threading.get_ident() == self.owner_thread and self.pending.is_set():
            return self.dispatched.is_set()
        return self.pending.is_set()

    def wait(self, timeout=None):
        return self.pending.wait(timeout)


def make_owner():
    names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
             "Xlib.ext", "Xlib.ext.xtest")
    saved = {name: sys.modules.get(name) for name in names}
    xlib = types.ModuleType("Xlib")
    constants = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                      Button1Mask=256, AnyPropertyType=0)
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    displays = []

    def make_display(name):
        value = FakeDisplay(name)
        displays.append(value)
        return value

    display.Display = make_display
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(connection, event, code):
        connection.events.append((event, code))
        if event == constants.KeyPress:
            connection.down.add(code)
        elif event == constants.KeyRelease:
            connection.down.discard(code)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.X = constants
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                        "Xlib.XK": xk, "Xlib.display": display,
                        "Xlib.error": error, "Xlib.ext": ext,
                        "Xlib.ext.xtest": xtest})

    owner_path = LIVE / "dependencies" / "pr7440" / "input_owner_v12.py"
    spec = importlib.util.spec_from_file_location("owner_under_test", owner_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["owner_under_test"] = module
    spec.loader.exec_module(module)
    import input_transition_owner_v4

    release_dequeued = threading.Event()
    lease_slot = [None]
    factory = queue.Queue

    def controlled_queue(*args, **kwargs):
        result = factory(*args, **kwargs)
        original_get = result.get

        def get(*get_args, **get_kwargs):
            item = original_get(*get_args, **get_kwargs)
            if item[0] == "release":
                release_dequeued.set()
            return item

        result.get = get
        return result

    queue.Queue = controlled_queue
    try:
        owner = input_transition_owner_v4.InputOwner(":fake")
    finally:
        queue.Queue = factory
    owner_thread = owner._inner.thread.ident
    return owner, displays, constants, release_dequeued, lease_slot, owner_thread, saved


class Backend:
    sequence = 1

    def __init__(self, owner, lease_slot):
        self.owner = owner
        self.lease_slot = lease_slot
        self.started = threading.Event()
        self.continue_step = threading.Event()
        self.lease = None

    def validate(self, _steps):
        pass

    def execute(self, _step, lease, _identifier, _index):
        self.lease = lease
        lease.expected_focus = 41
        self.lease_slot[0] = lease
        self.owner.call("down", lease, "W")
        self.started.set()
        self.continue_step.wait(1)

    def release_all(self):
        return self.owner.call("release", self.lease)


class ExecutorOwnerCancelCauseTests(unittest.TestCase):
    def test_ordinary_release_control(self):
        owner_source = (LIVE / "dependencies" / "pr7440" / "input_owner_v12.py").resolve()
        hook_fired = threading.Event()

        def source_line_hook(frame, event, _arg):
            if (event == "line" and frame.f_code.co_name == "_run"
                    and Path(frame.f_code.co_filename).resolve() == owner_source
                    and frame.f_lineno == 266):
                hook_fired.set()
                return None
            return source_line_hook

        threading.settrace(source_line_hook)
        try:
            owner, displays, constants, dequeued, lease_slot, owner_thread, saved = make_owner()
        finally:
            threading.settrace(None)
        events = []
        backend = Backend(owner, lease_slot)
        executor = executor_v12.Executor(backend, events.append)
        try:
            executor.submit("integration", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 5_000_000_000)
            self.assertTrue(backend.started.wait(1))
            worker = executor.active[2]
            backend.continue_step.set()
            self.assertTrue(dequeued.wait(1))
            self.assertTrue(hook_fired.wait(1))
            worker.join(1)
            self.assertFalse(worker.is_alive())

            release_events = [row for row in events if row["event"] == "input_released"]
            terminal = next(row for row in events if row["event"] == "terminal")
            owner_releases = [row for row in owner.records if row.get("event") == "owner_release"]
            self.assertEqual(len(release_events), 0, events)
            self.assertEqual(len(owner_releases), 1)
            self.assertEqual(owner_releases[0]["reason"], "release")
            self.assertTrue(owner_releases[0]["verified"])
            self.assertEqual(owner_releases[0]["keys_down"], [])
            self.assertEqual(owner_releases[0]["buttons_down"], [])
            self.assertIsNone(terminal.get("interruption"))
            self.assertNotIn("input_release_publication", terminal)
            self.assertEqual(terminal["status"], "completed")
            result = {
                "experiment": "CROSS-COMPONENT-POST-SAMPLE-CANCEL-7429-7440",
                "classification": "ORDINARY_RELEASE_CONTROL",
                "trigger": "No cancellation; same owner release reason-sample source line and key-up operation",
                "owner_release": owner_releases[0],
                "emitted_events": [row.get("event") for row in events],
                "input_released_count": len(release_events),
                "terminal": terminal,
                "fake_x_events": displays[0].events,
            }
            (LIVE / "RUN-02-FIX2.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(displays[0].events,
                             [(constants.KeyPress, 38), (constants.KeyRelease, 38)])
        finally:
            backend.continue_step.set()
            executor.close()
            owner.close()
            sys.modules.pop("owner_under_test", None)
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
