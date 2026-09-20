from __future__ import annotations

import unittest

from runtime.core_v1.contract import (
    CLOCK_MONOTONIC,
    ContractError,
    DISPLAY_GEOMETRY,
    EVENT_FEEDBACK,
    INPUT_KEYBOARD,
    INPUT_POINTER,
    INPUT_RELEASE_ALL,
    INPUT_SCROLL,
    INPUT_TEXT,
    OFFICE_FLOOR,
    CAPTURE_FRAME,
    WINDOW_FOCUS,
    SCHEMA_PROGRAM,
    admit_program,
    capability_manifest,
    office_readiness,
    required_capabilities,
    validate_program,
)


def program() -> dict:
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": "demo-1",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "authority": {"lease_id": "lease-1", "expires_at_ns": 10_000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "window-1"},
            {"op": "pointer_move", "frame": "window_client", "x": 10, "y": 20},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "pointer_button", "button": "left", "down": False},
            {"op": "text", "text": "hello"},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "scroll", "dx": 0, "dy": -1},
            {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 40, "h": 40},
            {"op": "wait_update", "timeout_ms": 100},
            {"op": "verify", "predicate": "saved"},
            {"op": "release_all"},
        ],
    }


FULL = OFFICE_FLOOR


class ProgramTests(unittest.TestCase):
    def test_unexpanded_repeat_cannot_be_silently_ignored(self):
        request = program()
        request['ops'].insert(-1, {'op': 'key_chord', 'keys': ['Right'], 'repeat': 3})
        with self.assertRaisesRegex(ValueError, 'repeat requires explicit expansion'):
            validate_program(request)

    def test_valid_program(self):
        self.assertEqual(validate_program(program()), program())

    def test_required_capabilities(self):
        required = set(required_capabilities(program()))
        self.assertEqual(required, {
            CAPTURE_FRAME, INPUT_KEYBOARD, INPUT_TEXT, INPUT_POINTER, INPUT_SCROLL,
            INPUT_RELEASE_ALL, WINDOW_FOCUS, DISPLAY_GEOMETRY, CLOCK_MONOTONIC,
            EVENT_FEEDBACK,
        })

    def test_release_all_must_be_final(self):
        value = program(); value["ops"].insert(-1, {"op": "release_all"})
        with self.assertRaises(ContractError): validate_program(value)

    def test_release_all_exactly_once(self):
        value = program(); value["ops"] = value["ops"][:-1]
        with self.assertRaises(ContractError): validate_program(value)

    def test_key_lifecycle(self):
        value = program(); value["ops"] = [
            {"op": "key_state", "key": "A", "down": False},
            {"op": "release_all"},
        ]
        with self.assertRaises(ContractError): validate_program(value)

    def test_unknown_op_rejected(self):
        value = program(); value["ops"] = [{"op": "teleport"}, {"op": "release_all"}]
        with self.assertRaises(ContractError): validate_program(value)


class AdmissionTests(unittest.TestCase):
    def manifest(self, os_name="linux", backend="x11"):
        return capability_manifest("test-backend", os_name, backend, FULL)

    def test_accepts_fresh_valid_program(self):
        result = admit_program(program(), self.manifest(), now_ns=9_000,
            current_observation_seq=7, current_binding_revision=3)
        self.assertTrue(result.accepted); self.assertIsNone(result.error)

    def test_expired_lease(self):
        result = admit_program(program(), self.manifest(), now_ns=10_001,
            current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(result.error, "LEASE_EXPIRED")

    def test_stale_observation(self):
        result = admit_program(program(), self.manifest(), now_ns=9_000,
            current_observation_seq=8, current_binding_revision=3)
        self.assertEqual(result.error, "STALE_OBSERVATION")

    def test_stale_binding(self):
        result = admit_program(program(), self.manifest(), now_ns=9_000,
            current_observation_seq=7, current_binding_revision=4)
        self.assertEqual(result.error, "STALE_BINDING")

    def test_permission_required(self):
        manifest = capability_manifest("mac", "macos", "quartz", FULL - {INPUT_POINTER},
            permission_required={INPUT_POINTER})
        result = admit_program(program(), manifest, now_ns=9_000,
            current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(result.error, "PERMISSION_DENIED")

    def test_unknown_capability_fails_closed(self):
        manifest = capability_manifest("win", "windows", "win32", FULL - {INPUT_TEXT},
            unknown={INPUT_TEXT})
        result = admit_program(program(), manifest, now_ns=9_000,
            current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(result.error, "UNSUPPORTED_CAPABILITY")

    def test_coordinate_frame_mismatch(self):
        manifest = capability_manifest("x", "linux", "x11", FULL,
            frames=("screen_physical_px",))
        result = admit_program(program(), manifest, now_ns=9_000,
            current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(result.error, "COORDINATE_UNSUPPORTED")


class CrossPlatformManifestTests(unittest.TestCase):
    def test_synthetic_linux_windows_macos_same_program(self):
        for os_name, backend in (("linux", "x11"), ("windows", "win32"), ("macos", "quartz")):
            with self.subTest(os=os_name):
                manifest = capability_manifest(f"synthetic-{os_name}", os_name, backend, FULL,
                    frames=("screen_physical_px", "screen_logical", "window_client"))
                self.assertTrue(office_readiness(manifest)["ready"])
                self.assertTrue(admit_program(program(), manifest, now_ns=9_000,
                    current_observation_seq=7, current_binding_revision=3).accepted)

    def test_unimplemented_profile_is_not_ready(self):
        manifest = capability_manifest("future-mac", "macos", "quartz", (), unknown=FULL)
        readiness = office_readiness(manifest)
        self.assertFalse(readiness["ready"])
        self.assertEqual(set(readiness["blocking_capabilities"]), set(FULL))

    def test_manifest_overlap_rejected(self):
        with self.assertRaises(ContractError):
            capability_manifest("bad", "linux", "x11", {INPUT_TEXT}, unknown={INPUT_TEXT})


if __name__ == "__main__":
    unittest.main()
