import unittest

from contract import (
    OFFICE_FLOOR, ContractError, admit_program, capability_manifest,
    office_readiness, required_capabilities, validate_program,
)


def full_manifest(os_name="linux", backend="x11"):
    return capability_manifest(
        f"{os_name}-{backend}", os_name, backend, OFFICE_FLOOR,
        frames=("screen_physical_px", "screen_logical", "window_client"),
    )


def sample_program():
    return {
        "schema": "agent-interface/program-v0",
        "program_id": "p1",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "authority": {"lease_id": "lease-1", "expires_at_ns": 2_000_000},
        "ops": [
            {"op": "focus", "target": "editor"},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 500},
            {"op": "verify", "predicate": "document_saved"},
            {"op": "release_all"},
        ],
        "terminal": {"release_all_required": True},
    }


class ContractTests(unittest.TestCase):
    def test_same_semantics_admit_on_three_full_profiles(self):
        program = sample_program()
        for os_name, backend in [("linux", "x11"), ("windows", "win32"), ("macos", "quartz")]:
            result = admit_program(
                program, full_manifest(os_name, backend), now_ns=1_000_000,
                current_observation_seq=7, current_binding_revision=3,
            )
            self.assertTrue(result.accepted, (os_name, result))

    def test_realistic_unimplemented_profiles_are_representable_but_not_ready(self):
        for os_name, backend in [("linux", "wayland"), ("windows", "native"), ("macos", "native")]:
            manifest = capability_manifest(
                f"{os_name}-{backend}", os_name, backend, [], unknown=OFFICE_FLOOR,
                frames=("screen_logical",),
            )
            status = office_readiness(manifest)
            self.assertFalse(status["ready"])
            self.assertEqual(set(status["blocking_capabilities"]), set(OFFICE_FLOOR))

    def test_permission_is_not_misreported_as_support(self):
        supported = set(OFFICE_FLOOR) - {"capture.frame"}
        manifest = capability_manifest(
            "macos-quartz", "macos", "quartz", supported,
            permission_required={"capture.frame"}, frames=("screen_logical", "window_client"),
            permissions=("screen-recording", "accessibility"),
        )
        self.assertFalse(office_readiness(manifest)["ready"])

    def test_stale_observation_fails_closed(self):
        result = admit_program(
            sample_program(), full_manifest(), now_ns=1_000_000,
            current_observation_seq=8, current_binding_revision=3,
        )
        self.assertEqual(result.error, "STALE_OBSERVATION")

    def test_stale_binding_fails_closed(self):
        result = admit_program(
            sample_program(), full_manifest(), now_ns=1_000_000,
            current_observation_seq=7, current_binding_revision=4,
        )
        self.assertEqual(result.error, "STALE_BINDING")

    def test_expired_lease_fails_closed(self):
        result = admit_program(
            sample_program(), full_manifest(), now_ns=2_000_001,
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(result.error, "LEASE_EXPIRED")

    def test_missing_capability_fails_closed(self):
        supported = set(OFFICE_FLOOR) - {"window.focus"}
        manifest = capability_manifest("linux-x11-lite", "linux", "x11", supported)
        result = admit_program(
            sample_program(), manifest, now_ns=1_000_000,
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(result.error, "UNSUPPORTED_CAPABILITY")

    def test_coordinate_frame_is_backend_capability(self):
        program = sample_program()
        program["ops"].insert(1, {"op": "pointer_move", "frame": "window_client", "x": 10, "y": 20})
        manifest = capability_manifest(
            "linux-x11-screen-only", "linux", "x11", OFFICE_FLOOR,
            frames=("screen_physical_px",),
        )
        result = admit_program(
            program, manifest, now_ns=1_000_000,
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(result.error, "COORDINATE_UNSUPPORTED")

    def test_unbalanced_key_state_rejected(self):
        program = sample_program()
        program["ops"] = [
            {"op": "key_state", "key": "CTRL", "down": True},
            {"op": "release_all"},
            {"op": "key_state", "key": "CTRL", "down": False},
        ]
        with self.assertRaises(ContractError):
            validate_program(program)

    def test_release_all_required(self):
        program = sample_program()
        program["ops"] = program["ops"][:-1]
        with self.assertRaises(ContractError):
            validate_program(program)

    def test_release_all_must_be_final(self):
        program = sample_program()
        program["ops"] = [{"op": "release_all"}, {"op": "focus", "target": "editor"}]
        with self.assertRaises(ContractError):
            validate_program(program)

    def test_release_all_must_be_unique(self):
        program = sample_program()
        program["ops"].insert(-1, {"op": "release_all"})
        with self.assertRaises(ContractError):
            validate_program(program)

    def test_required_capabilities_explicit(self):
        required = set(required_capabilities(sample_program()))
        self.assertTrue({"window.focus", "input.keyboard", "event.feedback", "clock.monotonic", "input.release_all"} <= required)


if __name__ == "__main__":
    unittest.main()
