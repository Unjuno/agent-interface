from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
from doom_action_validity_contract_v1 import build_contract


BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}


def signal(signal_id, value, sequence=1, capture=10):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": signal_id, "value": value, "sequence": sequence,
            "capture_ns": capture, "binding": BINDING}


def authored(ammo=1):
    return {"critical_health_minimum": 45, "maximum_health_loss": 8,
            "minimum_ammo": ammo, "max_current_age_ms": 500}


class DoomActionValidityContractTests(unittest.TestCase):
    def test_fire_binds_health_and_ammo_from_same_epoch(self):
        contract = build_contract(
            [{"action": "retreat_fire", "extent": "short"}], authored(),
            signal("health", 85), signal("ammo", 47))
        self.assertEqual(list(contract["source"]["signals"]), ["health", "ammo"])
        self.assertEqual(contract["predicates"][-1],
                         {"signal_id": "ammo", "operator": "minimum", "value": 1})

    def test_nonfire_has_no_ammo_dependency(self):
        contract = build_contract(
            [{"action": "strafe_left", "extent": "medium"}], authored(ammo=0),
            signal("health", 85))
        self.assertEqual(list(contract["source"]["signals"]), ["health"])
        self.assertEqual(len(contract["predicates"]), 2)

    def test_missing_or_misaligned_ammo_fails_closed(self):
        command = [{"action": "fire", "extent": "pulse"}]
        with self.assertRaises(ValueError):
            build_contract(command, authored(), signal("health", 85))
        with self.assertRaises(ValueError):
            build_contract(command, authored(), signal("health", 85),
                           signal("ammo", 47, sequence=2))

    def test_semantic_omission_and_spurious_dependency_fail_closed(self):
        with self.assertRaises(ValueError):
            build_contract([{"action": "fire", "extent": "pulse"}], authored(ammo=0),
                           signal("health", 85), signal("ammo", 47))
        with self.assertRaises(ValueError):
            build_contract([{"action": "strafe_right", "extent": "short"}], authored(),
                           signal("health", 85), signal("ammo", 47))


if __name__ == "__main__":
    unittest.main()
