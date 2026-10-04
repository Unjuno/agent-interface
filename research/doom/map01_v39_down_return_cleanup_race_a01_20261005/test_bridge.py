from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "SOURCE"
FIXTURE = SOURCE / "OWNER"
sys.path[:0] = [str(HERE), str(SOURCE / "EXECUTOR")]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def setup_imports():
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
        Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda value: 1)
    xlib.error = types.SimpleNamespace(BadWindow=Exception, BadDrawable=Exception)
    xlib.display = types.SimpleNamespace(Display=lambda name: None)
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = types.SimpleNamespace(fake_input=lambda *a, **k: None)
    sys.modules.update({"Xlib": xlib, "Xlib.ext": ext, "Xlib.ext.xtest": ext.xtest})
    pil = types.ModuleType("PIL")
    pil.ImageGrab = types.SimpleNamespace(grab=lambda **kwargs: None)
    sys.modules["PIL"] = pil
    base = types.ModuleType("doom_typed_release_backend_v1")
    class Previous:
        def close(self):
            self.owner.close()
    base.Backend, base.suite = Previous, object()
    sys.modules["doom_typed_release_backend_v1"] = base


setup_imports()
owner_source = load("input_owner_v13", FIXTURE / "input_owner_v13.py")
from bridge import Backend


def harness():
    source = load("v13_bridge_fixture", FIXTURE / "test_input_owner_v12.py")
    owner = owner_source
    h = source.Harness(owner)
    owner.XK.string_to_keysym = lambda value: 1 if value == "F8" else 0
    h.d.keysym_to_keycode = lambda sym: 74 if sym == 1 else 0
    return source, h


class CleanupForwardingTests(unittest.TestCase):
    def test_async_cancel_cleanup_becomes_contextual_release_once(self):
        source, h = harness()
        lease = source.Lease(intent="intent-v39-a02")
        b = object.__new__(Backend)
        b.owner, b.lease, b.held = h.owner, lease, set()
        b._input_event_context = ("cover-a02", 3)
        b._owner_records_cursor = 0
        b._active_actuations, b._actuation_context = {}, {}
        b.events, b.emit = [], None
        b.emit = b.events.append
        try:
            b.raw("F8", True)
            lease.cancel.set()
            for _ in range(1000):
                if any(r.get("event") == "owner_release" for r in h.owner.records):
                    break
                import time; time.sleep(.001)
            b.raw("F8", False)
            b.drain_owner_records()
            releases = [r for r in b.events if r.get("event") == "input_release_measurement"]
            self.assertEqual(len(releases), 1)
            row = releases[0]
            self.assertEqual((row["id"], row["step"], row["intent_token"]),
                             ("cover-a02", 3, "intent-v39-a02"))
            m = row["physical_key_measurement"]
            self.assertEqual(m["classification"], "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(m["actuation_id"], b.events[0]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(m["adapter_edge"]["edge"], "up")
            self.assertFalse(m["adapter_edge"]["grants_input_authority"])
            self.assertEqual(row["owner_cleanup_record"]["verified"], True)
            self.assertEqual(h.d.physical, set())
            self.assertFalse(any(r.get("event") == "input_release_measurement"
                                 and r.get("physical_key_measurement", {}).get("classification") == "NOOP_ALREADY_UP"
                                 for r in b.events))
            b.drain_owner_records()
            self.assertEqual(len([r for r in b.events if r.get("event") == "input_release_measurement"]), 1)
        finally:
            h.close()

    def test_cleanup_published_during_down_call_keeps_admission_context(self):
        aid = "owner:g1:F8"
        cleanup = {"event": "owner_release", "verified": True,
                   "per_key_release_measurements": [{
                       "key": "F8", "actuation_id": aid,
                       "classification": "CONFIRMED_PHYSICAL_UP",
                       "bracket": {"key": "F8", "owner_id": "owner",
                                   "intent_token": "tok",
                                   "physical_up_interval": [10, 11]}}]}

        class RacingOwner:
            owner_id = "owner"

            def __init__(self):
                self.records = []

            def call(self, operation, lease, key):
                if operation == "down":
                    # Deterministically model cancellation publication in the
                    # return-to-caller window of the down operation.
                    self.records.append(cleanup)
                    return {"event": "input_admission", "owner_id": "owner",
                            "intent_token": "tok", "key": key,
                            "physical_key_measurement": {
                                "actuation_id": aid, "classification": "ADMITTED"}}
                return {"event": "input_release_measurement", "owner_id": "owner",
                        "intent_token": "tok", "key": key,
                        "physical_key_measurement": {
                            "actuation_id": None, "classification": "NOOP_ALREADY_UP"}}

        b = object.__new__(Backend)
        b.owner, b.lease, b.held = RacingOwner(), types.SimpleNamespace(intent_token="tok"), set()
        b._input_event_context = ("run-race", 2)
        b._owner_records_cursor = 0
        b._active_actuations, b._actuation_context = {}, {}
        b.events, b.emit = [], None
        b.emit = b.events.append

        b.raw("F8", True)
        b.raw("F8", False)

        self.assertEqual([row["event"] for row in b.events],
                         ["input_admission", "input_release_measurement"])
        release = b.events[1]
        self.assertEqual((release["id"], release["step"], release["intent_token"]),
                         ("run-race", 2, "tok"))
        self.assertEqual(release["physical_key_measurement"]["actuation_id"], aid)
        self.assertEqual(release["physical_key_measurement"]["classification"],
                         "CONFIRMED_PHYSICAL_UP")
        self.assertEqual(release["owner_cleanup_record"], cleanup)
        self.assertFalse(release["grants_input_authority"])

    def test_unmapped_cleanup_is_retained_without_projected_authority(self):
        b = object.__new__(Backend)
        b._actuation_context, b._active_actuations = {}, {}
        b.events, b.emit = [], None
        b.emit = b.events.append
        record = {"event": "owner_release", "verified": True,
                  "per_key_release_measurements": [{"key": "F8", "actuation_id": "unknown"}]}
        b._emit_owner_cleanup(record)
        self.assertEqual(b.events[0]["event"], "input_cleanup_unscoped")
        self.assertFalse(b.events[0]["grants_input_authority"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
