"""Construction tests for a patched, isolated copy of #5630 InputOwner."""
import importlib.util
import sys
import threading
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dependencies" / "input_owner_v11.py"


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.events = []
        self.keymap_queries = []

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, symbol):
        return {"W": 25}.get(symbol, 0)

    def sync(self):
        return None

    def screen(self):
        return types.SimpleNamespace(root=types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0)))

    def query_keymap(self):
        bitmap = bytearray(32)
        for keycode in self.down:
            bitmap[keycode // 8] |= 1 << (keycode % 8)
        self.keymap_queries.append(bytes(bitmap))
        return bytes(bitmap)

    def close(self):
        return None


class Lease:
    expected_focus = 42
    intent_token = "t2-repeat-w"

    def __init__(self):
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("test lease expired")


def install_xlib(display_state):
    X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
        ButtonRelease=5, MotionNotify=6, Button1Mask=256, AnyPropertyType=0,
        IsViewable=2)
    XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
    display = types.ModuleType("Xlib.display")
    display.Display = lambda _name: display_state
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(_display, event, detail, **_kwargs):
        if event == X.KeyPress:
            display_state.down.add(detail)
        elif event == X.KeyRelease:
            display_state.down.discard(detail)
        display_state.events.append((event, detail))

    xtest.fake_input = fake_input
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = xtest
    xlib = types.ModuleType("Xlib")
    xlib.X, xlib.XK, xlib.display, xlib.error = X, XK, display, error
    sys.modules.update({"Xlib": xlib, "Xlib.display": display,
        "Xlib.error": error, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor


class OwnerOccurrenceContractTests(unittest.TestCase):
    def run_two_explicit_cycles(self):
        fake = FakeDisplay()
        install_xlib(fake)
        spec = importlib.util.spec_from_file_location("t2_input_owner", SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        owner = module.InputOwner("fake-display")
        lease = Lease()
        admissions = [owner.call("down", lease, "W")]
        owner.call("up", lease, "W")
        admissions.append(owner.call("down", lease, "W"))
        owner.call("up", lease, "W")
        owner.close()
        return fake, admissions, owner.records

    def test_each_repeated_explicit_up_keeps_its_admission_occurrence_id(self):
        _fake, admissions, records = self.run_two_explicit_cycles()
        releases = [row for row in records
                    if row.get("event") == "owner_key_release_bracket"]
        ids = [row.get("interval_id") for row in admissions]
        self.assertEqual(len(ids), 2)
        self.assertTrue(all(isinstance(value, str) and value for value in ids),
                        "each down admission must return an interval_id")
        self.assertEqual(len(set(ids)), 2, "repeated W presses need distinct IDs")
        self.assertEqual([row.get("interval_id") for row in releases], ids,
                         "each explicit-up bracket must carry its matching ID")

    def test_each_interval_has_ordered_full_keymap_witnesses(self):
        _fake, admissions, records = self.run_two_explicit_cycles()
        witnesses = [row for row in records
                     if row.get("event") == "owner_keymap_witness"]
        self.assertEqual(len(witnesses), 6,
                         "two intervals need pre-down, post-down, and post-up samples")
        expected_stages = ["pre_down", "post_down", "post_up"] * 2
        expected_pressed = [False, True, False] * 2
        self.assertEqual([row.get("stage") for row in witnesses], expected_stages)
        self.assertEqual([row.get("key_down") for row in witnesses], expected_pressed)
        self.assertEqual([row.get("interval_id") for row in witnesses],
                         [admissions[0]["interval_id"]] * 3
                         + [admissions[1]["interval_id"]] * 3)
        self.assertTrue(all(row.get("bitmap_hex") and len(row["bitmap_hex"]) == 64
                            and row.get("bitmap_sha256") for row in witnesses),
                        "every witness must retain the complete 32-byte bitmap")
        self.assertTrue(all(type(row.get("sample_started_ns")) is int
                            and type(row.get("sample_finished_ns")) is int
                            and row["sample_started_ns"] <= row["sample_finished_ns"]
                            for row in witnesses),
                        "every query must retain a monotonic call bracket")
        self.assertTrue(all(row.get("grants_input_authority") is False
                            and row.get("physical_key_up_claimed") is False
                            for row in witnesses),
                        "keymap witnesses are evidence, not authority or physical-key claims")


if __name__ == "__main__":
    unittest.main()
