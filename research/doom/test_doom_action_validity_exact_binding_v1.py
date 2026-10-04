"""Paired action sources require exact JSON binding identity."""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(REPO), str(HERE), str(HERE.parent / "live_control")]
from doom_action_validity_contract_v1 import build_contract


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


if __name__ == "__main__":
    unittest.main()
