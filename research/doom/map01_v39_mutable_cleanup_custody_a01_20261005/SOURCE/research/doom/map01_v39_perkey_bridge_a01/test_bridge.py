"""Construction integration of the v39 typed backend and InputOwner v12."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[3]
DOOM = WORKTREE / "research" / "doom"
LIVE_CONTROL = WORKTREE / "research" / "live_control"
OBSERVATION_TILES = WORKTREE / "research" / "observation_tiles"
OBSERVATION_GATING = WORKTREE / "research" / "observation_gating"
V12 = DOOM / "map01_attack_onset_phase_allocation_02_v1" / "dependencies" / "v12"
sys.path.insert(0, str(WORKTREE))
sys.path.insert(0, str(OBSERVATION_TILES))
sys.path.insert(0, str(OBSERVATION_GATING))
sys.path.insert(0, str(DOOM))
sys.path.insert(0, str(LIVE_CONTROL))
sys.path.insert(0, str(V12))


def install_import_stubs():
    """Stub only optional GUI bindings; the test harness supplies the fake display."""
    xlib = types.ModuleType("Xlib")
    x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                              Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xk = types.SimpleNamespace(string_to_keysym=lambda value: 1)
    error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                  BadDrawable=type("BadDrawable", (Exception,), {}))
    display = types.ModuleType("Xlib.display")
    display.Display = lambda name: None
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = lambda *args, **kwargs: None
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = xtest
    xlib.X, xlib.XK, xlib.error, xlib.display = x, xk, error, display
    sys.modules.update({"Xlib": xlib, "Xlib.display": display,
                        "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
    pil = types.ModuleType("PIL")
    image_grab = types.SimpleNamespace(grab=lambda **kwargs: None)
    pil.ImageGrab = image_grab
    sys.modules["PIL"] = pil


install_import_stubs()

# The raw() seam under test does not invoke the capture superclass. Keep its
# heavyweight screenshot/X11 import graph out of this component construction.
release_backend = types.ModuleType("doom_typed_release_backend_v1")
release_backend.Backend = type("PreviousBackend", (), {})
release_backend.suite = object()
sys.modules["doom_typed_release_backend_v1"] = release_backend

from map01_v39_perkey_bridge_a01.bridge import Backend


def load_v12_test_harness():
    path = V12 / "test_input_owner_v12.py"
    spec = importlib.util.spec_from_file_location("input_owner_v12_harness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.owner_module = module.load(
        "input_owner_v12_for_bridge", V12 / "input_owner_v12.py")
    return module


def run_bridge():
    owner_harness_module = load_v12_test_harness()
    harness = owner_harness_module.Harness(owner_harness_module.owner_module)
    backend = object.__new__(Backend)
    backend.owner = harness.owner
    backend.lease = owner_harness_module.Lease(intent="intent-v39-a01")
    backend.held = set()
    backend._input_event_context = ("cover-7", 2)
    backend.events = []
    backend.emit = backend.events.append
    try:
        backend.raw("F8", True)
        backend.raw("F8", False)
        return {"events": backend.events,
                "fake_physical_keys_after_up": sorted(harness.d.physical),
                "backend_held_after_up": sorted(backend.held)}
    finally:
        harness.close()


class PerKeyBridgeConstructionTests(unittest.TestCase):
    def test_backend_emits_same_intent_per_key_verified_up_edge(self):
        result = run_bridge()
        events = result["events"]
        self.assertEqual([row["event"] for row in events],
                         ["input_admission", "input_release_measurement"])
        down, up = events
        self.assertEqual((down["id"], down["step"], down["intent_token"]),
                         ("cover-7", 2, "intent-v39-a01"))
        self.assertEqual((up["id"], up["step"], up["intent_token"]),
                         ("cover-7", 2, "intent-v39-a01"))

        down_measurement = down["physical_key_measurement"]
        up_measurement = up["physical_key_measurement"]
        self.assertEqual(down_measurement["classification"], "CONFIRMED_PHYSICAL_DOWN")
        self.assertEqual(up_measurement["classification"], "CONFIRMED_PHYSICAL_UP")
        self.assertEqual(up_measurement["identity_status"], "RETIRED")
        self.assertEqual(up_measurement["actuation_id"], down_measurement["actuation_id"])
        edge = up_measurement["adapter_edge"]
        self.assertEqual(edge["edge"], "up")
        self.assertEqual(edge["status"], "CONFIRMED_PHYSICAL_UP")
        self.assertEqual(edge["intent_token"], "intent-v39-a01")
        self.assertEqual(edge["key"], "F8")
        self.assertEqual(edge["actuation_id"], down_measurement["actuation_id"])
        self.assertIsInstance(edge["interval"], list)
        self.assertEqual(len(edge["interval"]), 2)
        self.assertLessEqual(edge["interval"][0], edge["interval"][1])
        self.assertFalse(edge["grants_input_authority"])
        self.assertEqual(result["fake_physical_keys_after_up"], [])
        self.assertEqual(result["backend_held_after_up"], [])

    def test_missing_program_context_refuses_before_owner_call(self):
        harness_module = load_v12_test_harness()
        harness = harness_module.Harness(harness_module.owner_module)
        backend = object.__new__(Backend)
        backend.owner = harness.owner
        backend.lease = harness_module.Lease(intent="intent-v39-a01")
        backend.held = set()
        backend._input_event_context = None
        backend.events = []
        backend.emit = backend.events.append
        calls = []
        real_call = backend.owner.call
        def track_call(*args, **kwargs):
            calls.append(args)
            return real_call(*args, **kwargs)
        backend.owner.call = track_call
        try:
            with self.assertRaisesRegex(RuntimeError, "outside program/step"):
                backend.raw("F8", True)
            self.assertEqual(calls, [])
            self.assertEqual(backend.events, [])
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
