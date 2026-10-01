"""Composition tests for route selection and the frozen task lifecycle."""

import unittest

from adaptive_route import RouteStop
from arm_coordinator import ArmCoordinator


def source(sequence, layout):
    width = 1280 if layout == "A" else 1216
    return {"sequence": sequence, "delivery_id": f"delivery:{sequence}",
            "pointer_binding": {"surface": 91,
                                "geometry": [0, 24, width, 760]}}


def candidate():
    return {"op": "target_reference", "point_space": "source_observation_pixels",
            "points": [{"x": 150, "y": 220}, {"x": 640, "y": 410}],
            "motion_model": "surface_origin_translation",
            "confidence_basis": "visually_unambiguous"}


def palette_slots():
    return [{"row": 0, "column": 0, "point": [150, 220]},
            {"row": 0, "column": 1, "point": [196, 220]}]


class ArmCoordinatorTests(unittest.TestCase):
    def test_all_arms_compose_route_schedule_and_score_reset_barriers(self):
        expected_calls = {"plain": 6, "ephemeral": 6, "persistent": 2}
        expected_routes = {
            "plain": ["cold"] * 6,
            "ephemeral": ["cold"] * 6,
            "persistent": ["cold", "reuse", "reuse", "repair", "reuse", "reuse"],
        }
        for arm in ("plain", "ephemeral", "persistent"):
            with self.subTest(arm=arm):
                coordinator = ArmCoordinator(arm)
                actual_model_calls = []
                for sequence in range(1, 7):
                    resolved = coordinator.resolve(
                        source(sequence, "A" if sequence <= 3 else "B"),
                        1280 if sequence <= 3 else 1216, 760, palette_slots(),
                        lambda _obs: actual_model_calls.append(sequence) or candidate())
                    self.assertEqual(resolved["task"].task_id,
                                     ["A1", "A2", "A3", "B1", "B2", "B3"][sequence - 1])
                    coordinator.score(True)
                    coordinator.reset(True)
                    coordinator.advance()
                self.assertEqual(sum(row["model_calls"]
                                     for row in coordinator.task_records), expected_calls[arm])
                self.assertEqual([row["route"] for row in coordinator.task_records],
                                 expected_routes[arm])
                self.assertTrue(all(row["old_reference_pointer_admissions"] == 0
                                    for row in coordinator.task_records))
                self.assertEqual(len(actual_model_calls), expected_calls[arm])
                self.assertEqual(coordinator.lifecycle.phase, "complete")

    def test_route_cannot_advance_lifecycle_before_score_and_reset(self):
        coordinator = ArmCoordinator("plain")
        with self.assertRaisesRegex(ValueError, "requires one resolved task"):
            coordinator.score(True)
        coordinator.resolve(source(1, "A"), 1280, 760, palette_slots(),
                            lambda _obs: candidate())
        with self.assertRaisesRegex(ValueError, "one unresolved ready task"):
            coordinator.resolve(source(2, "A"), 1280, 760, palette_slots(),
                                lambda _obs: candidate())
        coordinator.score(True)
        with self.assertRaisesRegex(ValueError, "one unresolved ready task"):
            coordinator.resolve(source(2, "A"), 1280, 760, palette_slots(),
                                lambda _obs: candidate())
        coordinator.reset(True)
        coordinator.advance()
        self.assertEqual(coordinator.resolve(source(2, "A"), 1280, 760,
                         palette_slots(),
                         lambda _obs: candidate())["task"].task_id, "A2")

    def test_model_or_validation_failure_consumes_attempt_without_retry(self):
        coordinator = ArmCoordinator("plain")
        calls = []

        def invalid_model(_obs):
            calls.append("dispatched")
            return {"malformed": True}

        with self.assertRaisesRegex(RouteStop, "invalid model target output"):
            coordinator.resolve(source(1, "A"), 1280, 760,
                                palette_slots(), invalid_model)
        with self.assertRaisesRegex(ValueError, "one unresolved ready task"):
            coordinator.resolve(source(1, "A"), 1280, 760, palette_slots(),
                                lambda _obs: calls.append("retry") or candidate())
        self.assertEqual(calls, ["dispatched"])

    def test_input_locator_is_fresh_and_still_has_no_action_authority(self):
        coordinator = ArmCoordinator("plain")
        coordinator.resolve(source(1, "A"), 1280, 760, palette_slots(),
                            lambda _obs: candidate())
        locator = coordinator.locator_for_input(source(2, "A"), "A")
        self.assertEqual(locator["validated_sequence"], 2)
        self.assertEqual(locator["delivery_id"], "delivery:2")
        self.assertEqual(locator["authority"],
                         "locator only; explicit caller action still required")

    def test_task_specific_locator_does_not_invent_delivery_identity(self):
        coordinator = ArmCoordinator("plain")
        coordinator.resolve(source(1, "A"), 1280, 760, palette_slots(),
                            lambda _obs: candidate())
        missing = source(2, "A")
        del missing["delivery_id"]
        locator = coordinator.locator_for_input(missing, "A")
        self.assertNotIn("delivery_id", locator)
        self.assertEqual(locator["validated_sequence"], 2)

    def test_input_locator_refuses_layout_geometry_change(self):
        coordinator = ArmCoordinator("plain")
        coordinator.resolve(source(1, "A"), 1280, 760, palette_slots(),
                            lambda _obs: candidate())
        changed = source(2, "A")
        changed["pointer_binding"]["geometry"][2] = 1216
        with self.assertRaisesRegex(RouteStop, "refused before input: association_changed"):
            coordinator.locator_for_input(changed, "A")


if __name__ == "__main__":
    unittest.main()
