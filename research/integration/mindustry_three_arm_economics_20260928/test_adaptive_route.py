"""Host construction controls for one-generation acquisition and reuse routes."""

import unittest

from adaptive_route import (RouteStop, TargetBundle, require_current_locator,
                            route_task)


def observation(sequence, geometry=(0, 24, 1280, 760)):
    return {"sequence": sequence, "delivery_id": f"delivery:{sequence}",
            "pointer_binding": {"surface": 91, "geometry": list(geometry)}}


def candidate():
    return {"op": "target_reference", "point_space": "source_observation_pixels",
            "points": [{"x": 150, "y": 220}, {"x": 640, "y": 410}],
            "motion_model": "surface_origin_translation",
            "confidence_basis": "visually_unambiguous"}


def palette_slots():
    return [{"row": 0, "column": 0, "point": [150, 220]},
            {"row": 0, "column": 1, "point": [196, 220]}]


class AdaptiveRouteTests(unittest.TestCase):
    def test_persistent_cold_reuse_repair_reuse_has_exact_two_generations(self):
        calls = []

        def model(obs):
            calls.append(obs["sequence"])
            return candidate()

        cached = None
        plan = [("A1", "A", "cold", observation(1)),
                ("A2", "A", "reuse", observation(2)),
                ("A3", "A", "reuse", observation(3)),
                ("B1", "B", "repair", observation(4, (0, 24, 1216, 760))),
                ("B2", "B", "reuse", observation(5, (0, 24, 1216, 760))),
                ("B3", "B", "reuse", observation(6, (0, 24, 1216, 760)))]
        observed_calls = []
        for task_id, layout, route, source in plan:
            result = route_task(arm="persistent", route=route, task_id=task_id,
                layout=layout, cached=cached, observation=source,
                width=1280, height=760, palette_slots=palette_slots(),
                model_call=model)
            observed_calls.append(result["model_calls"])
            self.assertEqual(result["old_reference_pointer_admissions"], 0)
            if result["cache_update"] is not None:
                cached = result["cache_update"]
        self.assertEqual(observed_calls, [1, 0, 0, 1, 0, 0])
        self.assertEqual(calls, [1, 4])

    def test_stale_reuse_refuses_without_model_call_or_target_input(self):
        first = route_task(arm="persistent", route="cold", task_id="A1", layout="A",
            cached=None, observation=observation(1), width=1280, height=760,
            palette_slots=palette_slots(),
            model_call=lambda _obs: candidate())["cache_update"]
        calls = []
        with self.assertRaisesRegex(RouteStop, "refused before input: association_changed"):
            route_task(arm="persistent", route="reuse", task_id="A2", layout="A",
                cached=first, observation=observation(2, (0, 24, 1216, 760)),
                width=1216, height=760, palette_slots=palette_slots(),
                model_call=lambda obs: calls.append(obs) or candidate())
        self.assertEqual(calls, [])

    def test_repair_requires_stale_old_reference(self):
        first = TargetBundle((150, 220), (640, 410), 91,
                             (0, 24, 1280, 760), "B", 1)
        with self.assertRaisesRegex(RouteStop, "repair requires the prior target to be stale"):
            route_task(arm="persistent", route="repair", task_id="B1", layout="B",
                cached=first, observation=observation(2), width=1280, height=760,
                palette_slots=palette_slots(), model_call=lambda _obs: candidate())

    def test_reference_arms_are_cold_and_ephemeral_does_not_cache(self):
        for arm in ("plain", "ephemeral"):
            with self.subTest(arm=arm):
                result = route_task(arm=arm, route="cold", task_id="A1", layout="A",
                    cached=None, observation=observation(1), width=1280, height=760,
                    palette_slots=palette_slots(),
                    model_call=lambda _obs: candidate())
                self.assertEqual(result["model_calls"], 1)
                self.assertIsNone(result["cache_update"])

    def test_candidate_must_supply_two_distinct_ordered_points(self):
        bad = dict(candidate(), points=[{"x": 200, "y": 200}])
        with self.assertRaisesRegex(RouteStop, "invalid model target output"):
            route_task(arm="plain", route="cold", task_id="A1", layout="A",
                cached=None, observation=observation(1), width=1280, height=760,
                palette_slots=palette_slots(), model_call=lambda _obs: bad)

    def test_palette_probe_snaps_to_nearby_screen_slot_and_refuses_far_candidate(self):
        slots = [{"row": 0, "column": 0, "point": [152, 221]},
                 {"row": 0, "column": 1, "point": [198, 221]}]
        result = route_task(arm="plain", route="cold", task_id="A1", layout="A",
            cached=None, observation=observation(1), width=1280, height=760,
            palette_slots=slots, model_call=lambda _obs: candidate())
        self.assertEqual(result["bundle"].palette_point, (152, 221))

        far = dict(candidate(), points=[{"x": 300, "y": 220}, {"x": 640, "y": 410}])
        with self.assertRaisesRegex(RouteStop, "outside 48px slot neighborhood"):
            route_task(arm="plain", route="cold", task_id="A1", layout="A",
                cached=None, observation=observation(1), width=1280, height=760,
                palette_slots=slots, model_call=lambda _obs: far)

    def test_final_locator_requires_fresh_same_binding_observation(self):
        bundle = route_task(arm="persistent", route="cold", task_id="A1", layout="A",
            cached=None, observation=observation(1), width=1280, height=760,
            palette_slots=palette_slots(),
            model_call=lambda _obs: candidate())["bundle"]
        locator = require_current_locator(bundle, observation(2), "A")
        self.assertEqual(locator["validated_sequence"], 2)
        self.assertEqual(locator["authority"],
                         "locator only; explicit caller action still required")

    def test_final_locator_refuses_geometry_change_after_model_response(self):
        bundle = route_task(arm="persistent", route="cold", task_id="A1", layout="A",
            cached=None, observation=observation(1), width=1280, height=760,
            palette_slots=palette_slots(),
            model_call=lambda _obs: candidate())["bundle"]
        with self.assertRaisesRegex(RouteStop, "refused before input: association_changed"):
            require_current_locator(bundle, observation(2, (0, 24, 1216, 760)), "A")


if __name__ == "__main__":
    unittest.main()
