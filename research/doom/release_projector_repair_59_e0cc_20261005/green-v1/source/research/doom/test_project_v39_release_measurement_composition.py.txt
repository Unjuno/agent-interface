"""Real V12/V4/batch producer -> offline projector against synthetic Xlib.

The ancestor backend initializer is inert; raw dispatch and publication are real.
This does not run Session, V39, the typed executor, or a game.
"""
import copy
import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

LIVE = Path(__file__).resolve().parents[1] / "live_control"
sys.path.insert(0, str(LIVE))
from test_input_owner_v12_explicit_up_cancel import FakeDisplay, Lease
from project_v39_release_measurement_v1 import project


class ProducerProjectionTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDisplay()
        x = types.ModuleType("Xlib.X")
        x.KeyPress, x.KeyRelease, x.ButtonRelease = 2, 3, 5
        x.Button1Mask, x.AnyPropertyType = 256, 0
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = ord
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: self.fake
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            self.fake.trace.append(("key_event", event, code))
            if event == x.KeyPress:
                self.fake.down.add(code)
            elif event == x.KeyRelease:
                self.fake.keyrelease_attempts += 1
                if self.fake.drop_keyreleases:
                    self.fake.drop_keyreleases -= 1
                else:
                    self.fake.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib = types.ModuleType("Xlib")
        xlib.X, xlib.XK, xlib.display, xlib.error, xlib.ext = x, xk, display, error, ext

        class InertAncestor:
            def __init__(backend, session, out, emit, signal_readers):
                backend.owner = types.SimpleNamespace(close=lambda: None)
                backend.emit, backend.held = emit, set()

        ancestor = types.ModuleType("doom_typed_release_backend_v2")
        ancestor.Backend, ancestor.suite = InertAncestor, None
        modules = {"Xlib": xlib, "Xlib.X": x, "Xlib.XK": xk,
                   "Xlib.display": display, "Xlib.error": error,
                   "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
                   "doom_typed_release_backend_v2": ancestor}
        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("input_owner_v10", "input_owner_v12", "input_transition_owner_v3",
                     "input_transition_owner_v4", "doom_owner_thread_release_batch_backend_v1"):
            sys.modules.pop(name, None)
        backend_class = importlib.import_module("doom_owner_thread_release_batch_backend_v1").Backend
        self.events = []
        self.backend = backend_class(types.SimpleNamespace(name=":fake"), None, self.events.append, {})
        self.addCleanup(self.close_owner)
        self.lease = Lease()
        self.backend.lease = self.lease
        self.backend._input_event_context = ("program", 0)
        self.backend._release_batch.context = {
            "identifier": "program", "step": 0, "rows": [], "pending_ups": []}

    def close_owner(self):
        owner = self.backend.owner._inner
        self.backend.owner.close()
        self.assertTrue(owner.stopped.wait(1), "fake owner thread did not stop")
        self.assertFalse(owner.thread.is_alive())
        self.assertEqual(self.fake.down, set())

    def run_batch(self, *, retry=False, cancel=False, cross_step=False):
        for key in ("W", "A"):
            self.backend.raw(key, True)
        self.fake.drop_keyreleases = int(retry)
        if cancel:
            self.fake.on_sync = self.lease.cancel.set
        if cross_step:
            self.backend._input_event_context = ("program", 1)
            self.backend._release_batch.context["step"] = 1
        for key in ("A", "W"):
            self.backend.raw(key, False)
        result = project(self.events)
        print(json.dumps({"case": self.id(), "events": self.events, "projection": result,
                          "fake_trace": self.fake.trace}, sort_keys=True), flush=True)
        self.assertEqual(len(self.events), 4)
        self.assertTrue(all("operation" not in row for row in self.events[:2]))
        self.assertTrue(all("owner_sample_after_batch_available" not in row
                            for row in self.events[2:]))
        return result

    def test_actual_two_key_batch_projects_without_rewriting_emitted_rows(self):
        result = self.run_batch()
        self.assertTrue(result["measurement_ready"])
        self.assertEqual([row["key"] for row in result["rows"]], ["A", "W"])
        self.assertTrue(all(row["application_consumption"] == "unobserved" for row in result["rows"]))

    def test_actual_retry_projects_both_keys(self):
        result = self.run_batch(retry=True)
        self.assertEqual(self.events[2]["owner_thread_keyup_receipt"]["server_keyup_attempt_count"], 2)
        self.assertTrue(result["measurement_ready"])
        self.assertEqual(len(result["rows"]), 2)

    def test_actual_cancelled_batch_remains_unready(self):
        self.assertEqual(self.run_batch(cancel=True), {"measurement_ready": False, "rows": []})

    def test_duplicate_actual_release_cannot_cover_the_other_key(self):
        self.run_batch()
        altered = copy.deepcopy(self.events)
        altered[3] = copy.deepcopy(altered[2])
        altered[3]["release_batch_position"] = 1
        self.assertEqual(project(altered), {"measurement_ready": False, "rows": []})

    def test_cross_step_holds_remain_outside_same_step_projection(self):
        self.assertEqual(self.run_batch(cross_step=True), {"measurement_ready": False, "rows": []})


if __name__ == "__main__":
    unittest.main()
