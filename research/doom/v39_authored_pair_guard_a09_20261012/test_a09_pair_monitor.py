import ast
import importlib.util
import json
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / "map01_overlap_controller_v39.py"
GUARD_SOURCE = ROOT / "observable_signal_guard_v2.py"
BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}


def load_frozen_functions():
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    top = {node.name: node for node in tree.body
           if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    chosen = [top[name] for name in (
        "guard_spec", "ammo_guard_spec", "_typed_json_equal",
        "_signal_pair_matches", "_signal_pair_content_matches",
        "DoomCoverSignalPairMonitor")]
    spec = importlib.util.spec_from_file_location("frozen_guard", GUARD_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    namespace = {"json": json, "time": time,
                 "ObservableSignalGuard": module.ObservableSignalGuard}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(CONTROLLER), "exec"), namespace)
    return namespace


def signal(name, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


def make_monitor(functions, health=70, ammo=6):
    source_health = signal("health", health, 10, 1_000_000_000)
    source_ammo = signal("ammo", ammo, 10, 1_000_000_000)
    authored = {"signal_id": "health", "critical_health_minimum": 65,
                "maximum_health_loss": 8, "max_source_age_ms": 1000}
    hs = functions["guard_spec"](authored, source_health, "a09")
    ass = functions["ammo_guard_spec"](source_ammo, "a09", 1000)
    hg = functions["ObservableSignalGuard"](hs, source_health, BINDING)
    ag = functions["ObservableSignalGuard"](ass, source_ammo, BINDING)
    monitor = functions["DoomCoverSignalPairMonitor"](
        {"health": hg, "ammo": ag}, None, None)
    return monitor


def observe(functions, monitor, health, ammo, sequence=11, capture_ns=1_100_000_000):
    return monitor.observe({
        "event": "typed_observation", "sequence": sequence,
        "capture_ns": capture_ns, "pointer_binding": BINDING,
        "signals": {"health": signal("health", health, sequence, capture_ns),
                    "ammo": signal("ammo", ammo, sequence, capture_ns)}})


class AuthoredPairGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions = load_frozen_functions()

    def test_health_floor_crossing_invalidates(self):
        result = observe(self.functions, make_monitor(self.functions), health=64, ammo=6)
        self.assertEqual(result["event"], "paired_signal_invalidation")
        self.assertEqual(result["reason"], "health:below_hard_minimum")
        self.assertTrue(result["requires_new_decision"])
        self.assertFalse(result["grants_input_authority"])
        self.assertEqual(result["outcome"]["status"], "HARD_INVALIDATED")

    def test_zero_ammo_floor_crossing_invalidates(self):
        result = observe(self.functions, make_monitor(self.functions), health=70, ammo=0)
        self.assertEqual(result["event"], "paired_signal_invalidation")
        self.assertEqual(result["reason"], "ammo:below_hard_minimum")
        self.assertTrue(result["requires_new_decision"])
        self.assertFalse(result["grants_input_authority"])
        self.assertEqual(result["outcome"]["hard_minimum"], 1)

    def test_within_envelope_pair_is_soft_and_non_authoritative(self):
        monitor = make_monitor(self.functions)
        result = observe(self.functions, monitor, health=68, ammo=5)
        self.assertIsNone(result)
        self.assertEqual(monitor.soft_event_count, 2)
        self.assertEqual(monitor.last_values, {"health": 68, "ammo": 5})

    def test_mixed_epoch_fails_closed(self):
        monitor = make_monitor(self.functions)
        row = {"event": "typed_observation", "sequence": 11,
               "capture_ns": 1_100_000_000, "pointer_binding": BINDING,
               "signals": {"health": signal("health", 68, 11, 1_100_000_000),
                           "ammo": signal("ammo", 5, 12, 1_200_000_000)}}
        result = monitor.observe(row)
        self.assertEqual(result["reason"], "signal_pair_epoch_mismatch")
        self.assertTrue(result["requires_new_decision"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
