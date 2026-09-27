import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
import map01_overlap_controller_v33 as controller
from persistent_planner_adapter_v2 import _validate_schema, PlannerProtocolError


BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}


def signal(signal_id, value, sequence, capture_ns, status="observed"):
    return {"format": "observable-signal-v1", "status": status,
            "signal_id": signal_id, "value": value if status == "observed" else None,
            "sequence": sequence, "capture_ns": capture_ns, "binding": BINDING}


def action(command="retreat_fire", minimum_ammo=1):
    return {"assessment": "bounded action remains applicable under typed evidence",
            "state": "active",
            "commands": [{"action": command, "extent": "short"}],
            "contingencies": [],
            "next_cover": [{"action": "strafe_left", "extent": "short"}],
            "next_cover_validity": [{"signal_id": "health",
                                     "critical_health_minimum": 45,
                                     "maximum_health_loss": 8,
                                     "max_source_age_ms": 30000}],
            "action_validity": [{"critical_health_minimum": 45,
                                 "maximum_health_loss": 8,
                                 "minimum_ammo": minimum_ammo,
                                 "max_current_age_ms": 500}]}


def initial_receipt():
    result = SimpleNamespace(handle=SimpleNamespace(turn_id="turn-1"),
                             status="completed", answer_eligible=True)
    return controller.final_admission_from_planner_result(result, 10, None, 11)


class Map01OverlapControllerV33Tests(unittest.TestCase):
    def test_schema_and_semantics_require_separate_action_validity(self):
        candidate = action()
        schema = json.loads((HERE / "map01_cover_policy_schema_v6.json").read_text())
        _validate_schema(candidate, schema)
        controller.validate_action(candidate)
        missing = copy.deepcopy(candidate); missing["action_validity"] = []
        with self.assertRaises(ValueError):
            controller.validate_action(missing)
        terminal = {"assessment": "dead", "state": "dead", "commands": [],
                    "contingencies": [], "next_cover": [],
                    "next_cover_validity": [], "action_validity": []}
        _validate_schema(terminal, schema)
        controller.validate_action(terminal)
        malformed = copy.deepcopy(candidate)
        malformed["action_validity"][0]["max_current_age_ms"] = 1001
        with self.assertRaises(PlannerProtocolError):
            _validate_schema(malformed, schema)

    def test_fire_reaches_executor_ready_only_after_current_health_and_ammo(self):
        candidate = action()
        ready = controller.prepare_action_admission(
            initial_receipt(), candidate, candidate["action_validity"][0],
            signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
            signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)
        self.assertEqual(ready["status"], "READY_FOR_FRESH_EXECUTOR_ADMISSION")
        self.assertEqual([row["signal_id"] for row in
                          ready["action_validity"]["checks"]],
                         ["health", "health", "ammo"])
        admitted = controller.bind_first_plan_acceptance(
            ready, {"id": "primary", "accepted_ns": 202})
        self.assertEqual(admitted["status"], "INPUT_ADMITTED")

    def test_zero_or_unknown_ammo_rejects_before_executor(self):
        candidate = action()
        for current in (signal("ammo", 0, 2, 200),
                        signal("ammo", 0, 2, 200, status="unknown")):
            rejected = controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), current, 201)
            self.assertEqual(rejected["status"], "REJECTED_ACTION_NOT_CURRENT")
            self.assertIsNone(rejected["executor_admission"])

    def test_fire_cannot_omit_ammo_and_movement_cannot_add_it(self):
        with self.assertRaises(ValueError):
            candidate = action(minimum_ammo=0)
            controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)
        with self.assertRaises(ValueError):
            candidate = action(command="strafe_left", minimum_ammo=1)
            controller.prepare_action_admission(
                initial_receipt(), candidate, candidate["action_validity"][0],
                signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
                signal("health", 79, 2, 200), signal("ammo", 46, 2, 200), 201)

    def test_prompt_exposes_exact_source_epoch_health_and_ammo(self):
        class Planner:
            def begin_turn(self, prompt, **params):
                self.prompt, self.params = prompt, params
                return "handle"
        planner = Planner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); image = root / "sheet.png"; image.write_bytes(b"x")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                controller.begin_model_turn(
                    planner, root, image, [], 85, 47, None, {"type": "object"})
        self.assertIn("Current locally verified health: 85", planner.prompt)
        self.assertIn("Current locally verified ammo: 47", planner.prompt)


if __name__ == "__main__":
    unittest.main()
