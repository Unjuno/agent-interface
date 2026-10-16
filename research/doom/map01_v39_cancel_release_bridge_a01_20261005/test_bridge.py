"""Focused fake-display checks for cancellation receipt forwarding."""
from __future__ import annotations

import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM = REPO / "research" / "doom"
BASE_TEST = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CancelReleaseBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_tests = _load("base_v39_bridge_test_for_cleanup", BASE_TEST)
        cls.harness_module = cls.base_tests.load_v12_test_harness()
        cls.owner_v13 = importlib.import_module(
            "map01_v39_cancel_release_bridge_a01_20261005.input_owner_v13")
        cls.backend_module = importlib.import_module(
            "map01_v39_cancel_release_bridge_a01_20261005.bridge")
        cls.Backend = cls.backend_module.Backend

        previous = sys.modules["doom_typed_release_backend_v1"].Backend

        def cancel_after_admission(self, step, cancel, identifier, index):
            self.raw("F8", True)
            cancel.set()
            return None

        previous.execute = cancel_after_admission

    def harness(self):
        return self.harness_module.Harness(self.owner_v13)

    def backend(self, harness, lease, events):
        value = object.__new__(self.Backend)
        value.owner = harness.owner
        value.lease = lease
        value.held = set()
        value._input_event_context = None
        value._active_admissions = {}
        value.emit = events.append
        return value

    def test_cancel_cleanup_emits_matched_per_admission_up_and_clears_held(self):
        harness = self.harness()
        lease = self.harness_module.Lease(intent="intent-cancel-bridge-a01")
        events = []
        backend = self.backend(harness, lease, events)
        try:
            backend.execute({"op": "hold"}, lease.cancel,
                            "cover-cancel-bridge-a01", 7)
            self.assertEqual([row["event"] for row in events],
                             ["input_admission", "input_release_measurement"],
                             msg=repr((harness.owner.records, backend.held,
                                       backend._active_admissions)))
            admission, released = events
            down = admission["physical_key_measurement"]
            up = released["physical_key_measurement"]
            self.assertEqual((admission["id"], admission["step"]),
                             ("cover-cancel-bridge-a01", 7))
            self.assertEqual((released["id"], released["step"]),
                             (admission["id"], admission["step"]))
            self.assertEqual(released["key"], admission["key"])
            self.assertEqual(released["intent_token"], admission["intent_token"])
            self.assertEqual(up["classification"], "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(up["actuation_id"], down["actuation_id"])
            self.assertEqual(up["bracket"]["physical_up_interval"],
                             up["adapter_edge"]["interval"])
            self.assertEqual(up["adapter_edge"]["edge"], "up")
            self.assertEqual(up["adapter_edge"]["actuation_id"], down["actuation_id"])
            self.assertFalse(released["grants_input_authority"])
            self.assertFalse(up["application_consumption_observed"])
            self.assertTrue(released["owner_release"]["verified"])
            self.assertEqual(released["owner_release"]["keys_down"], [])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
            self.assertEqual(backend._active_admissions, {})
        finally:
            harness.close()

    def test_malformed_or_unverified_cleanup_cannot_emit_or_reconcile(self):
        base_measurement = {
            "edge": "up", "key": "F8", "keycode": 74,
            "classification": "CONFIRMED_PHYSICAL_UP",
            "actuation_id": "owner:g1:F8", "identity_status": "RETIRED",
            "release_attempted": True,
            "bracket": {
                "status": "CONFIRMED_PHYSICAL_UP",
                "physical_up_interval": [10, 20], "owner_id": "owner",
                "intent_token": "intent", "key": "F8",
                "grants_input_authority": False,
            },
        }
        base_release = {
            "event": "owner_release", "reason": "cancelled", "verified": True,
            "keys_down": [], "buttons_down": [], "verified_ns": 30,
            "per_key_release_measurements": [base_measurement],
        }
        mutations = []

        wrong_actuation = {**base_release, "per_key_release_measurements": [
            {**base_measurement, "actuation_id": "other:g1:F8"}]}
        mutations.append(wrong_actuation)

        wrong_owner_bracket = {
            **base_measurement,
            "bracket": {**base_measurement["bracket"], "owner_id": "other"},
        }
        mutations.append({**base_release, "per_key_release_measurements": [wrong_owner_bracket]})
        mutations.append({**base_release, "per_key_release_measurements": []})
        mutations.append({**base_release, "verified": False})
        mutations.append({**base_release, "per_key_release_measurements": [
            base_measurement, base_measurement]})

        for release in mutations:
            with self.subTest(release=release):
                owner = type("Owner", (), {})()
                owner.owner_id = "owner"
                owner.records = [release]
                owner.call = lambda operation: {
                    "owner_id": "owner", "owned_keycodes": [], "owned_buttons": []}
                backend = object.__new__(self.Backend)
                backend.owner = owner
                backend.held = {"F8"}
                backend.emit = lambda row: self.fail("invalid cleanup emitted")
                backend._active_admissions = {
                    "F8": {
                        "key": "F8", "owner_id": "owner",
                        "intent_token": "intent", "actuation_id": "owner:g1:F8",
                        "id": "program", "step": 0,
                    }
                }
                backend._forward_verified_cleanup(0)
                self.assertEqual(backend.held, {"F8"})
                self.assertIn("F8", backend._active_admissions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
