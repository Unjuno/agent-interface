import ast
import importlib.util
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
sys.path.insert(0, str(SOURCE))
from observable_signal_guard_v2 import ObservableSignalGuard


def load_exact_monitor():
    source = SOURCE / "map01_overlap_controller_v39.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    selected = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    names = (
        "guard_spec", "ammo_guard_spec", "_typed_json_equal",
        "_signal_pair_matches", "_signal_pair_content_matches",
        "DoomCoverSignalPairMonitor",
    )
    namespace = {"time": time, "ObservableSignalGuard": ObservableSignalGuard}
    module = ast.Module(body=[selected[name] for name in names], type_ignores=[])
    exec(compile(module, str(source), "exec"), namespace)
    return namespace


H = load_exact_monitor()
BINDING = {"focus": 41, "surface": 7, "geometry": [0, 0, 800, 600]}


class TypedObservationGuardTests(unittest.TestCase):
    def make_monitor(self):
        capture = 1_000_000_000
        health = {"status": "observed", "signal_id": "health", "value": 59,
                  "sequence": 10, "capture_ns": capture, "binding": BINDING}
        ammo = {"status": "observed", "signal_id": "ammo", "value": 8,
                "sequence": 10, "capture_ns": capture, "binding": BINDING}
        validity = {"signal_id": "health", "critical_health_minimum": 45,
                    "maximum_health_loss": 8, "max_source_age_ms": 1000}
        guards = {
            "health": ObservableSignalGuard(H["guard_spec"](validity, health, 0),
                                              health, BINDING),
            "ammo": ObservableSignalGuard(H["ammo_guard_spec"](ammo, 0, 1000),
                                            ammo, BINDING),
        }
        class Reader:
            def __init__(self, signal_id): self.signal_id = signal_id
            def read(self, _observation):
                raise AssertionError("typed path must use captured typed signals")
        return H["DoomCoverSignalPairMonitor"](
            guards, Reader("health"), Reader("ammo"))

    @staticmethod
    def typed(sequence=11, capture=1_100_000_000, health=48, ammo=8,
              binding=BINDING):
        return {"event": "typed_observation", "schema": "doom-typed-observation-v1",
                "sequence": sequence, "capture_ns": capture,
                "pointer_binding": binding,
                "signals": {
                    "health": {"status": "observed", "signal_id": "health",
                               "value": health, "sequence": sequence,
                               "capture_ns": capture, "binding": binding},
                    "ammo": {"status": "observed", "signal_id": "ammo",
                             "value": ammo, "sequence": sequence,
                             "capture_ns": capture, "binding": binding},
                }, "grants_input_authority": False}

    def test_typed_hard_health_change_invalidates_without_artifact_reader(self):
        monitor = self.make_monitor()
        result = monitor.observe(self.typed(health=48))
        self.assertEqual(result["event"], "paired_signal_invalidation")
        self.assertEqual(result["reason"], "health:below_hard_minimum")
        self.assertTrue(result["requires_new_decision"])
        self.assertFalse(result["grants_input_authority"])
        self.assertEqual(result["signals"]["health"]["value"], 48)
        self.assertEqual(monitor.last_pair_sequence, 11)

    def test_typed_soft_change_preserves_policy(self):
        monitor = self.make_monitor()
        result = monitor.observe(self.typed(health=55))
        self.assertIsNone(result)
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 55)

    def test_unpaired_epoch_fails_closed(self):
        monitor = self.make_monitor()
        event = self.typed(health=48)
        event["signals"]["ammo"]["sequence"] = 10
        result = monitor.observe(event)
        self.assertEqual(result["reason"], "signal_pair_epoch_mismatch")
        self.assertFalse(result["grants_input_authority"])

    def test_duplicate_typed_epoch_with_changed_content_fails_closed(self):
        monitor = self.make_monitor()
        first = self.typed(health=55)
        self.assertIsNone(monitor.observe(first))
        duplicate = self.typed(health=48)
        result = monitor.observe(duplicate)
        self.assertEqual(result["reason"], "signal_pair_duplicate_epoch_mismatch")
        self.assertFalse(result["grants_input_authority"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
