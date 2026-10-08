"""Exercise marker pruning across repeated asynchronous owner cancellations."""
import importlib.util
from pathlib import Path
import sys
import threading
import time
import types


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WRAPPER = REPO / "research/live_control/input_transition_owner_v3.py"
OWNER = REPO / "research/live_control/input_owner_v10.py"
EXPECTED = {
    "input_transition_owner_v3.py":
        "672e7471b91f321f0d8723ef6277d974b24b2fa322f5e89907b17bf92998f177",
    "input_owner_v10.py":
        "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
}


def sha256(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, path in (("input_transition_owner_v3.py", WRAPPER),
                   ("input_owner_v10.py", OWNER)):
    if sha256(path) != EXPECTED[name]:
        raise SystemExit(f"STOP_SOURCE_DRIFT {name}")


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0))

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


class Lease:
    def __init__(self):
        self.intent_token = "marker-cycle"
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")


names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
         "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10")
saved = {name: sys.modules.get(name) for name in names}
try:
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
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
        connection.events.append((event, code))
        if event == xlib.X.KeyPress:
            connection.down.add(code)
        elif event == xlib.X.KeyRelease:
            connection.down.discard(code)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules.update({
        "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk,
        "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext,
        "Xlib.ext.xtest": xtest, "executor_v3": executor,
    })

    spec = importlib.util.spec_from_file_location("input_owner_v10", OWNER)
    owner_module = importlib.util.module_from_spec(spec)
    sys.modules["input_owner_v10"] = owner_module
    spec.loader.exec_module(owner_module)
    spec = importlib.util.spec_from_file_location("input_transition_owner_v3", WRAPPER)
    wrapper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper_module)

    owner = wrapper_module.InputOwner(":fake")
    try:
        max_markers = 0
        for index in range(64):
            lease = Lease()
            previous_records = len(owner.records)
            admission = owner.call("down", lease, "a")
            assert admission["event"] == "input_admission"
            lease.cancel.set()
            end = time.monotonic() + 1
            while len(owner.records) == previous_records and time.monotonic() < end:
                time.sleep(0.001)
            assert len(owner.records) == previous_records + 1, index
            cleanup = owner.records[-1]
            assert (cleanup["event"] == "owner_release"
                    and cleanup["reason"] == "cancelled"
                    and cleanup["verified"] is True)
            count = len(owner._admission_records)
            assert count == 1, (index, count)
            max_markers = max(max_markers, count)
        assert len(displays[0].events) == 128
        assert len(owner._admission_records) == 1
        print("PASS cycles=64 verified_cancel_cleanup=64 key_events=128 "
              f"peak_markers={max_markers} final_markers={len(owner._admission_records)}")
    finally:
        owner.close()
finally:
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module
