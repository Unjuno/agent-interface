import unittest
from .adapter import SCHEMA
from .native_result import NativeResultError, motor_state_from_native_result


def raw():
    return {
        "result_id": "r1",
        "target": {"surface_id": "surface-1", "frame": "window-client"},
        "focus_confirmed": True,
        "ack_id": "ack-1",
        "observation": {"observation_id": "obs-1", "observed_pointer": {"x": 1, "y": 2}},
        "execution": {"transport_passed": True},
        "release": {"final_release_verified": True},
    }


class NativeResultTests(unittest.TestCase):
    def test_complete_result_maps_to_valid_state(self):
        row = motor_state_from_native_result(raw())
        self.assertEqual(row["schema"], SCHEMA)
        self.assertEqual(row["uncertainty"], "NONE")
        self.assertEqual(row["input_ack"], {"id": "ack-1", "status": "ACKED"})
        self.assertEqual(row["release"]["status"], "VERIFIED_EMPTY")

    def test_missing_observation_is_uncertain_and_valid(self):
        value = raw()
        value["observation"] = None
        row = motor_state_from_native_result(value)
        self.assertEqual(row["uncertainty"], "OS_UNCONFIRMED")

    def test_transport_failure_cannot_emit_none(self):
        value = raw()
        value["execution"] = {"transport_passed": False}
        row = motor_state_from_native_result(value)
        self.assertNotEqual(row["uncertainty"], "NONE")

    def test_missing_pointer_cannot_emit_none(self):
        value = raw()
        value["observation"] = {"observation_id": "obs-1"}
        row = motor_state_from_native_result(value)
        self.assertNotEqual(row["uncertainty"], "NONE")

    def test_empty_pointer_cannot_emit_none(self):
        value = raw()
        value["observation"]["observed_pointer"] = {}
        row = motor_state_from_native_result(value)
        self.assertNotEqual(row["uncertainty"], "NONE")

    def test_missing_ack_cannot_emit_acked_or_none(self):
        value = raw()
        del value["ack_id"]
        row = motor_state_from_native_result(value)
        self.assertEqual(row["input_ack"]["status"], "UNKNOWN")
        self.assertNotEqual(row["uncertainty"], "NONE")

    def test_release_error_precedes_verified_flag(self):
        value = raw()
        value["release"] = {"error": "release_failed", "final_release_verified": True}
        self.assertEqual(motor_state_from_native_result(value)["release"]["status"], "FAILED")

    def test_bad_revision_is_rejected(self):
        value = raw()
        value["binding_revision"] = "1"
        with self.assertRaises(NativeResultError):
            motor_state_from_native_result(value)

    def test_missing_surface_is_rejected(self):
        value = raw()
        value["target"] = {"frame": "window-client"}
        with self.assertRaises(NativeResultError):
            motor_state_from_native_result(value)

    def test_authority_promotion_is_rejected(self):
        value = raw()
        value["extends_lease"] = True
        with self.assertRaises(NativeResultError):
            motor_state_from_native_result(value)

    def test_raw_input_is_not_mutated(self):
        value = raw()
        before = repr(value)
        motor_state_from_native_result(value)
        self.assertEqual(repr(value), before)


if __name__ == "__main__":
    unittest.main()
