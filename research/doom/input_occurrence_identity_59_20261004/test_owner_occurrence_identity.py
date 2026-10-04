import sys
import threading
import time
import types
import unittest


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, key):
        return {"W": 38, "A": 39}[key]

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


class Lease:
    def __init__(self):
        self.deadline = 2**62
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interrupted = threading.Event()
        self.interruptions = []
        self.intent_token = "intent-test"

    def check(self):
        pass

    def record_interruption(self, row):
        self.interruptions.append(row)
        self.interrupted.set()


class OwnerOccurrenceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                      "Xlib.ext", "Xlib.ext.xtest")
        self.saved = {name: sys.modules.get(name) for name in self.names}
        self.display_instance = FakeDisplay()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0)
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: key
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: self.display_instance
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            if event == xlib.X.KeyPress:
                self.display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                self.display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                            "Xlib.XK": xk, "Xlib.display": display,
                            "Xlib.error": error, "Xlib.ext": ext,
                            "Xlib.ext.xtest": xtest})
        sys.modules.pop("input_owner_v12", None)
        from input_owner_v12 import InputOwner
        self.owner = InputOwner(":fake")
        self.lease = Lease()

    def tearDown(self):
        self.owner.close()
        sys.modules.pop("input_owner_v12", None)
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_explicit_keyup_preserves_exact_owner_occurrence(self):
        first = self.owner.call("down", self.lease, "W")
        self.assertEqual(first["event"], "input_admission")
        self.assertEqual(first["keycode"], 38)
        self.assertEqual(first["owner_id"], self.owner.owner_id)
        first_id = first["input_occurrence_id"]
        self.owner.call("up", self.lease, "W")
        explicit = [row for row in self.owner.records
                    if row.get("event") == "owner_explicit_keyup"]
        self.assertEqual(len(explicit), 1)
        self.assertEqual(explicit[0]["input_occurrence_id"], first_id)
        second = self.owner.call("down", self.lease, "W")
        self.assertNotEqual(second["input_occurrence_id"], first_id)
        self.owner.call("up", self.lease, "W")

    def test_cancel_batch_keeps_per_key_occurrence_identity(self):
        first = self.owner.call("down", self.lease, "W")
        second = self.owner.call("down", self.lease, "A")
        self.lease.cancel.set()
        self.assertTrue(self.lease.interrupted.wait(1))
        release = self.lease.interruptions[0]
        self.assertEqual(release["reason"], "cancelled")
        self.assertTrue(release["verified"])
        rows = release["key_release_intervals_ns"]
        self.assertEqual({row["keycode"] for row in rows}, {38, 39})
        self.assertEqual({row["input_occurrence_id"] for row in rows},
                         {first["input_occurrence_id"],
                          second["input_occurrence_id"]})
        self.assertTrue(all(row["owner_id"] == self.owner.owner_id
                            and row["intent_token"] == self.lease.intent_token
                            and row["interval_ns"][0] <= row["interval_ns"][1]
                            and row["interval_ns"][1] <= release["verified_ns"]
                            for row in rows))
        from executor_v13 import Executor
        wrapped = object.__new__(Executor)._release_event(
            "program-cancelled",
            {"intent_token": self.lease.intent_token, "record": release})
        self.assertEqual(wrapped["event"], "input_released")
        self.assertEqual(wrapped["owner_release"]["key_release_intervals_ns"], rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
