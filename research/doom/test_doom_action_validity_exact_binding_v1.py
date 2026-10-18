"""Paired action sources require exact JSON binding identity."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(REPO), str(HERE), str(HERE.parent / "live_control")]
from doom_action_validity_contract_v1 import build_contract
import map01_overlap_controller_v39 as controller


class ExactPairedBindingTests(unittest.TestCase):
    def test_fire_contract_rejects_nested_boolean_integer_binding_alias(self):
        health_binding = {
            "focus": 1, "surface": 9, "geometry": [0, 0, 640, 480],
        }
        ammo_binding = {
            "focus": True, "surface": 9, "geometry": [0, 0, 640, 480],
        }

        def signal(signal_id, binding):
            return {
                "format": "observable-signal-v1", "status": "observed",
                "signal_id": signal_id, "value": 80 if signal_id == "health" else 4,
                "sequence": 3, "capture_ns": 30, "binding": binding,
            }

        authored = {
            "critical_health_minimum": 40, "maximum_health_loss": 10,
            "minimum_ammo": 1, "max_current_age_ms": 500,
        }
        with self.assertRaisesRegex(ValueError, "share one observation epoch"):
            build_contract(
                [{"action": "fire", "extent": "pulse"}], authored,
                signal("health", health_binding), signal("ammo", ammo_binding))

    def test_current_fire_admission_rejects_nested_binding_alias(self):
        source_binding = {
            "focus": 1, "surface": 9, "geometry": [0, 0, 640, 480],
        }
        current_ammo_binding = {
            "focus": True, "surface": 9, "geometry": [0, 0, 640, 480],
        }

        def signal(signal_id, binding, sequence, capture_ns):
            return {
                "format": "observable-signal-v1", "status": "observed",
                "signal_id": signal_id,
                "value": 80 if signal_id == "health" else 4,
                "sequence": sequence, "capture_ns": capture_ns,
                "binding": binding,
            }

        candidate = {"commands": [{"action": "fire", "extent": "pulse"}]}
        authored = {
            "critical_health_minimum": 40, "maximum_health_loss": 10,
            "minimum_ammo": 1, "max_current_age_ms": 500,
        }
        source_health = signal("health", source_binding, 3, 30)
        source_ammo = signal("ammo", source_binding, 3, 30)
        current_health = signal("health", source_binding, 4, 40)
        current_ammo = signal("ammo", current_ammo_binding, 4, 40)
        planner_result = SimpleNamespace(
            handle=SimpleNamespace(turn_id="turn-1"),
            status="completed", answer_eligible=True)
        receipt = controller.final_admission_from_planner_result(
            planner_result, 32, None, 33)

        with self.assertRaisesRegex(ValueError,
                                    "current health and ammo must share"):
            controller.prepare_action_admission(
                receipt, candidate, authored, source_health, source_ammo,
                current_health, current_ammo, 41)


if __name__ == "__main__":
    unittest.main()
