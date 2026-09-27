from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
from action_validity_admission_v1 import CONTRACT_FORMAT
from doom_action_snapshot_v1 import build_action_snapshot


BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
OBSERVATION = {"sequence": 2, "capture_ns": 200, "pointer_binding": BINDING}


class Reader:
    def __init__(self, signal_id, status="observed", value=1, sequence=2):
        self.signal_id, self.status, self.value, self.sequence = signal_id, status, value, sequence

    def read(self, observation):
        return {"signal_id": self.signal_id, "status": self.status,
                "value": self.value, "sequence": self.sequence,
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}


def contract(signals):
    return {"format": CONTRACT_FORMAT, "source": {"signals": signals}}


class DoomActionSnapshotTests(unittest.TestCase):
    def test_health_and_ammo_share_one_exact_snapshot(self):
        value = build_action_snapshot(
            OBSERVATION, contract({"health": {}, "ammo": {}}),
            {"health": Reader("health", value=90), "ammo": Reader("ammo", value=12)})
        self.assertEqual(value["sequence"], 2)
        self.assertEqual(value["signals"]["health"]["value"], 90)
        self.assertEqual(value["signals"]["ammo"]["value"], 12)

    def test_unknown_is_preserved_instead_of_dropped(self):
        value = build_action_snapshot(
            OBSERVATION, contract({"health": {}}),
            {"health": Reader("health", status="unknown", value=None)})
        self.assertEqual(value["signals"]["health"], {"status": "unknown", "value": None})

    def test_missing_spurious_and_misbound_readers_fail_closed(self):
        spec = contract({"health": {}})
        with self.assertRaises(ValueError):
            build_action_snapshot(OBSERVATION, spec, {})
        with self.assertRaises(ValueError):
            build_action_snapshot(OBSERVATION, spec,
                                  {"health": Reader("health"), "ammo": Reader("ammo")})
        with self.assertRaises(ValueError):
            build_action_snapshot(OBSERVATION, spec, {"health": Reader("health", sequence=3)})

    def test_unsupported_contract_signal_fails_closed(self):
        with self.assertRaises(ValueError):
            build_action_snapshot(
                OBSERVATION, contract({"enemy_visible": {}}),
                {"enemy_visible": Reader("enemy_visible")})


if __name__ == "__main__":
    unittest.main()
