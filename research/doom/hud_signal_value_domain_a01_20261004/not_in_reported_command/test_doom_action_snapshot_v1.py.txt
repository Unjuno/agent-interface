from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
from action_validity_admission_v1 import CONTRACT_FORMAT
from doom_action_snapshot_v1 import build_action_snapshot
from doom_typed_observation_v1 import (
    SCHEMA as TYPED_SCHEMA, build_action_snapshot as build_typed_action_snapshot)


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

    def test_out_of_domain_current_values_fail_in_both_snapshot_builders(self):
        spec = contract({"health": {}, "ammo": {}})
        for health, ammo in ((201, 12), (90, 1000)):
            with self.subTest(health=health, ammo=ammo):
                with self.assertRaisesRegex(ValueError, "outside its declared domain"):
                    build_action_snapshot(
                        OBSERVATION, spec,
                        {"health": Reader("health", value=health),
                         "ammo": Reader("ammo", value=ammo)})

        typed = {
            "event": "typed_observation", "schema": TYPED_SCHEMA,
            "sequence": 2, "capture_ns": 200, "pointer_binding": BINDING,
            "frame_rgb_sha256": "a" * 64, "frame_size": [640, 480],
            "typed_extraction_started_ns": 201, "typed_ready_ns": 202,
            "capture_to_typed_ready_ms": 0.000002,
            "artifact_published": False, "grants_input_authority": False,
            "signals": {
                "health": {"signal_id": "health", "status": "observed",
                           "value": 201, "sequence": 2, "capture_ns": 200,
                           "binding": BINDING, "wad_sha256": "b" * 64},
                "ammo": {"signal_id": "ammo", "status": "observed",
                         "value": 12, "sequence": 2, "capture_ns": 200,
                         "binding": BINDING, "wad_sha256": "b" * 64},
            },
        }
        with self.assertRaisesRegex(ValueError, "outside its declared domain"):
            build_typed_action_snapshot(typed, spec)


if __name__ == "__main__":
    unittest.main()
