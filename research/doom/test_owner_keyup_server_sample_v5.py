"""Fake-Xlib integration probe for the opt-in V15 per-key keymap sample."""
import importlib
import sys
import threading
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
MODULES = (
    "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
    "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
    "doom_typed_coast_backend_v1", "input_owner_v12",
    "input_transition_owner_v3", "input_transition_owner_v4",
    "input_transition_owner_v5", "input_owner_v11",
    "doom_typed_release_backend_v1", "doom_typed_release_backend_v2",
    "doom_owner_thread_release_batch_backend_v1",
    "doom_owner_thread_release_batch_backend_v2",
)


def run_fake_batch(backend_module, *, fail_query=False, sticky_key=None):
    fail_query = [fail_query] if type(fail_query) is bool else fail_query
    trace = []
    displays = []

    class FakeDisplay:
        def __init__(self):
            self.down = set()
            self.root = types.SimpleNamespace(
                query_pointer=lambda: types.SimpleNamespace(
                    mask=0, root_x=0, root_y=0))
            displays.append(self)

        def get_input_focus(self):
            return types.SimpleNamespace(focus=41)

        def keysym_to_keycode(self, key):
            return {"a": 38, "b": 56}.get(key, 0)

        def screen(self):
            return types.SimpleNamespace(root=self.root)

        def query_keymap(self):
            trace.append(("query_keymap", sorted(self.down)))
            if fail_query[0]:
                fail_query[0] = False
                raise OSError("injected fake keymap query failure")
            bitmap = bytearray(32)
            for code in self.down:
                bitmap[code // 8] |= 1 << (code % 8)
            return bytes(bitmap)

        def sync(self):
            trace.append(("sync", sorted(self.down)))

        def close(self):
            pass

    fake_x = types.ModuleType("Xlib.X")
    for name, value in {
        "KeyPress": 2, "KeyRelease": 3, "ButtonRelease": 5,
        "Button1Mask": 256, "AnyPropertyType": 0, "IsViewable": 2,
    }.items():
        setattr(fake_x, name, value)
    xlib = types.ModuleType("Xlib")
    xlib.X = fake_x
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda key: key
    display = types.ModuleType("Xlib.display")
    display.Display = lambda _name: FakeDisplay()
    errors = types.ModuleType("Xlib.error")
    errors.BadWindow = type("BadWindow", (Exception,), {})
    errors.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(d, event, code):
        if event == fake_x.KeyPress:
            d.down.add(code)
            name = "KeyPress"
        elif event == fake_x.KeyRelease:
            name = "KeyRelease"
            if code != sticky_key:
                d.down.discard(code)
        else:
            name = f"Event{event}"
        trace.append((name, code, sorted(d.down)))

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, errors, ext

    exc = types.ModuleType("executor_v3")
    exc.Cancelled = type("Cancelled", (Exception,), {})
    exc.DecisionRequired = type("DecisionRequired", (Exception,), {})

    class UnusedOwner:
        def __init__(self, *_args):
            pass
        def close(self):
            pass
        def call(self, *_args):
            return None

    owner10 = types.ModuleType("input_owner_v10")
    owner10.InputOwner = UnusedOwner

    coast = types.ModuleType("doom_typed_coast_backend_v1")
    class FakeGameFacingBackend:
        def __init__(self, session, _out, emit, _signal_readers):
            self.owner = UnusedOwner()
            self.held = set()
            self.emit = emit
            self.lease = types.SimpleNamespace(
                intent_token="lease-1", deadline=2**62,
                cancel=threading.Event(), expected_focus=41,
                focus_invalid=False, check=lambda: None)

        def execute(self, _step, _cancel, _identifier, _index):
            for key, down in (
                ("a", True), ("b", True), ("a", False), ("b", False)
            ):
                self.raw(key, down)
            return {"executed": True}

        def release_all(self):
            return {"verified": True}

    coast.Backend = FakeGameFacingBackend
    coast.suite = object()

    saved = {name: sys.modules.get(name) for name in MODULES}
    prior_path = list(sys.path)
    try:
        sys.path[:0] = [str(DOOM), str(LIVE)]
        sys.modules.update({
            "Xlib": xlib, "Xlib.X": fake_x, "Xlib.XK": xk,
            "Xlib.display": display, "Xlib.error": errors,
            "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
            "executor_v3": exc, "input_owner_v10": owner10,
            "doom_typed_coast_backend_v1": coast,
        })
        for name in MODULES:
            if name not in {
                "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
                "doom_typed_coast_backend_v1",
            }:
                sys.modules.pop(name, None)

        selected = importlib.import_module(backend_module)
        emitted = []
        backend = selected.Backend(
            types.SimpleNamespace(name=":fake"), None,
            lambda row: emitted.append(dict(row)), {})
        trace.clear()  # exclude empty construction-owner startup/cleanup
        cleanup_error = None
        try:
            backend.execute({}, None, "program-1", 0)
        finally:
            try:
                backend.owner.close()
            except Exception as error:
                cleanup_error = type(error).__name__
        return {
            "trace": list(trace),
            "release_rows": [
                row for row in emitted
                if row.get("event") == "input_release_transition"
            ],
            "cleanup_error": cleanup_error,
        }
    finally:
        sys.path[:] = prior_path
        for name, old in saved.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class SelectedV15PerKeySampleTests(unittest.TestCase):
    def test_v1_baseline_samples_keymap_only_after_release_batch(self):
        result = run_fake_batch("doom_owner_thread_release_batch_backend_v1")
        trace = result["trace"]
        releases = [i for i, row in enumerate(trace) if row[0] == "KeyRelease"]
        samples = [i for i, row in enumerate(trace) if row[0] == "query_keymap"]
        self.assertEqual(len(releases), 2)
        self.assertEqual(len(samples), 1)
        self.assertGreater(samples[0], releases[-1])
        rows = result["release_rows"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(
            "owner_keymap_sample_available" not in row for row in rows))

    def test_v2_selected_path_samples_after_each_explicit_up(self):
        result = run_fake_batch("doom_owner_thread_release_batch_backend_v2")
        trace = result["trace"]
        releases = [i for i, row in enumerate(trace) if row[0] == "KeyRelease"]
        samples = [i for i, row in enumerate(trace) if row[0] == "query_keymap"]
        self.assertEqual(len(releases), 2)
        self.assertGreater(len(samples), 2)  # two per-edge plus terminal cleanup
        self.assertLess(releases[0], samples[0])
        self.assertLess(samples[0], releases[1])
        self.assertLess(releases[1], samples[1])
        self.assertEqual(trace[samples[0]], ("query_keymap", [56]))
        self.assertEqual(trace[samples[1]], ("query_keymap", []))
        rows = result["release_rows"]
        self.assertEqual([row["key"] for row in rows], ["a", "b"])
        self.assertTrue(all(row["owner_keymap_sample_available"] is True for row in rows))
        self.assertEqual([row["owner_keymap_state_after_release"] for row in rows],
                         ["UP", "UP"])
        self.assertTrue(all(row["owner_transition_verified"] is True for row in rows))
        self.assertTrue(all(
            row["physical_verification_authoritative"] is False for row in rows))
        for row in rows:
            receipt = row["owner_thread_keyup_receipt"]
            self.assertLessEqual(receipt["owner_sync_returned_ns"],
                                 receipt["owner_keymap_sample_started_ns"])
            self.assertLessEqual(receipt["owner_keymap_sample_started_ns"],
                                 receipt["owner_keymap_sample_finished_ns"])
            self.assertLessEqual(receipt["owner_keymap_sample_finished_ns"],
                                 row["release_call_returned_ns"])

    def test_down_sample_blocks_batch_verified_decision(self):
        result = run_fake_batch(
            "doom_owner_thread_release_batch_backend_v2", sticky_key=38)
        rows = result["release_rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["owner_keymap_state_after_release"], "DOWN")
        self.assertFalse(rows[0]["ordinary_release_candidate"])
        self.assertFalse(any(row["owner_transition_verified"] for row in rows))
        self.assertIsNotNone(result["cleanup_error"])

    def test_query_failure_is_explicit_and_blocks_batch_verified_decision(self):
        result = run_fake_batch(
            "doom_owner_thread_release_batch_backend_v2", fail_query=[True])
        rows = result["release_rows"]
        self.assertEqual(len(rows), 2)
        self.assertFalse(rows[0]["owner_keymap_sample_available"])
        self.assertEqual(rows[0]["owner_keymap_sample_error_type"], "OSError")
        self.assertFalse(rows[0]["ordinary_release_candidate"])
        self.assertFalse(any(row["owner_transition_verified"] for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)


