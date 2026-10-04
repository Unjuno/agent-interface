"""Regressions for source-bound HUD state feedback in V39 planner context."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v39 as controller


WAD_SHA256 = "a" * 64
BINDING = {"focus": 11, "surface": 11, "geometry": [0, 0, 640, 480]}


def observation(sequence, capture_ns):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": BINDING,
            "frame_rgb_sha256": f"{sequence:064x}",
            "id": "program-1", "step": sequence}


def typed_observation(sequence, capture_ns, health, ammo, *, binding=BINDING):
    signals = {}
    for name, value in (("health", health), ("ammo", ammo)):
        signals[name] = {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding,
            "wad_sha256": WAD_SHA256,
        }
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns,
            "frame_rgb_sha256": f"{sequence:064x}", "signals": signals,
            "id": "program-1", "step": sequence}


class FakePlanner:
    def __init__(self):
        self.calls = []

    def begin_turn(self, prompt, **params):
        self.calls.append((prompt, params))
        return "handle"


class V39TypedStateFeedbackTests(unittest.TestCase):
    def test_feedback_reports_exact_health_and_ammo_deltas_for_matching_frames(self):
        before = observation(83, 100)
        after = observation(89, 200)
        typed = [typed_observation(83, 100, 97, 48),
                 typed_observation(89, 200, 91, 45)]

        result = controller.action_state_feedback(before, after, typed)

        self.assertEqual(result, {
            "status": "observed",
            "from_sequence": 83,
            "to_sequence": 89,
            "signals": {
                "health": {"before": 97, "after": 91, "delta": -6},
                "ammo": {"before": 48, "after": 45, "delta": -3},
            },
            "scope": "public HUD transition observed after action; not causal or beneficial evidence",
        })

    def test_unchanged_ammo_after_fire_is_reported_as_zero_resource_delta(self):
        result = controller.action_state_feedback(
            observation(83, 100), observation(89, 200),
            [typed_observation(83, 100, 91, 45),
             typed_observation(89, 200, 91, 45)])

        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["signals"]["ammo"],
                         {"before": 45, "after": 45, "delta": 0})

    def test_feedback_refuses_typed_frame_with_mismatched_capture_time(self):
        before = observation(83, 100)
        after = observation(89, 200)
        typed = [typed_observation(83, 100, 91, 45),
                 typed_observation(89, 199, 91, 44)]

        result = controller.action_state_feedback(before, after, typed)

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_typed_frame_with_mismatched_rgb_hash(self):
        before = observation(83, 100)
        after = observation(89, 200)
        mismatched = typed_observation(89, 200, 91, 44)
        mismatched["frame_rgb_sha256"] = "b" * 64

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), mismatched])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_typed_frame_from_another_program(self):
        before = observation(83, 100)
        after = observation(89, 200)
        wrong_program = typed_observation(89, 200, 91, 44)
        wrong_program["id"] = "other-program"

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), wrong_program])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_out_of_domain_typed_hud_values(self):
        before = observation(83, 100)
        after = observation(89, 200)

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45),
                            typed_observation(89, 200, 201, 45)])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_signal_unavailable")

    def test_feedback_refuses_wad_identity_change_between_frames(self):
        before = observation(83, 100)
        after = observation(89, 200)
        changed_wad = typed_observation(89, 200, 91, 44)
        changed_wad["signals"]["ammo"]["wad_sha256"] = "b" * 64

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), changed_wad])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_signal_binding_mismatch")

    def test_feedback_refuses_nonforward_capture_order(self):
        result = controller.action_state_feedback(
            observation(89, 200), observation(83, 100),
            [typed_observation(83, 100, 91, 45),
             typed_observation(89, 200, 91, 44)])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_order_invalid")

    def test_planner_prompt_receives_prior_state_delta_as_observation_only(self):
        planner = FakePlanner()
        feedback = [{"action": "fire", "extent": "pulse",
                     "viewport_result": "visible_change",
                     "state_feedback": {"status": "observed", "signals": {
                         "health": {"before": 91, "after": 91, "delta": 0},
                         "ammo": {"before": 45, "after": 45, "delta": 0}}}}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sheet.png"
            image.write_bytes(b"fixture")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                controller.begin_model_turn(
                    planner, root, image, [], 91, 45, None,
                    {"type": "object"}, prior_state_feedback=feedback)

        prompt, _ = planner.calls[0]
        self.assertIn('"ammo":{"before":45,"after":45,"delta":0}', prompt)
        self.assertIn("not causal or beneficial evidence", prompt)


if __name__ == "__main__":
    unittest.main()
