import ast
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / "map01_overlap_controller_v39.py"
sys.path.insert(0, str(ROOT))
from action_validity_admission_v1 import SNAPSHOT_FORMAT, evaluate_action_validity
from doom_action_validity_contract_v1 import build_contract

BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}
COMMANDS = [{"action": "fire", "extent": "short"}]


class SignalReader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": observation[self.signal_id],
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}


def load_cover_functions():
    guard_spec = importlib.util.spec_from_file_location(
        "frozen_observable_guard", ROOT / "observable_signal_guard_v2.py")
    guard_module = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard_module)
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    chosen = [top[name] for name in (
        "guard_spec", "ammo_guard_spec", "_typed_json_equal",
        "_signal_pair_matches", "_signal_pair_content_matches",
        "DoomCoverSignalPairMonitor", "build_cover_monitor")]
    namespace = {
        "json": json, "time": __import__("time"),
        "ObservableSignalGuard": guard_module.ObservableSignalGuard,
        "ObservableSignalPolicyMonitor": guard_module.ObservableSignalPolicyMonitor,
        "MAX_AUTHORED_HEALTH_LOSS": 20,
    }
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(CONTROLLER), "exec"), namespace)
    return namespace


def source_observation(health=70, ammo=6, sequence=10, capture_ns=1_000_000_000):
    return {"event": "observation", "sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": BINDING, "health": health, "ammo": ammo}


def current_pair(health, ammo, sequence=11, capture_ns=1_100_000_000):
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns, "pointer_binding": BINDING,
            "signals": {
                "health": {"format": "observable-signal-v1", "status": "observed",
                           "signal_id": "health", "value": health,
                           "sequence": sequence, "capture_ns": capture_ns,
                           "binding": BINDING},
                "ammo": {"format": "observable-signal-v1", "status": "observed",
                         "signal_id": "ammo", "value": ammo,
                         "sequence": sequence, "capture_ns": capture_ns,
                         "binding": BINDING}}}


class AmmoPropagationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions = load_cover_functions()
        cls.health_reader = SignalReader("health")
        cls.ammo_reader = SignalReader("ammo")
        cls.source = source_observation()
        cls.cover_monitor, cls.cover_receipt = cls.functions["build_cover_monitor"](
            cls.health_reader, cls.source,
            {"signal_id": "health", "critical_health_minimum": 45,
             "maximum_health_loss": 8, "max_source_age_ms": 1000},
            "a11", ammo_reader=cls.ammo_reader, requires_ammo=True)
        cls.contract = build_contract(
            COMMANDS,
            {"critical_health_minimum": 45, "maximum_health_loss": 8,
             "minimum_ammo": 5, "max_current_age_ms": 500},
            cls.health_reader.read(cls.source), cls.ammo_reader.read(cls.source))

    def test_positive_ammo_below_authored_action_minimum_diverges(self):
        pair = current_pair(health=70, ammo=4)
        monitor_result = self.cover_monitor.observe(pair)
        snapshot = {"format": SNAPSHOT_FORMAT, "sequence": 11,
                    "capture_ns": 1_100_000_000, "binding": BINDING,
                    "signals": {"health": {"status": "observed", "value": 70},
                                "ammo": {"status": "observed", "value": 4}}}
        action_result = evaluate_action_validity(
            COMMANDS, self.contract, snapshot, 1_200_000_000)
        self.assertIsNone(monitor_result,
                          "positive ammo above monitor's 1-round floor should not invalidate cover")
        self.assertEqual(self.cover_monitor.last_values["ammo"], 4)
        self.assertEqual(action_result["status"], "REJECTED_PREDICATE")
        self.assertEqual(action_result["reason"], "ammo_minimum_failed")
        self.assertEqual(action_result["checks"][-1],
                         {"signal_id": "ammo", "operator": "minimum",
                          "expected": 5, "observed": 4, "passed": False})
        result = {"classification": "CONSTRUCTION_ONLY_POLICY_PROPAGATION_COMPARISON",
                  "source_sequence": 10, "current_sequence": 11,
                  "source_ammo": 6, "current_ammo": 4,
                  "planner_authored_minimum_ammo": 5,
                  "cover_ammo_hard_minimum": self.cover_monitor.guards["ammo"].spec["hard_minimum"],
                  "cover_monitor_invalidated": monitor_result is not None,
                  "cover_soft_events": self.cover_monitor.soft_event_count,
                  "action_admission_status": action_result["status"],
                  "action_admission_reason": action_result["reason"],
                  "action_ammo_check": action_result["checks"][-1]}
        self._save(result)

    def test_zero_ammo_is_the_cover_monitor_boundary(self):
        monitor, _receipt = self.functions["build_cover_monitor"](
            self.health_reader, self.source,
            {"signal_id": "health", "critical_health_minimum": 45,
             "maximum_health_loss": 8, "max_source_age_ms": 1000},
            "a11-zero", ammo_reader=self.ammo_reader, requires_ammo=True)
        outcome = monitor.observe(current_pair(health=70, ammo=0))
        self.assertEqual(outcome["reason"], "ammo:below_hard_minimum")
        self.assertEqual(outcome["outcome"]["hard_minimum"], 1)
        self._save({"classification": "CONSTRUCTION_ONLY_ZERO_AMMO_CONTROL",
                    "current_ammo": 0, "monitor_invalidated": True,
                    "reason": outcome["reason"],
                    "hard_minimum": outcome["outcome"]["hard_minimum"]})

    @staticmethod
    def _save(result):
        result_dir = ROOT / "results"
        result_dir.mkdir(exist_ok=True)
        path = result_dir / ("zero_ammo.json" if result["classification"].endswith("CONTROL")
                             else "positive_ammo_gap.json")
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("A11_RESULT=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
